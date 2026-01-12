#!/bin/bash
# Wrapper that runs forge from any directory while using poetry's venv
export FORGE_CWD="$(pwd)"
cd /Users/dp/Scripts/forge
exec poetry run python -c "
import os
os.chdir(os.environ['FORGE_CWD'])
from forge.cli.main import main
main()
" "$@"
