#!/bin/bash
# Simplified MGLTools Installer Script

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Installing MGLTools (AutoDock Tools) ===${NC}"

# Define installation paths
INSTALL_DIR="$PWD/mgltools_1.5.7_MacOS-X"
DOWNLOAD_URL="https://ccsb.scripps.edu/mgltools/download/447/"
DOWNLOAD_FILE="mgltools_1.5.7_MacOS-X.tar.gz"

# 1. Download MGLTools
echo -e "${YELLOW}Downloading MGLTools...${NC}"
if [ -f "$DOWNLOAD_FILE" ]; then
    echo "MGLTools archive already exists, skipping download."
else
    curl -L "$DOWNLOAD_URL" -o "$DOWNLOAD_FILE"
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to download MGLTools.${NC}"
        exit 1
    fi
fi

# 2. Extract the archive
echo -e "${YELLOW}Extracting MGLTools...${NC}"
if [ -d "$INSTALL_DIR" ]; then
    echo "MGLTools directory already exists, skipping extraction."
else
    tar -xzf "$DOWNLOAD_FILE"
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to extract MGLTools.${NC}"
        exit 1
    fi
fi

# 3. Create environment variables for MGLTools
echo -e "${YELLOW}Setting up environment variables...${NC}"
echo "# MGLTools Environment Setup" > mgltools_env.sh
echo "export MGL_ROOT=\"$INSTALL_DIR\"" >> mgltools_env.sh
echo "export PYTHONPATH=\"$INSTALL_DIR/MGLToolsPckgs:\$PYTHONPATH\"" >> mgltools_env.sh
echo "export PATH=\"$INSTALL_DIR/bin:\$PATH\"" >> mgltools_env.sh

# Make the environment file executable
chmod +x mgltools_env.sh

echo -e "${GREEN}MGLTools installation complete!${NC}"
echo -e "To use MGLTools, run: source $PWD/mgltools_env.sh"
echo -e "Then you can convert PDB files with:"
echo -e "  $INSTALL_DIR/bin/pythonsh $INSTALL_DIR/MGLToolsPckgs/AutoDockTools/Utilities24/prepare_receptor4.py -r protein.pdb -o protein.pdbqt" 