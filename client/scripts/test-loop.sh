#!/bin/bash

echo "Starting test loop for RessyApi live tests..."
echo "Press Ctrl+C to stop the loop"

while true; do
    echo "Running tests at $(date)"
    npm test src/api/core/__tests__/RessyApi.live.test.ts
    echo "------------------------"
    echo "Waiting 5 seconds before next run..."
    sleep 5
done
