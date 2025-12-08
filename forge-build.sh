#!/bin/bash
# Wrapper script to ensure environment variables are loaded

# Source shell config to load environment variables
if [ -f ~/.zshrc ]; then
    source ~/.zshrc
fi

# Run forge build with all arguments passed through
poetry run forge build "$@"
