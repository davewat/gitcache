#!/bin/bash

# Configuration
REMOTE_REPO="https://github.com/davewat/gitcache.git"
CLONE_DIR="./.tmp_git_repo_clone"  # Temporary clone location
DEST_DIR="/var/lib/gitcache"
CONFIG_DIR="/etc/gitcache"
STATUS_WEB_PORT=8000

### verify OS and update as needed
#!/bin/bash

# Function to detect the OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt &> /dev/null; then
            OS="debian"
        elif command -v yum &> /dev/null; then
            OS="rhel"
        else
            echo "❌ Unsupported Linux distribution. Exiting."
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        echo "❌ Automatic installating is not supported for MacOS. Exiting."
        exit 1
    else
        echo "❌ Unsupported OS: $OSTYPE. Exiting."
        exit 1
    fi
}

# Function to check if a command exists
check_command() {
    command -v "$1" &> /dev/null
}

# Function to install or update a package based on OS
install_or_update() {
    PACKAGE=$1
    if check_command "$PACKAGE"; then
        echo "✔ $PACKAGE is already installed. Updating..."
        case $OS in
            debian) sudo apt update && sudo apt install -y --only-upgrade "$PACKAGE" ;;
            rhel) sudo yum update -y "$PACKAGE" ;;
            macos) brew upgrade "$PACKAGE" ;;
        esac
    else
        echo "❌ $PACKAGE is NOT installed. Installing..."
        case $OS in
            debian) sudo apt update && sudo apt install -y "$PACKAGE" ;;
            rhel) sudo yum install -y "$PACKAGE" ;;
            macos) brew install "$PACKAGE" ;;
        esac
    fi
}

# Function to install pip and virtualenv
install_pip_virtualenv() {
    if check_command pip3; then
        echo "✔ pip3 is already installed. Upgrading..."
        python3 -m pip install --upgrade pip
    else
        echo "❌ pip3 is NOT installed. Installing..."
        case $OS in
            debian) sudo apt install -y python3-pip ;;
            rhel) sudo yum install -y python3-pip ;;
            macos) brew install python3 ;;
        esac
    fi

    if check_command virtualenv; then
        echo "✔ virtualenv is already installed. Upgrading..."
        python3 -m pip install --upgrade virtualenv
    else
        echo "❌ virtualenv is NOT installed. Installing..."
        python3 -m pip install virtualenv
    fi
}

# Function to prompt for OS selection
prompt_firewall() {
    echo "Select to have iptables open port $STATUS_WEB_PORT for status update page?"
    echo "Changes are as follows:"
    echo "iptables -I INPUT -p tcp -m tcp --dport $STATUS_WEB_PORT -j ACCEPT"
    echo "iptables -I OUTPUT -p tcp --sport $STATUS_WEB_PORT -m state --state ESTABLISHED -j ACCEPT"
    echo ""
    echo "1) No - do not change iptables"
    echo "2) Update IP Tables"
    read -p "Enter the number (1/2): " fw_choice

    case $fw_choice in
        1) firewall_config="none" ;;
        2) firewall_config="update" ;;
        *) echo "Invalid choice. Exiting."; exit 1 ;;
    esac
}

update_iptables() {
    # enable ip port
    # update detect_os function notes if this is changed
    iptables -I INPUT -p tcp -m tcp --dport "$STATUS_WEB_PORT" -j ACCEPT
    iptables -I OUTPUT -p tcp --sport "$STATUS_WEB_PORT" -m state --state ESTABLISHED -j ACCEPT
    echo "Firewall updated"
}

firewall_config() {
    case $firewall_config in
        update) update_iptables ;;
        none) echo "No Firewall Changes" ;;
    esac
}

# Detect OS
detect_os
echo "✅ Detected OS: $OS"

# Prompt for firewall configuration
prompt_firewall
firewall_config

# Install or update Git, Python, pip, and Virtualenv
echo "🔍 Checking for Git, Python, rsync, pip, and virtualenv installation..."
install_or_update git
install_or_update python3
install_or_update rsync
install_pip_virtualenv

# Verify installations
echo "✅ Git version: $(git --version)"
echo "✅ Python version: $(python3 --version)"
echo "✅ Rsync version: $(rsync --version)"
echo "✅ pip version: $(pip3 --version)"
echo "✅ virtualenv version: $(virtualenv --version)"

echo "🎉 Git, Python, pip, and virtualenv are installed and up to date!"





### Continue with install
# Ensure the destination directory exists
mkdir -p "$DEST_DIR"
mkdir -p "$CONFIG_DIR"


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

## python venv tools need to be available
# sudo apt-get -y install python3-venv

cd $DEST_DIR
python3 -m venv "$DEST_DIR/venv"
source "$DEST_DIR/venv/bin/activate"
python3 -m pip install -r src/requirements.txt
cp "$DEST_DIR/systemd/gitcache.service" /etc/systemd/system/gitcache.service
# reload systemd to apply changes:
sudo systemctl daemon-reload

# Enable the service to start on boot:
sudo systemctl enable gitcache.service

# Start the service
sudo systemctl restart gitcache.service

# Verify it is running
sudo systemctl status gitcache.service

echo "Done!"

