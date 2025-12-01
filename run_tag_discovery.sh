#!/bin/bash
# Discover player tags by crawling battle opponents

# Unset environment variables to force reload from .env file
unset DATABASE_URL
unset CLASH_ROYALE_API_KEY
unset SAMPLE_PLAYER_TAG

# Activate virtual environment
source venv/bin/activate

# Set PYTHONPATH to include src directory
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"

echo "Starting tag discovery crawler..."
echo "This will discover 1000 player tags across trophy ranges"
echo "Target: 250 tags per range (0-4000, 4000-8000, 8000-10000, 10000-15000)"
echo ""

# Run the tag discovery
python3 src/tag_discovery.py "$@"

echo ""
echo "Tag discovery complete! Check player_tags.txt for results"
echo "Next step: Run ./run_batch_collect.sh to collect player data"
