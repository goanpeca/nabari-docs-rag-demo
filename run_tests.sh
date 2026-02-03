#!/bin/bash
# Run tests in the correct conda environment

set -e

echo "🧪 Running tests in nebari-rag environment..."

# Activate environment and run tests
eval "$(conda shell.bash hook)"
conda activate nebari-rag

# Run pytest
pytest tests/ -v "$@"

echo "✅ Tests complete!"
