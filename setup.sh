#!/bin/bash
# Setup script for Blender Multi-Channel Export Pipeline project

# Exit on any error
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Setting up Blender Multi-Channel Export Pipeline project...${NC}"

# Create the main project directory
mkdir -p blender-multi-channel-export
cd blender-multi-channel-export

# Create the directory structure
echo -e "${GREEN}Creating directory structure...${NC}"
mkdir -p addon/operators addon/panels addon/utils
mkdir -p server
mkdir -p tests
mkdir -p .github/workflows
mkdir -p dist

# Create empty files for all components
echo -e "${GREEN}Creating empty files...${NC}"

# Main addon files
touch addon/__init__.py
touch addon/operators/__init__.py
touch addon/operators/setup.py
touch addon/operators/render.py
touch addon/panels/__init__.py
touch addon/panels/export_panel.py
touch addon/utils/__init__.py
touch addon/utils/file_utils.py
touch addon/utils/render_utils.py

# Server files
touch server/process_queue.py
touch server/requirements.txt
echo "watchdog==3.0.0" > server/requirements.txt

# Testing files
touch tests/__init__.py
touch tests/test_load_addon.py
touch .github/workflows/test.yml

# Project files
touch README.md
touch LICENSE
touch .gitignore
touch build.py
touch "Setup Instructions.md"

echo -e "${GREEN}Project structure created successfully!${NC}"
echo -e "${BLUE}Now paste the code into each file.${NC}"

# Print the file structure for reference
echo -e "${GREEN}File structure:${NC}"
find . -type f | sort

echo -e "${BLUE}Directory: $(pwd)${NC}"
echo -e "${GREEN}Done!${NC}"