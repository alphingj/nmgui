from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Connection:
    name: str
    uuid: str
    type: str
    device: str
    active: bool


@dataclass
class Device:
    device: str
    type: str
    state: str
    connection: str


@dataclass
class WifiNetwork:
    in_use: bool
    ssid: str
    mode: str
    channel: str
    frequency: str
    rate: str
    signal: str
    security: str


@dataclass
class CommandResult:
    command: List[str]
    stdout: str
    stderr: str
    returncode: int

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    @property
    def short(self) -> str:
        if self.ok:
            return self.stdout.strip() or "(no output)"
        return self.stderr.strip() or "(no error output)"


@dataclass
class NmcliInfo:
    version: Optional[str]
    available: bool
