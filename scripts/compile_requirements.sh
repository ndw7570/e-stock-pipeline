#!/usr/bin/env bash
# bash scripts/compile_requirements.sh

set -euo pipefail

AIRFLOW_VERSION="3.1.6"
PYTHON_VERSION="3.12"
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

python -m pip install --upgrade pip
python -m pip install --upgrade pip-tools

pip-compile \
  --resolver=backtracking \
  --constraint "${CONSTRAINT_URL}" \
  --output-file requirements.txt \
  requirements.in