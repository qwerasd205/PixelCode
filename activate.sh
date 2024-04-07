#!/bin/sh -e

ROOT_DIR=$(dirname "$0")

cd $ROOT_DIR

echo "Creating virtual environment..."
python3 -m venv .venv
echo "Activating..."
source .venv/bin/activate
echo ""
echo "================"
echo ""
echo "Installing requirements..."
pip3 install -r requirements.txt
echo ""
echo "================"
echo ""
echo "Done setting up virtual environment."
echo "Deactivate with \`deactivate\`."

