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
        apt) sudo apt-get update -qq && sudo apt-get install -y "$pkg" ;;
        dnf) sudo dnf install -y "$pkg" ;;
        yum) sudo yum install -y "$pkg" ;;
        pacman) sudo pacman -S --noconfirm "$pkg" ;;
        zypper) sudo zypper install -y "$pkg" ;;
        apk) sudo apk add "$pkg" ;;
        *) echo "Cannot install $pkg: unsupported package manager" >&2; return 1 ;;
    esac
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

# Install NetworkManager only when missing; installation must not upgrade it.
echo "📦 NetworkManager..."
if ! command -v nmcli &> /dev/null; then
    case "$PKG_MGR" in
        apt) sudo apt-get update -qq && sudo apt-get install -y network-manager ;;
        dnf) sudo dnf install -y NetworkManager ;;
        yum) sudo yum install -y NetworkManager ;;
        pacman) sudo pacman -S --noconfirm networkmanager ;;
        zypper) sudo zypper install -y NetworkManager ;;
        apk) sudo apk add networkmanager ;;
    esac
fi
if command -v nmcli &> /dev/null; then
    echo "✓ $(nmcli --version | head -1)"
else
    echo "❌ nmcli not found after installation" >&2
    exit 1
fi

# Install polkit
echo "📦 Polkit..."
if ! command -v pkexec &> /dev/null; then
    case "$PKG_MGR" in
        apt) sudo apt-get install -y policykit-1 ;;
        dnf) sudo dnf install -y polkit ;;
        yum) sudo yum install -y polkit ;;
        pacman) sudo pacman -S --noconfirm polkit ;;
        zypper) sudo zypper install -y polkit ;;
        apk) sudo apk add polkit ;;
    esac
fi
command -v pkexec &> /dev/null && echo "✓ pkexec" || echo "⚠ pkexec not found"

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
if ! python3 -m pip install --user . -q; then
    echo "⚠ User-site installation unavailable; using an isolated virtual environment"
    VENV_PATH="${XDG_DATA_HOME:-$HOME/.local/share}/nmgui/venv"
    python3 -m venv "$VENV_PATH"
    "$VENV_PATH/bin/python" -m pip install . -q
    mkdir -p "$HOME/.local/bin"
    cat > "$HOME/.local/bin/nmgui" <<EOF
#!/usr/bin/env bash
exec "$VENV_PATH/bin/python" -m nmgui "\$@"
EOF
    chmod +x "$HOME/.local/bin/nmgui"
fi

echo ""
echo "✅ Done! Run: nmgui"
echo ""
[ -d "$HOME/.local/bin" ] && ! echo ":$PATH:" | grep -q ":$HOME/.local/bin:" && echo "Add to ~/.bashrc: export PATH=\"\$HOME/.local/bin:\$PATH\""
