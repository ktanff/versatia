#!/bin/bash
# init.sh - One-time setup for the application

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

GRADIO_PATH=$(python -c "import gradio; print(gradio.__file__)" | head -1)
GRADIO_DIR=$(dirname "$GRADIO_PATH")
patch -b "$GRADIO_DIR/routes.py" vhagilab/gr-patches/routes.patch
