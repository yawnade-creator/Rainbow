#!/bin/bash
# One-line deploy for Vultr VPS
# Run: curl -sS https://raw.githubusercontent.com/yawnade-creator/Rainbow/main/kisstoy/deploy.sh | bash

set -e

echo "=== KissToy Remote Control Setup ==="

# Install websockets
pip3 install --quiet websockets 2>/dev/null || pip install --quiet websockets

# Clone or update
DEST="$HOME/kisstoy"
if [ -d "$DEST" ]; then
    echo "Updating..."
    cd "$DEST"
    git pull origin main -- kisstoy/ 2>/dev/null || true
else
    echo "Installing..."
    git clone --depth 1 --filter=blob:none --sparse https://github.com/yawnade-creator/Rainbow.git "$DEST-tmp"
    cd "$DEST-tmp"
    git sparse-checkout set kisstoy
    mv kisstoy "$DEST"
    cd /
    rm -rf "$DEST-tmp"
fi

cd "$DEST"
chmod +x control.py

echo ""
echo "=== Done! ==="
echo ""
echo "Usage:"
echo "  cd ~/kisstoy"
echo "  python3 control.py link <share_url>    # paste share link"
echo "  python3 control.py status              # check connection"
echo "  python3 control.py suction 60          # go"
echo "  python3 control.py stop                # stop"
echo ""
