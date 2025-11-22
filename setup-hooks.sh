#!/bin/bash

# Setup script to configure Git hooks for this repository

echo "Setting up Git hooks..."

# Configure Git to use the hooks directory
git config core.hooksPath ./hooks

# Make all hooks executable
chmod +x hooks/*

echo "✅ Git hooks configured successfully!"
echo ""
echo "Active hooks:"
ls -1 hooks/ | grep -v README.md
echo ""
echo "Note: Make sure you have gitleaks installed for the pre-commit hook to work."
echo "Install with: brew install gitleaks (macOS) or see hooks/README.md"
