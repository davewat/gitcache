#!/bin/bash

# Configuration
REMOTE_REPO="https://github.com/davewat/gitcache.git"
CLONE_DIR="./.tmp_git_repo_clone"  # Temporary clone location
DEST_DIR="/var/lib/gitcache"
CONFIG_DIR="/etc/gitcache"

# Ensure the destination directory exists
mkdir -p "$DEST_DIR"
mkdir -p "$DEST_DIR"


# Clone or update the repo
if [ -d "$CLONE_DIR/.git" ]; then
    echo "Repository already exists. Pulling latest changes..."
    git -C "$CLONE_DIR" pull origin main
else
    echo "Cloning repository..."
    git clone "$REMOTE_REPO" "$CLONE_DIR"
fi

# Copy files to the destination directory
echo "Copying files to $DEST_DIR..."
rsync -av --delete "$CLONE_DIR/" "$DEST_DIR/"

# cleanup
rm -rf "$CLONE_DIR"

# copy config example
rsync -av --delete "$DEST_DIR/src/_config.toml" "$CONFIG_DIR/config.toml"

cd $DEST_DIR
python3 -m venv "$DEST_DIR/venv"
source "$DEST_DIR/venv/bin/activate"
python3 -m pip install -r src/requirements.txt

echo "Done!"