#!/bin/bash
# Analyze collected deck data to identify meta cards

# Unset environment variables to force reload from .env file
unset DATABASE_URL
unset CLASH_ROYALE_API_KEY
unset SAMPLE_PLAYER_TAG

# Activate virtual environment
source venv/bin/activate

# Set PYTHONPATH to include src directory
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"

echo "Starting meta analysis..."
echo "Analyzing card usage, win rates, and deck archetypes"
echo ""

# Run the meta analysis
python3 analyze_meta.py "$@"
python3 generate_report.py

echo ""
echo "Results saved to META_REPORT.txt"
