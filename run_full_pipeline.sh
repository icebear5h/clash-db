#!/bin/bash
# Complete 3-step meta analysis pipeline

echo "======================================================================"
echo "CLASH ROYALE META ANALYSIS PIPELINE"
echo "======================================================================"
echo ""
echo "This pipeline will:"
echo "  1. Discover 1000 player tags across trophy ranges"
echo "  2. Collect deck data from all players"
echo "  3. Analyze collected data to identify meta cards"
echo ""
echo "Press Ctrl+C to cancel, or wait 5 seconds to begin..."
sleep 5

echo ""
echo "======================================================================"
echo "STEP 1/3: TAG DISCOVERY"
echo "======================================================================"
./run_tag_discovery.sh
if [ $? -ne 0 ]; then
    echo "Error in tag discovery. Exiting."
    exit 1
fi

echo ""
echo "======================================================================"
echo "STEP 2/3: DATA COLLECTION"
echo "======================================================================"
./run_batch_collect.sh
if [ $? -ne 0 ]; then
    echo "Error in data collection. Exiting."
    exit 1
fi

echo ""
echo "======================================================================"
echo "STEP 3/3: META ANALYSIS"
echo "======================================================================"
./run_meta_analysis.sh
if [ $? -ne 0 ]; then
    echo "Error in meta analysis. Exiting."
    exit 1
fi

echo ""
echo "======================================================================"
echo "PIPELINE COMPLETE!"
echo "======================================================================"
echo ""
echo "Results:"
echo "  - Discovered tags: player_tags.txt"
echo "  - Collection logs: data_collection.log"
echo "  - Meta analysis: meta_report.txt"
echo ""
