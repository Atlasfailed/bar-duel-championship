#!/bin/bash
# Simple test runner script for bot tests

set -e

echo "🧪 Running bot tests..."
echo ""

# Check if pytest is installed
if ! python3 -m pytest --version > /dev/null 2>&1; then
    echo "❌ pytest is not installed. Installing..."
    pip3 install pytest pytest-cov
fi

# Run tests
echo "📋 Running all tests..."
python3 -m pytest bot/tests/ -v --tb=short

echo ""
echo "✅ Tests completed!"

