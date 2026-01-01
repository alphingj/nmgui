from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from typing import Iterable, List, Optional

from .models import CommandResult, Connection, Device, NmcliInfo, WifiNetwork


def _split_t_fields(line: str, expected: int) -> List[str]:
    # nmcli -t escapes ':' as '\:'; split while unescaping
    parts: List[str] = []
    current = []
    escaped = False
    for ch in line:
        if escaped:
            current.append(ch)
            escaped = False
        elif ch == "\\":
            escaped = True
        elif ch == ":":
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    parts.append("".join(current))
    # pad to expected length
    while len(parts) < expected:
        parts.append("")
    return parts


class Nmcli:
    def __init__(self) -> None:
        self._nmcli_path = shutil.which("nmcli")
        self._pkexec_path = shutil.which("pkexec")
        # Commands that modify state and need privileges
        self._privileged_commands = {
            "device connect",
            "device disconnect",
            "device wifi connect",
            "connection up",
            "connection down",
            "connection add",
            "connection modify",
            "connection delete",
            "radio wifi on",
            "radio wifi off",
        }

    def info(self) -> NmcliInfo:
        if not self._nmcli_path:
            return NmcliInfo(version=None, available=False)
        proc = subprocess.run([self._nmcli_path, "-g", "version", "general"],
                              text=True, capture_output=True, check=False)
        version = proc.stdout.strip() if proc.returncode == 0 else None
        return NmcliInfo(version=version, available=True)

    def _needs_privileges(self, args: List[str]) -> bool:
        """Check if command needs elevated privileges"""
        if len(args) < 2:
            return False
        # Check first two args against privileged command list
        cmd_prefix = " ".join(args[:2])
        return any(cmd_prefix.startswith(priv_cmd) for priv_cmd in self._privileged_commands)

    def _run_nmcli(self, args: Iterable[str], timeout: int = 20, force_privileged: bool = False) -> CommandResult:
        if not self._nmcli_path:
            raise RuntimeError("nmcli not found on PATH")
        
        args_list = list(args)
        cmd = [self._nmcli_path, *args_list]
        
        # Try with pkexec if command needs privileges
        if force_privileged or self._needs_privileges(args_list):
            if self._pkexec_path and os.environ.get("DISPLAY"):
                # Use pkexec for GUI privilege escalation
                cmd = [self._pkexec_path, self._nmcli_path, *args_list]
            # Otherwise try without pkexec and let nmcli handle it
        
        proc = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout, check=False)
        return CommandResult(command=cmd, stdout=proc.stdout, stderr=proc.stderr, returncode=proc.returncode)

    def connection_list(self) -> List[Connection]:
        res = self._run_nmcli(["-t", "-f", "NAME,UUID,TYPE,DEVICE,ACTIVE", "connection", "show"])
        conns: List[Connection] = []
        if res.returncode != 0:
            return conns
        for line in res.stdout.splitlines():
            fields = _split_t_fields(line, 5)
            if len(fields) >= 5:
                conns.append(Connection(name=fields[0], uuid=fields[1], type=fields[2], device=fields[3], active=fields[4].lower() == "yes"))
        return conns

    def device_status(self) -> List[Device]:
        res = self._run_nmcli(["-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device", "status"])
        devices: List[Device] = []
        if res.returncode != 0:
            return devices
        for line in res.stdout.splitlines():
            fields = _split_t_fields(line, 4)
            if len(fields) >= 4:
                devices.append(Device(device=fields[0], type=fields[1], state=fields[2], connection=fields[3]))
        return devices

    def wifi_scan(self) -> List[WifiNetwork]:
        res = self._run_nmcli([
            "-t",
            "-f",
            "IN-USE,SSID,MODE,CHAN,FREQ,RATE,SIGNAL,SECURITY",
            "device",
            "wifi",
            "list",
        ])
        networks: List[WifiNetwork] = []
        if res.returncode != 0:
            return networks
        for line in res.stdout.splitlines():
            fields = _split_t_fields(line, 8)
            if len(fields) >= 8:
                networks.append(
                    WifiNetwork(
                        in_use=fields[0] == "*",
                        ssid=fields[1],
                        mode=fields[2],
                        channel=fields[3],
                        frequency=fields[4],
                        rate=fields[5],
                        signal=fields[6],
                        security=fields[7],
                    )
                )
        return networks

    def wifi_connect(self, ssid: str, password: Optional[str] = None, iface: Optional[str] = None) -> CommandResult:
        args: List[str] = ["device", "wifi", "connect", ssid]
        if password:
            args.extend(["password", password])
        if iface:
            args.extend(["ifname", iface])
        return self._run_nmcli(args, force_privileged=True)

    def device_disconnect(self, device: str) -> CommandResult:
        return self._run_nmcli(["device", "disconnect", device], force_privileged=True)

    def device_connect(self, device: str) -> CommandResult:
        return self._run_nmcli(["device", "connect", device], force_privileged=True)

    def connection_up(self, name_or_uuid: str) -> CommandResult:
        return self._run_nmcli(["connection", "up", name_or_uuid], force_privileged=True)

    def connection_down(self, name_or_uuid: str) -> CommandResult:
        return self._run_nmcli(["connection", "down", name_or_uuid], force_privileged=True)

    def run_raw(self, command_line: str) -> CommandResult:
        # Accepts args without the leading nmcli, but allows full command too
        parts = shlex.split(command_line)
        if parts and parts[0] == "nmcli":
            parts = parts[1:]
        # Auto-detect if privileges needed for raw commands
        return self._run_nmcli(parts)
