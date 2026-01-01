# nmgui Installation Troubleshooting

When running `bash install.sh`, you may encounter various errors. This guide provides solutions for common issues.

## APT Dependency Conflicts (Debian/Ubuntu)

**Error:**
```
E: Unable to satisfy dependencies. Reached two conflicting decisions:
   network-manager : Depends: libc6 (>= 2.42) but 2.41-12 is to be installed
```

**Cause:** System package libraries are out of sync or pinned to older versions.

**Solutions:**

### Option 1: Clear APT Cache and Retry
```bash
sudo apt-get clean
sudo apt-get update --allow-insecure-repositories
sudo apt --fix-broken install
bash install.sh
```

### Option 2: Skip Broken Packages
```bash
sudo apt-get install -o APT::Get::AllowUnauthenticated=true -y network-manager
bash install.sh
```

### Option 3: Use apt instead of apt-get
```bash
sudo apt update
sudo apt install network-manager policykit-1
bash install.sh
```

### Option 4: Manual Installation (Skip System Packages)
If system packages won't install, just install nmgui directly:
```bash
# Already have nmcli? Skip the installer and install nmgui directly
python3 -m venv venv_nmgui
source venv_nmgui/bin/activate
git clone https://github.com/alphingj/nmgui.git
cd nmgui
pip install -e .
nmgui
```

---

## SSL Certificate Verification Errors

**Error:**
```
W: Failed to fetch https://apt.packages.shiftkey.dev/ubuntu/dists/any/InRelease
SSL connection failed: error:0A000086:SSL routines::certificate verify failed
```

**Cause:** Repository SSL certificates are invalid or blocked by network/firewall.

**Solutions:**

### Option 1: Update Package Lists with Insecure Mode
```bash
sudo apt-get update --allow-insecure-repositories
bash install.sh
```

### Option 2: Remove Problematic PPA
The error often comes from third-party PPAs (like shiftkey). Remove and try again:
```bash
sudo add-apt-repository --remove ppa:shiftkey/github-desktop  # or relevant PPA
sudo apt-get update
bash install.sh
```

### Option 3: Fix System Certificates
```bash
sudo apt-get install --reinstall ca-certificates
sudo update-ca-certificates
bash install.sh
```

---

## Fedora/RHEL DNF Errors

**Error:**
```
Error: Unable to find a match
```

**Solutions:**

```bash
# Clear dnf cache
sudo dnf clean all

# Sync database
sudo dnf makecache

# Try installation again
bash install.sh
```

### Skip Broken Dependencies
```bash
sudo dnf install --skip-broken -y NetworkManager polkit
bash install.sh
```

---

## Arch Linux Pacman Issues

**Error:**
```
error: failed to commit transaction (conflicting files)
```

**Solutions:**

```bash
# Sync packages
sudo pacman -Sy

# Remove conflicting packages if needed
sudo pacman -R conflicting_package

# Try again
bash install.sh
```

---

## OpenSUSE Zypper Problems

**Error:**
```
Problem: nothing provides required ...
```

**Solutions:**

```bash
# Refresh repositories
sudo zypper refresh

# Update package database
sudo zypper up -y

# Try installation
bash install.sh
```

---

## Alpine APK Conflicts

**Error:**
```
ERROR: unable to select packages
```

**Solutions:**

```bash
# Update repository index
sudo apk update

# Upgrade system packages
sudo apk upgrade

# Try installation
bash install.sh
```

---

## NetworkManager Already Works?

**If you just want to install nmgui without system package hassles:**

```bash
# Clone the repo
git clone https://github.com/alphingj/nmgui.git
cd nmgui

# Create isolated environment
python3 -m venv venv

# Activate
source venv/bin/activate

# Install nmgui (no system packages needed)
pip install -e .

# Run
nmgui
```

**nmgui works fine with NetworkManager already installed on your system!**

---

## Checking What's Already Installed

Before troubleshooting, verify what you already have:

```bash
# Check Python
python3 --version

# Check tkinter
python3 -c "import tkinter; print('✓ tkinter')"

# Check nmcli
nmcli --version

# Check pkexec
which pkexec

# Check git
git --version
```

---

## Manual Installation of System Dependencies

If the installer fails, install manually:

### Debian/Ubuntu
```bash
sudo apt-get update
sudo apt-get install -y python3-tk network-manager policykit-1
```

### Fedora/RHEL
```bash
sudo dnf install -y python3-tkinter NetworkManager polkit
```

### Arch
```bash
sudo pacman -S tk networkmanager polkit
```

### openSUSE
```bash
sudo zypper install -y python3-tk NetworkManager polkit
```

### Alpine
```bash
sudo apk add python3-tkinter networkmanager polkit
```

Then install nmgui:
```bash
git clone https://github.com/alphingj/nmgui.git
cd nmgui
python3 -m venv venv
source venv/bin/activate
pip install -e .
nmgui
```

---

## Still Having Issues?

1. **Check the error message carefully** - the installer provides specific commands for your distro
2. **Try installing only nmgui** - system packages are optional, nmgui works with existing NetworkManager
3. **Use the venv approach** - creates isolated Python environment (always works)
4. **Report an issue**: https://github.com/alphingj/nmgui/issues

---

## Remember

- **nmgui only needs**: Python 3.10+, tkinter, nmcli (already installed), polkit (already on most systems)
- **System packages are optional** - if they won't install due to conflicts, nmgui still works!
- **Virtual environment approach is safest** - no system package conflicts
