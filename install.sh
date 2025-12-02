#!/bin/bash

##############################################################################
# macOS Hardware Test Suite - Robust Installer
# Compatible with Apple Silicon (M1/M2/M3) & Intel
##############################################################################

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Ensure we are in the script's directory
cd "$(dirname "$0")"
PROJECT_DIR=$(pwd)

echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   macOS Hardware Test Suite - Auto Installer      ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}\n"

# 1. Fix Directory Structure First (Critical for Import Error)
echo -e "${YELLOW}→ Verifying directory structure...${NC}"
mkdir -p app/templates logs
touch app/__init__.py
touch app/templates/__init__.py 2>/dev/null || true

# 2. Check Homebrew (Handle Apple Silicon Path)
if [[ "$(uname -m)" == "arm64" ]]; then
    echo -e "${GREEN}✓ Apple Silicon detected${NC}"
    # Add standard brew path to environment if missing
    if [[ ":$PATH:" != *":/opt/homebrew/bin:"* ]]; then
        export PATH="/opt/homebrew/bin:$PATH"
    fi
fi

if ! command -v brew &> /dev/null; then
    echo -e "${YELLOW}→ Installing Homebrew...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo -e "${GREEN}✓ Homebrew installed${NC}"
fi

# 3. Install System Dependencies
echo -e "${YELLOW}→ Checking system tools...${NC}"
brew install stress-ng smartmontools python@3.11 2>/dev/null || brew upgrade stress-ng smartmontools python@3.11

# 4. Setup Virtual Environment
echo -e "${YELLOW}→ Configuring Python environment...${NC}"
# Clean rebuild of venv to ensure consistency
rm -rf venv
python3 -m venv venv
source venv/bin/activate

# 5. Install Python Requirements
echo -e "${YELLOW}→ Installing libraries...${NC}"
pip install --upgrade pip
pip install Flask==3.0.0 PyYAML==6.0.1 psutil==5.9.6 requests==2.31.0 Werkzeug==3.0.1 py-cpuinfo==9.0.0

# 6. Finalize
chmod +x run.py
echo -e "\n${GREEN}✓ Installation Complete!${NC}"
echo -e "  Location: $PROJECT_DIR"
echo -e "  Run command: ${YELLOW}./run.py${NC}"
