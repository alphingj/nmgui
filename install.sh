#!/usr/bin/env bash
# nmgui installer - cross-distribution Linux support
# Usage: bash install.sh  or  curl -fsSL https://raw.githubusercontent.com/alphingj/nmgui/main/install.sh | bash

set -e

echo "==> nmgui installer"
echo ""

# Detect package manager
detect_pkg_manager() {
    if command -v apt-get &> /dev/null; then echo "apt"
    elif command -v dnf &> /dev/null; then echo "dnf"
    elif command -v yum &> /dev/null; then echo "yum"
    elif command -v pacman &> /dev/null; then echo "pacman"
    elif command -v zypper &> /dev/null; then echo "zypper"
    elif command -v apk &> /dev/null; then echo "apk"
    else echo "unknown"; fi
}

install_package() {
    local pkg=$1
    local mgr=$2
    case "$mgr" in
        apt) sudo apt-get install -y "$pkg" ;;
        dnf) sudo dnf install -y "$pkg" ;;
        yum) sudo yum install -y "$pkg" ;;
        pacman) sudo pacman -S --noconfirm "$pkg" ;;
        zypper) sudo zypper install -y "$pkg" ;;
        apk) sudo apk add "$pkg" ;;
    esac
}

# Handle package manager errors and provide helpful suggestions
handle_pkg_error() {
    local mgr=$1
    local pkg=$2
    echo ""
    echo "❌ Failed to install/upgrade: $pkg"
    echo ""
    echo "This may be due to:"
    echo "  • Conflicting package dependencies"
    echo "  • Repository issues or SSL certificate problems"
    echo "  • System package conflicts"
    echo ""
    echo "Suggested fixes:"
    case "$mgr" in
        apt)
            echo "  1. Clear apt cache: sudo apt-get clean"
            echo "  2. Update package lists: sudo apt-get update --allow-insecure-repositories"
            echo "  3. Fix broken packages: sudo apt --fix-broken install"
            echo "  4. Try again: sudo apt-get install -y $pkg"
            echo ""
            echo "For certificate issues, add -o Apt::Get::AllowUnauthenticated=true:"
            echo "  sudo apt-get install -o Apt::Get::AllowUnauthenticated=true -y $pkg"
            echo ""
            echo "If all else fails, nmgui will still work without the latest NetworkManager!"
            ;;
        dnf)
            echo "  1. Clear dnf cache: sudo dnf clean all"
            echo "  2. Try again: sudo dnf install -y $pkg"
            echo "  3. Use --skip-broken: sudo dnf install --skip-broken -y $pkg"
            ;;
        yum)
            echo "  1. Clear yum cache: sudo yum clean all"
            echo "  2. Try again: sudo yum install -y $pkg"
            ;;
        pacman)
            echo "  1. Sync database: sudo pacman -Sy"
            echo "  2. Try again: sudo pacman -S --noconfirm $pkg"
            ;;
        zypper)
            echo "  1. Refresh repositories: sudo zypper refresh"
            echo "  2. Try again: sudo zypper install -y $pkg"
            ;;
        apk)
            echo "  1. Update package list: sudo apk update"
            echo "  2. Try again: sudo apk add $pkg"
            ;;
    esac
    echo ""
}

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"; exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if [ "$(printf '%s\n' "3.10" "$PYTHON_VERSION" | sort -V | head -n1)" != "3.10" ]; then
    echo "❌ Python 3.10+ required (found $PYTHON_VERSION)"; exit 1
fi
echo "✓ Python $PYTHON_VERSION"

PKG_MGR=$(detect_pkg_manager)
[ "$PKG_MGR" = "unknown" ] && echo "⚠ Unknown package manager; install dependencies manually" && PKG_MGR=""

# Install tkinter
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "📦 Installing tkinter..."
    case "$PKG_MGR" in
        apt) install_package "python3-tk" "$PKG_MGR" ;;
        dnf) install_package "python3-tkinter" "$PKG_MGR" ;;
        yum) install_package "python3-tkinter" "$PKG_MGR" ;;
        pacman) install_package "tk" "$PKG_MGR" ;;
        zypper) install_package "python3-tk" "$PKG_MGR" ;;
        apk) install_package "python3-tkinter" "$PKG_MGR" ;;
    esac
fi
python3 -c "import tkinter" 2>/dev/null && echo "✓ tkinter" || echo "⚠ tkinter install failed"

# Install/upgrade NetworkManager
echo "📦 NetworkManager..."
if ! command -v nmcli &> /dev/null; then
    echo "  Installing NetworkManager (first time)..."
    case "$PKG_MGR" in
        apt) 
            if ! sudo apt-get update -qq 2>/dev/null || ! sudo apt-get install -y network-manager 2>/dev/null; then
                handle_pkg_error "$PKG_MGR" "network-manager"
                echo "⚠ Skipping NetworkManager install (may already be present)"
            fi
            ;;
        dnf) sudo dnf install -y NetworkManager 2>/dev/null || handle_pkg_error "$PKG_MGR" "NetworkManager" ;;
        yum) sudo yum install -y NetworkManager 2>/dev/null || handle_pkg_error "$PKG_MGR" "NetworkManager" ;;
        pacman) sudo pacman -S --noconfirm networkmanager 2>/dev/null || handle_pkg_error "$PKG_MGR" "networkmanager" ;;
        zypper) sudo zypper install -y NetworkManager 2>/dev/null || handle_pkg_error "$PKG_MGR" "NetworkManager" ;;
        apk) sudo apk add networkmanager 2>/dev/null || handle_pkg_error "$PKG_MGR" "networkmanager" ;;
    esac
else
    echo "  NetworkManager already installed, attempting upgrade..."
    case "$PKG_MGR" in
        apt) 
            if ! sudo apt-get update -qq 2>/dev/null || ! sudo apt-get upgrade -y network-manager 2>/dev/null; then
                echo "⚠ Could not upgrade NetworkManager (likely due to dependencies)"
                echo "   This is OK - existing version will work fine with nmgui"
            fi
            ;;
        dnf) sudo dnf upgrade -y NetworkManager 2>/dev/null || echo "⚠ Could not upgrade NetworkManager (OK for nmgui)" ;;
        yum) sudo yum upgrade -y NetworkManager 2>/dev/null || echo "⚠ Could not upgrade NetworkManager (OK for nmgui)" ;;
        pacman) sudo pacman -S --noconfirm networkmanager 2>/dev/null || echo "⚠ Could not upgrade NetworkManager (OK for nmgui)" ;;
        zypper) sudo zypper update -y NetworkManager 2>/dev/null || echo "⚠ Could not upgrade NetworkManager (OK for nmgui)" ;;
        apk) sudo apk upgrade networkmanager 2>/dev/null || echo "⚠ Could not upgrade NetworkManager (OK for nmgui)" ;;
    esac
fi
command -v nmcli &> /dev/null && echo "✓ $(nmcli --version | head -1)" || echo "⚠ nmcli not found (install manually: https://github.com/NetworkManager/NetworkManager)"

# Install polkit
echo "📦 Polkit..."
if ! command -v pkexec &> /dev/null; then
    case "$PKG_MGR" in
        apt) sudo apt-get install -y policykit-1 2>/dev/null || echo "⚠ Could not install polkit" ;;
        dnf) sudo dnf install -y polkit 2>/dev/null || echo "⚠ Could not install polkit" ;;
        yum) sudo yum install -y polkit 2>/dev/null || echo "⚠ Could not install polkit" ;;
        pacman) sudo pacman -S --noconfirm polkit 2>/dev/null || echo "⚠ Could not install polkit" ;;
        zypper) sudo zypper install -y polkit 2>/dev/null || echo "⚠ Could not install polkit" ;;
        apk) sudo apk add polkit 2>/dev/null || echo "⚠ Could not install polkit" ;;
    esac
fi
command -v pkexec &> /dev/null && echo "✓ pkexec" || echo "⚠ pkexec not found (install manually)"

# Download nmgui
if [ ! -f "pyproject.toml" ]; then
    if ! command -v git &> /dev/null; then
        echo "❌ git not found"; exit 1
    fi
    echo ""
    echo "📦 Downloading nmgui..."
    git clone https://github.com/alphingj/nmgui.git
    cd nmgui
fi

# Install
echo ""
echo "📦 Installing nmgui..."

# Try standard user install first, fall back to venv
if python3 -m pip install --user . -q 2>/dev/null; then
    echo "✓ Installed to ~/.local/bin"
    [ -d "$HOME/.local/bin" ] && ! echo ":$PATH:" | grep -q ":$HOME/.local/bin:" && echo "⚠ Add to ~/.bashrc: export PATH=\"\$HOME/.local/bin:\$PATH\""
else
    echo "⚠ User install unavailable, using venv..."
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    python3 -m venv "$SCRIPT_DIR/venv_nmgui"
    source "$SCRIPT_DIR/venv_nmgui/bin/activate"
    pip install -e . -q
    deactivate
    
    # Create wrapper script in ~/.local/bin
    mkdir -p "$HOME/.local/bin"
    cat > "$HOME/.local/bin/nmgui" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
VENV_DIR="$(dirname "$SCRIPT_DIR")"/.."
[ ! -d "$VENV_DIR/nmgui/venv_nmgui" ] && VENV_DIR="."
if [ -d "$VENV_DIR/nmgui/venv_nmgui" ]; then
    source "$VENV_DIR/nmgui/venv_nmgui/bin/activate"
    exec python -m nmgui "$@"
else
    echo "Error: venv not found. Re-run install.sh from nmgui directory."
    exit 1
fi
EOF
    chmod +x "$HOME/.local/bin/nmgui"
    echo "✓ Created wrapper script at ~/.local/bin/nmgui"
    [ ! echo ":$PATH:" | grep -q ":$HOME/.local/bin:" ] && echo "⚠ Add to ~/.bashrc: export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

echo ""
echo "✅ Installation complete!"
