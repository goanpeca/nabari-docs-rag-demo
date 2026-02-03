#!/bin/bash
# Setup script for testing and pre-commit

echo "🔧 Installing test dependencies..."
source ~/.bash_profile
conda activate nebari-rag

# Install dev dependencies
pip install pytest pytest-cov black flake8 isort bandit pre-commit

echo "✅ Installing pre-commit hooks..."
pre-commit install

echo "🧪 Running tests..."
pytest tests/ -v

echo "✨ All set! Pre-commit hooks installed and tests passed."
