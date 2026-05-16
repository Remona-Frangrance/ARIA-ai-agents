#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "--- Installing Python Dependencies ---"
pip install -r requirements.txt

echo "--- Building React Frontend ---"
cd dashboard
npm install
npm run build

echo "--- Preparing Static Files ---"
cd ..
mkdir -p static
cp -r dashboard/dist/* static/

echo "--- Build Complete ---"
