#!/usr/bin/env python3
"""Launcher: python github_pr_report.py --repo URL"""

import sys

from github_pr_report.cli import main

if __name__ == "__main__":
    sys.exit(main())
