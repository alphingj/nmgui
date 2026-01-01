from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Optional, Tuple

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from .models import CommandResult, Connection, Device, WifiNetwork
from .nmcli import Nmcli


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("nmgui - NetworkManager GUI")
        self.geometry("1024x640")
        self.nmcli = Nmcli()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._connections_cache = []
        self._devices_cache = []

        self.status_var = tk.StringVar(value="Ready")

        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(container)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.dashboard_tab = self._build_dashboard(self.notebook)
        self.connections_tab = self._build_connections_tab(self.notebook)
        self.devices_tab = self._build_devices_tab(self.notebook)
        self.wifi_tab = self._build_wifi_tab(self.notebook)
        self.raw_tab = self._build_raw_tab(self.notebook)

        self.notebook.add(self.dashboard_tab, text="Dashboard")
        self.notebook.add(self.connections_tab, text="Connections")
        self.notebook.add(self.devices_tab, text="Devices")
        self.notebook.add(self.wifi_tab, text="Wi-Fi")
        self.notebook.add(self.raw_tab, text="Raw nmcli")

        status_bar = ttk.Label(self, textvariable=self.status_var, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.refresh_all()

    # ----- shared helpers -------------------------------------------------
    def on_close(self) -> None:
        self.executor.shutdown(wait=False)
        self.destroy()

    def run_task(self, fn: Callable, callback: Callable[[object, Optional[Exception]], None]) -> None:
        def wrapper() -> Tuple[object, Optional[Exception]]:
            try:
                return fn(), None
            except Exception as exc:
                return None, exc

        future = self.executor.submit(wrapper)
        future.add_done_callback(lambda fut: self.after(0, callback, *fut.result()))

    def show_error(self, title: str, message: str) -> None:
        messagebox.showerror(title, message, parent=self)

    def set_status(self, text: str) -> None:
        self.status_var.set(text)

    # ----- dashboard ------------------------------------------------------
    def _build_dashboard(self, parent: tk.Widget) -> tk.Frame:
        frame = ttk.Frame(parent, padding=8)
        self.info_label = ttk.Label(frame, text="nmcli status pending", justify=tk.LEFT)
        refresh_btn = ttk.Button(frame, text="Refresh", command=self.refresh_all)
        self.info_label.pack(anchor=tk.NW, fill=tk.X, pady=(0, 6))
        refresh_btn.pack(anchor=tk.W)
        return frame

    def _update_dashboard(self, devices: list[Device], conns: list[Connection]) -> None:
        active = [c for c in conns if c.active]
        connected_devices = [d for d in devices if d.state.lower() == "connected"]
        info = self.nmcli.info()
        lines = [
            f"nmcli version: {info.version or 'unknown'}",
            f"Connections: {len(conns)} (active: {len(active)})",
            f"Devices: {len(devices)} (connected: {len(connected_devices)})",
        ]
        self.info_label.config(text="\n".join(lines))

    # ----- connections tab -----------------------------------------------
    def _build_connections_tab(self, parent: tk.Widget) -> tk.Frame:
        frame = ttk.Frame(parent, padding=8)
        toolbar = ttk.Frame(frame)
        self.conn_refresh_btn = ttk.Button(toolbar, text="Refresh", command=self.refresh_connections)
        self.conn_up_btn = ttk.Button(toolbar, text="Up", command=self._connection_up)
        self.conn_down_btn = ttk.Button(toolbar, text="Down", command=self._connection_down)
        self.conn_refresh_btn.pack(side=tk.LEFT, padx=(0, 6))
        self.conn_up_btn.pack(side=tk.LEFT, padx=(0, 6))
        self.conn_down_btn.pack(side=tk.LEFT)
        toolbar.pack(fill=tk.X, pady=(0, 6))

        columns = ("name", "type", "device", "active", "uuid")
        self.conn_table = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        for col, text in zip(columns, ["Name", "Type", "Device", "Active", "UUID"]):
            self.conn_table.heading(col, text=text)
            self.conn_table.column(col, width=140 if col != "uuid" else 260)
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.conn_table.yview)
        self.conn_table.configure(yscrollcommand=vsb.set)
        self.conn_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        return frame

    def _populate_connections(self, conns: list[Connection]) -> None:
        self.conn_table.delete(*self.conn_table.get_children())
        for conn in conns:
            self.conn_table.insert("", tk.END, values=(conn.name, conn.type, conn.device, "yes" if conn.active else "no", conn.uuid))

    def _selected_connection(self) -> Optional[Connection]:
        sel = self.conn_table.selection()
        if not sel:
            return None
        vals = self.conn_table.item(sel[0], "values")
        name, type_, device, active_text, uuid = vals
        return Connection(name=name, uuid=uuid, type=type_, device=device, active=active_text == "yes")

    def _connection_up(self) -> None:
        conn = self._selected_connection()
        if not conn:
            self.show_error("No selection", "Pick a connection to bring up.")
            return
        self.set_status(f"Bringing up {conn.name}...")
        self.run_task(lambda: self.nmcli.connection_up(conn.uuid or conn.name), self._handle_command_result)

    def _connection_down(self) -> None:
        conn = self._selected_connection()
        if not conn:
            self.show_error("No selection", "Pick a connection to bring down.")
            return
        self.set_status(f"Bringing down {conn.name}...")
        self.run_task(lambda: self.nmcli.connection_down(conn.uuid or conn.name), self._handle_command_result)

    # ----- devices tab ----------------------------------------------------
    def _build_devices_tab(self, parent: tk.Widget) -> tk.Frame:
        frame = ttk.Frame(parent, padding=8)
        toolbar = ttk.Frame(frame)
        self.dev_refresh_btn = ttk.Button(toolbar, text="Refresh", command=self.refresh_devices)
        self.dev_connect_btn = ttk.Button(toolbar, text="Connect", command=self._device_connect)
        self.dev_disconnect_btn = ttk.Button(toolbar, text="Disconnect", command=self._device_disconnect)
        self.dev_refresh_btn.pack(side=tk.LEFT, padx=(0, 6))
        self.dev_connect_btn.pack(side=tk.LEFT, padx=(0, 6))
        self.dev_disconnect_btn.pack(side=tk.LEFT)
        toolbar.pack(fill=tk.X, pady=(0, 6))

        columns = ("device", "type", "state", "connection")
        self.dev_table = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        for col, text in zip(columns, ["Device", "Type", "State", "Connection"]):
            self.dev_table.heading(col, text=text)
            self.dev_table.column(col, width=150)
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.dev_table.yview)
        self.dev_table.configure(yscrollcommand=vsb.set)
        self.dev_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        return frame

    def _populate_devices(self, devices: list[Device]) -> None:
        self.dev_table.delete(*self.dev_table.get_children())
        for dev in devices:
            self.dev_table.insert("", tk.END, values=(dev.device, dev.type, dev.state, dev.connection))

    def _selected_device(self) -> Optional[Device]:
        sel = self.dev_table.selection()
        if not sel:
            return None
        vals = self.dev_table.item(sel[0], "values")
        device, type_, state, connection = vals
        return Device(device=device, type=type_, state=state, connection=connection)

    def _device_disconnect(self) -> None:
        dev = self._selected_device()
        if not dev:
            self.show_error("No selection", "Pick a device to disconnect.")
            return
        self.set_status(f"Disconnecting {dev.device}...")
        self.run_task(lambda: self.nmcli.device_disconnect(dev.device), self._handle_command_result)

    def _device_connect(self) -> None:
        dev = self._selected_device()
        if not dev:
            self.show_error("No selection", "Pick a device to connect.")
            return
        self.set_status(f"Connecting {dev.device}...")
        self.run_task(lambda: self.nmcli.device_connect(dev.device), self._handle_command_result)

    # ----- wifi tab -------------------------------------------------------
    def _build_wifi_tab(self, parent: tk.Widget) -> tk.Frame:
        frame = ttk.Frame(parent, padding=8)
        toolbar = ttk.Frame(frame)
        self.wifi_refresh_btn = ttk.Button(toolbar, text="Scan", command=self.refresh_wifi)
        self.wifi_connect_btn = ttk.Button(toolbar, text="Connect", command=self._wifi_connect)
        self.wifi_refresh_btn.pack(side=tk.LEFT, padx=(0, 6))
        self.wifi_connect_btn.pack(side=tk.LEFT)
        toolbar.pack(fill=tk.X, pady=(0, 6))

        columns = ("in_use", "ssid", "signal", "security", "mode", "freq", "channel")
        self.wifi_table = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        labels = ["In use", "SSID", "Signal", "Security", "Mode", "Freq", "Channel"]
        widths = [70, 200, 90, 140, 100, 100, 90]
        for col, text, width in zip(columns, labels, widths):
            self.wifi_table.heading(col, text=text)
            self.wifi_table.column(col, width=width)
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.wifi_table.yview)
        self.wifi_table.configure(yscrollcommand=vsb.set)
        self.wifi_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        return frame

    def _populate_wifi(self, nets: list[WifiNetwork]) -> None:
        self.wifi_table.delete(*self.wifi_table.get_children())
        for net in nets:
            self.wifi_table.insert(
                "",
                tk.END,
                values=("yes" if net.in_use else "no", net.ssid, net.signal, net.security, net.mode, net.frequency, net.channel),
            )

    def _selected_wifi(self) -> Optional[WifiNetwork]:
        sel = self.wifi_table.selection()
        if not sel:
            return None
        vals = self.wifi_table.item(sel[0], "values")
        in_use_text, ssid, signal, security, mode, freq, channel = vals
        return WifiNetwork(in_use=in_use_text == "yes", ssid=ssid, signal=signal, security=security, mode=mode, frequency=freq, channel=channel, rate="")

    def _wifi_connect(self) -> None:
        net = self._selected_wifi()
        if not net:
            self.show_error("No selection", "Pick a network to connect.")
            return
        
        password = None
        # Check if network requires authentication
        has_security = net.security and net.security.lower() not in ("--", "none", "")
        
        if has_security:
            # Prompt user for password
            pwd_dialog = simpledialog.askstring(
                "Wi-Fi Authentication",
                f"Enter password for:\n{net.ssid}\n\nNetwork: {net.security}",
                show="*",
                parent=self
            )
            if pwd_dialog is None:
                self.set_status("Connection cancelled")
                return
            password = pwd_dialog
        
        self.set_status(f"Connecting to {net.ssid}...")
        self.run_task(lambda: self.nmcli.wifi_connect(net.ssid, password=password), self._handle_command_result)

    # ----- raw nmcli tab --------------------------------------------------
    def _build_raw_tab(self, parent: tk.Widget) -> tk.Frame:
        frame = ttk.Frame(parent, padding=8)
        form = ttk.Frame(frame)
        self.raw_input = ttk.Entry(form)
        self.raw_input.insert(0, "device status")
        run_btn = ttk.Button(form, text="Run", command=self._run_raw_command)
        self.raw_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        run_btn.pack(side=tk.LEFT)
        form.pack(fill=tk.X, pady=(0, 6))

        self.raw_output = tk.Text(frame, height=16, wrap=tk.NONE)
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.raw_output.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.raw_output.xview)
        self.raw_output.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.raw_output.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        vsb.pack(fill=tk.Y, side=tk.RIGHT)
        hsb.pack(fill=tk.X, side=tk.BOTTOM)
        return frame

    def _run_raw_command(self) -> None:
        cmd = self.raw_input.get().strip()
        if not cmd:
            return
        self.set_status(f"Running nmcli {cmd}")
        self.run_task(lambda: self.nmcli.run_raw(cmd), self._handle_raw_result)

    def _handle_raw_result(self, result: Optional[CommandResult], err: Optional[Exception]) -> None:
        if err:
            self.show_error("nmcli error", str(err))
            self.set_status("Error")
            return
        assert result is not None
        output = ["$ " + " ".join(result.command), ""]
        if result.stdout:
            output.append(result.stdout)
        if result.stderr:
            output.append("stderr:\n" + result.stderr)
        output.append(f"exit {result.returncode}")
        self.raw_output.delete("1.0", tk.END)
        self.raw_output.insert("1.0", "\n".join(output))
        self.set_status("Done")
        self.refresh_all()

    # ----- refresh actions ------------------------------------------------
    def refresh_all(self) -> None:
        self.refresh_connections()
        self.refresh_devices()
        self.refresh_wifi()

    def refresh_connections(self) -> None:
        self.set_status("Loading connections...")
        self.run_task(self.nmcli.connection_list, self._on_connections_loaded)

    def _on_connections_loaded(self, conns: Optional[list[Connection]], err: Optional[Exception]) -> None:
        if err:
            self.show_error("nmcli error", str(err))
            self.set_status("Error")
            return
        assert conns is not None
        self._connections_cache = conns
        self._populate_connections(conns)
        self._update_dashboard(self._devices_cache, conns)
        self.set_status("Ready")

    def refresh_devices(self) -> None:
        self.set_status("Loading devices...")
        self.run_task(self.nmcli.device_status, self._on_devices_loaded)

    def _on_devices_loaded(self, devices: Optional[list[Device]], err: Optional[Exception]) -> None:
        if err:
            self.show_error("nmcli error", str(err))
            self.set_status("Error")
            return
        assert devices is not None
        self._devices_cache = devices
        self._populate_devices(devices)
        self._update_dashboard(devices, self._connections_cache)
        self.set_status("Ready")

    def refresh_wifi(self) -> None:
        self.set_status("Scanning Wi-Fi...")
        self.run_task(self.nmcli.wifi_scan, self._on_wifi_loaded)

    def _on_wifi_loaded(self, nets: Optional[list[WifiNetwork]], err: Optional[Exception]) -> None:
        if err:
            self.show_error("nmcli error", str(err))
            self.set_status("Error")
            return
        assert nets is not None
        self._populate_wifi(nets)
        self.set_status("Ready")

    # ----- generic command result ----------------------------------------
    def _handle_command_result(self, result: Optional[CommandResult], err: Optional[Exception]) -> None:
        if err:
            self.show_error("Error", str(err))
            self.set_status("Error")
            return
        assert result is not None
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
            if not error_msg:
                error_msg = "Command failed with no output"
            self.show_error("Connection failed", error_msg)
            self.set_status("Failed")
        else:
            success_msg = result.stdout.strip() if result.stdout else "Connected successfully"
            self.set_status(f"✓ {success_msg[:50]}")
        self.refresh_all()


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
