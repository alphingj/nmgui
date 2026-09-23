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


class NmcliError(RuntimeError):
    def __init__(self, operation: str, result: CommandResult) -> None:
        message = result.stderr.strip() or result.stdout.strip() or "command failed"
        super().__init__(f"{operation} failed ({result.returncode}): {message}")
        self.result = result


@dataclass
class NmcliInfo:
    version: Optional[str]
    available: bool
