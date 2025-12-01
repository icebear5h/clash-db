#!/bin/bash
# Run batch collection for multiple players across trophy ranges

# Unset environment variables to force reload from .env file
unset DATABASE_URL
unset CLASH_ROYALE_API_KEY
unset SAMPLE_PLAYER_TAG

# Activate virtual environment
source venv/bin/activate

# Set PYTHONPATH to include src directory
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"

echo "Starting batch collection..."
echo "Reading player tags from player_tags.txt"
echo "Target: 100 players per trophy range (0-4000, 4000-8000, 8000-10000, 10000-15000)"
echo ""

# Run the batch collector
python3 src/batch_collect.py "$@"
