# nmgui - NetworkManager GUI

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Linux-important)
![Zero Dependencies](https://img.shields.io/badge/Dependencies-Zero-brightgreen)

A lightweight, zero-dependency graphical interface for **nmcli** that works on any Linux desktop.

[Installation](#installation) • [Features](#features) • [Usage](#quick-start) • [Documentation](#documentation)

</div>

---

## Overview

**nmgui** is a thin GUI layer over `nmcli` (NetworkManager CLI) that brings network management to your fingertips. Forget terminal commands—manage Wi-Fi, devices, and connections through a clean, intuitive interface.

- **Works everywhere**: Same codebase on Ubuntu, Fedora, Arch, openSUSE, Alpine...
- **Zero bloat**: Only Python stdlib (tkinter) + system nmcli binary
- **Auto-privilege escalation**: Uses `pkexec` for privileged operations (no "sudo the entire app" needed)
- **Full nmcli access**: All 150+ nmcli commands available via raw terminal tab
- **Smart Wi-Fi**: Auto-detects secured networks and only prompts for password when needed

Made by **alphingj**

---

## Features

### 🎨 Dashboard
- System status summary (devices, connections, active links)
- One-click refresh for all network data

### 🔗 Connections Tab
- List all saved network connections
- Activate/deactivate connections with one click
- See connection type, device, and status

### 🖥️ Devices Tab
- View all network devices (Ethernet, Wi-Fi, VPN, etc.)
- Check device state and connected network
- Connect/disconnect devices instantly

### 📡 Wi-Fi Tab
- Scan available networks in real-time
- See SSID, signal strength, security type, frequency
- **Smart password prompt**: Automatically asks for password only if network requires authentication
- Join networks with one click

### ⌨️ Raw nmcli Terminal
- Execute any nmcli command directly
- Full output, stderr, and exit code visibility
- For power users and automation

### 🔐 Automatic Privilege Escalation
- Network changes automatically use `pkexec` for privilege escalation
- No need to run entire app as root
- polkit (desktop environment) handles authentication dialog

---

## Installation

### 🚀 Quick Install (All Linux Distros)

```bash
bash install.sh
```

Or via curl:
```bash
curl -fsSL https://raw.githubusercontent.com/alphingj/nmgui/main/install.sh | bash
```

**What it does:**
- ✓ Checks Python 3.10+ (installs if needed)
- ✓ Installs tkinter
- ✓ Installs/updates NetworkManager + nmcli
- ✓ Installs polkit for privilege escalation
- ✓ Installs nmgui to `~/.local/bin`

### 📦 Manual Installation

```bash
# Clone repo
git clone https://github.com/alphingj/nmgui.git
cd nmgui

# Install (user-local, no sudo)
pip install --user .

# Or system-wide (requires sudo)
sudo pip install .
```

### 🐍 Development Setup

```bash
git clone https://github.com/alphingj/nmgui.git
cd nmgui
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
nmgui
```

### Run Without Installing

```bash
git clone https://github.com/alphingj/nmgui.git
cd nmgui
python3 main.py
```

---

## Quick Start

Launch nmgui:
```bash
nmgui
```

That's it! The GUI will open with all tabs ready to use.

### First Time Setup

1. **Check Dashboard** for system status
2. **Go to Wi-Fi tab** → Click "Scan"
3. **Select a network** and click "Connect"
4. **Enter password** if prompted (only for secured networks)
5. **Wait for connection** - status updates when complete

---

## How It Works

```
Your Click (GUI)
    ↓
nmgui (Tkinter UI)
    ↓
nmcli wrapper (Python)
    ↓
pkexec (Privilege escalation via polkit)
    ↓
nmcli binary (NetworkManager CLI)
    ↓
NetworkManager daemon
    ↓
Linux kernel (network drivers)
```

All heavy lifting is done by battle-tested NetworkManager. nmgui only:
- Parses nmcli output
- Shows it in a GUI
- Handles privilege escalation dialogs

---

## Requirements

- **Linux** (any distribution)
- **Python 3.10+** (standard on most systems)
- **tkinter** (usually bundled with Python)
  - Ubuntu/Debian: `sudo apt install python3-tk`
  - Fedora/RHEL: `sudo dnf install python3-tkinter`
  - Arch: `sudo pacman -S tk`
- **NetworkManager** (`nmcli` command)
  - Usually pre-installed; install.sh handles this
- **polkit** (`pkexec`) for privilege escalation
  - Usually pre-installed; install.sh handles this

**That's it.** No Qt, no 170MB wheels, no bloat.

---

## Documentation

### Wi-Fi Connection Flow

When you click "Connect" on a Wi-Fi network:

1. **Security check**: nmgui examines the network's security type
2. **Smart prompt**: 
   - Open networks (no security) → connects immediately
   - Secured networks → asks for password with visual feedback
3. **Password entry**:
   - Shows network SSID and security method (WPA2, WPA3, etc.)
   - Password input hidden (masked with •)
   - Cancel anytime with Cancel button
4. **Connection**: Runs `pkexec nmcli device wifi connect "SSID" password "PASSWORD"`
5. **Authentication**: polkit prompts you for your user password (one-time per session)
6. **Status**: Shows success/failure and automatically refreshes network status

### Device Management
- **Connect**: Brings a device online to use its active connection
- **Disconnect**: Takes a device offline
- Requires privilege escalation

### Connection Lifecycle
1. **Connections** = saved network profiles (SSID, credentials, settings)
2. **Devices** = physical hardware (eth0, wlan0, etc.)
3. To connect to Wi-Fi:
   - nmgui creates a connection (or uses existing)
   - Activates it on the device
   - NetworkManager handles DHCP, DNS, etc.

### Raw nmcli Commands

The **Raw nmcli** tab lets you run any command:
```
device status              # List all devices
device show                # Device details
connection show            # List connections
device wifi list           # Scan networks
radio wifi on              # Enable Wi-Fi
radio wifi off             # Disable Wi-Fi
connection modify <name>   # Edit connection
```

[Full nmcli documentation](https://linux.die.net/man/1/nmcli)

---

## Troubleshooting

### "nmcli not found"
```bash
# Debian/Ubuntu
sudo apt update && sudo apt install network-manager

# Fedora/RHEL
sudo dnf install NetworkManager

# Arch
sudo pacman -S networkmanager

# openSUSE
sudo zypper install NetworkManager

# Alpine
sudo apk add networkmanager
```

### "pkexec not found" or "polkit not found"
```bash
# Debian/Ubuntu
sudo apt install policykit-1

# Fedora/RHEL
sudo dnf install polkit

# Arch
sudo pacman -S polkit

# openSUSE
sudo zypper install polkit

# Alpine
sudo apk add polkit
```

### "Command not found" after user install
Add to `~/.bashrc` or `~/.zshrc`:
```bash
export PATH="$HOME/.local/bin:$PATH"
```
Then reload:
```bash
source ~/.bashrc
```

### UI not rendering
- Ensure tkinter is installed: `python3 -c "import tkinter"` should work
- Check X11/Wayland: `echo $DISPLAY` should show something like `:0`
- Install tkinter if missing (see Requirements section)

### Password not being requested
- Check Wi-Fi network security type in Wi-Fi tab
- Open networks show no security type
- Secured networks show WPA2, WPA3, WEP, etc.
- If password still not requested, check nmcli errors in Raw tab

### Cannot connect to Wi-Fi
**Try the Raw nmcli tab:**
```
device wifi connect "SSID" password "PASSWORD"
```
This shows the actual error from nmcli.

### Permission denied on connect
Your user may not have NetworkManager permissions:
```bash
# Add user to netdev group
sudo usermod -aG netdev $USER

# Log out and back in, then try again
```

### Cannot disconnect devices
Some devices are in-use or have active connections:
- Try deactivating the connection instead (Connections tab)
- Use Raw nmcli: `connection down <name>`

---

## Uninstall

```bash
# User installation
pip uninstall nmgui

# System-wide
sudo pip uninstall nmgui
```

---

## Development

### Project Structure
```
nmgui/
├── src/nmgui/
│   ├── app.py          # Tkinter GUI (360+ lines)
│   ├── nmcli.py        # nmcli wrapper with pkexec (164 lines)
│   ├── models.py       # Data classes (50 lines)
│   └── __init__.py
├── main.py             # Entry point
├── pyproject.toml      # Package metadata
├── install.sh          # Cross-distro installer
├── LICENSE             # MIT
└── README.md
```

### Code Quality
- **No external Python dependencies** (tkinter is stdlib)
- **Type hints** on all functions
- **Error handling** with user-friendly messages
- **Threading** for non-blocking UI
- **Concise code** (~600 lines total)

### Contributing
Pull requests welcome! Areas for enhancement:
- VPN connection profiles
- IPv6 configuration
- Connection editing/creation UI
- Theme customization

### Building from Source
```bash
git clone https://github.com/alphingj/nmgui.git
cd nmgui
python3 -m pip install -e .
```

---

## Performance

- **Startup**: ~200ms (just Python + Tkinter)
- **Operations**: <1s for most nmcli commands
- **Memory**: ~20MB resident (tkinter UI only)
- **Disk**: ~50KB (just code, no wheels)

Compare to Qt/PyQt alternatives: 170MB+ for the same functionality.

---

## Security

- **No network access**: nmgui is 100% local
- **Privilege escalation**: Uses system polkit (desktop-standard)
- **Credentials**: Never stored by nmgui (NetworkManager handles creds)
- **Open source**: Full code available for audit
- **No telemetry**: Zero data collection

---

## License

MIT License - See [LICENSE](LICENSE) file

---

## Acknowledgments

Built with:
- [Python](https://python.org) - Language
- [tkinter](https://docs.python.org/3/library/tkinter.html) - GUI framework
- [nmcli](https://linux.die.net/man/1/nmcli) - Network management
- [polkit](https://www.freedesktop.org/wiki/Software/polkit/) - Privilege escalation

---

<div align="center">

**Made by alphingj**

[Report Issues](https://github.com/alphingj/nmgui/issues) | [Star on GitHub](https://github.com/alphingj/nmgui) | [View Source](https://github.com/alphingj/nmgui)

</div>
