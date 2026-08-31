# github-pr-report

CLI en Python que consulta GitHub y convierte los **pull requests abiertos**
en una vista operativa por repositorio: qué PRs están abiertos, desde cuándo,
quién los abrió, de quién falta approval y para qué versión (milestone) van.

No ejecuta ningún trabajo ni escribe en los repositorios: es una "fachada de
entrega" que identifica dónde se detuvo cada PR y cuál es la siguiente acción.

## Requisitos

- Python >= 3.9
- Un token de GitHub con acceso de lectura a los repositorios a consultar
  (`GITHUB_TOKEN`). Sin token también funciona contra repositorios públicos,
  sujeto a los límites de la API sin autenticar.

## Instalación

```bash
python3 -m pip install -e ".[dev]"
```

## Uso

```bash
export GITHUB_TOKEN="github_pat_..."
python3 github_pr_report.py --repo https://github.com/org/repo-a
```

Varios repositorios en un mismo reporte, repitiendo `--repo`:

```bash
python3 github_pr_report.py --repo org/repo-a --repo org/repo-b
```

`--repo` acepta URLs HTTPS (`https://github.com/owner/repo`), SSH
(`git@github.com:owner/repo.git`) o el slug corto `owner/repo`.

El proceso termina con código de salida `1` si algún repositorio falló
(URL inválida, repositorio no encontrado, error de la API o rate limit);
`0` si todos los reportes se generaron correctamente.

## Arquitectura

Regla de diseño: **la presentación no contiene lógica y la lógica no conoce
la terminal.** Esto permite reutilizar todo salvo `cli.py` y
`presentation.py` desde una futura aplicación web.

```text
github-pr-report/
├── github_pr_report.py            # Launcher: python3 github_pr_report.py --repo URL
├── github_pr_report/
│   ├── __init__.py
│   ├── urls.py                    # Parseo/validación de URLs; owner/repo local
│   ├── client.py                  # HTTP, auth, paginación, rate limits, errores
│   ├── transform.py               # JSON de GitHub -> modelos internos
│   ├── logic.py                   # Antigüedad, approval pendiente, versión destino
│   ├── models.py                  # Dataclasses del dominio
│   ├── service.py                 # Orquestación reutilizable (cliente+transform+logic)
│   ├── presentation.py            # Render de tablas en terminal (solo formato)
│   └── cli.py                     # Capa externa: argumentos, token, impresión
├── tests/
│   ├── conftest.py                # FakeTransport + loader de fixtures
│   ├── fixtures/*.json
│   ├── test_urls.py
│   ├── test_logic.py
│   ├── test_transform.py
│   ├── test_client.py
│   ├── test_service_and_presentation.py
│   └── test_cli.py
├── pyproject.toml
├── README.md
└── .gitignore
```

| Capa | Módulo | Responsabilidad |
| --- | --- | --- |
| URLs | `urls.py` | Extracción local de `owner/repo`, sin llamadas de red. |
| Cliente | `client.py` | HTTP, autenticación, paginación, rate limits, errores. Transporte inyectable para tests. |
| Transformación | `transform.py` | Convierte JSON de GitHub en modelos internos. Aísla del formato de la API. |
| Lógica | `logic.py` | Cálculos operativos. No sabe de terminal ni HTTP. |
| Orquestación | `service.py` | Une todo: `build_reports(client, repos)`. |
| Presentación | `presentation.py` | Recibe `RepositoryReport` ya calculado, devuelve strings. |
| CLI | `cli.py` | Argumentos, lectura del token, impresión, códigos de salida. |

Para una web futura: llamar a `service.build_reports(...)` y renderizar los
objetos `RepositoryReport` con una capa de presentación propia. No hay que
tocar `logic`, `service`, `transform` ni `client`.

## Decisiones tomadas

1. **"Approval pendiente"** = reviewers solicitados que aún no entregan
   review, excluyendo a quienes ya aprobaron.
   - Si no hay reviewers solicitados y nadie aprobó: `Sin approval`.
   - Si ya hay approval y no queda nadie pendiente: `-`.
   - Esto implica una llamada extra por PR al endpoint de reviews
     (`/pulls/{n}/reviews`), porque la API del PR no expone approvals
     directamente.
2. **Versión destino** = título del milestone; si no existe, `No
   identificada`. (Simplificación acordada para el MVP; se descartaron
   label/rama/issue por ahora.)
3. **Token** solo desde la variable de entorno `GITHUB_TOKEN`, nunca por
   argumento.
4. **Runtime sin dependencias externas**: se usó `urllib` en lugar de
   `requests`.
5. **Orden de filas**: de más antigua a más reciente.

## Solución de problemas

### macOS: `SSL: CERTIFICATE_VERIFY_FAILED`

Si al ejecutar el script obtienes un error como:

```text
ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify
failed: unable to get local issuer certificate (_ssl.c:1002)
```

es porque instalaste Python desde [python.org](https://www.python.org/) en
macOS. Ese instalador trae su propio bundle de certificados y no usa el
keychain del sistema, así que si no corriste el paso final del instalador,
`urllib` (usado por este proyecto para no depender de `requests`) no puede
verificar el certificado TLS de `api.github.com`.

Para arreglarlo, corre el script `Install Certificates.command` que viene
con esa instalación de Python (ajusta la versión si no es 3.11):

```bash
open "/Applications/Python 3.11/Install Certificates.command"
```

Vuelve a correr el comando después de que termine.

Alternativa: instala Python con Homebrew (`brew install python3`), que usa
los certificados del sistema y no tiene este problema.

## Fuera de alcance (backlog)

- Stacked PRs (formal e inferencia por ramas `head == base`).
- Exportación a Markdown/CSV/JSON.
- Aplicación web.
- Cualquier escritura o modificación de repositorios.

## Pruebas

```bash
python3 -m pytest
```

Las pruebas usan mocks y fixtures JSON. No hacen llamadas de red, no
requieren token ni acceden a repositorios reales.
