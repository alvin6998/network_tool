import subprocess
import sys
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QTextEdit,
    QComboBox, QSpinBox, QMessageBox, QCheckBox
)
from PySide6.QtCore import QThread, Signal

from core import network_tools


def _get_console_encoding():
    """取得Windows主控台程式(ping/tracert)的輸出編碼"""
    if sys.platform == "win32":
        import ctypes
        codepage = ctypes.windll.kernel32.GetOEMCP()
        return f"cp{codepage}"
    return "utf-8"


class CommandWorker(QThread):
    """在背景執行subprocess,並把輸出一行一行即時丟回主執行緒"""
    line_received = Signal(str)
    finished_ok = Signal()
    failed = Signal(str)

    def __init__(self, command):
        super().__init__()
        self.command = command
        self._process = None
        self._stop_requested = False

    def run(self):
        encoding = _get_console_encoding()
        try:
            self._process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding=encoding,
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        except FileNotFoundError:
            self.failed.emit(f"找不到指令: {self.command[0]}")
            return
        except Exception as e:
            self.failed.emit(f"執行失敗: {e}")
            return

        for line in self._process.stdout:
            if self._stop_requested:
                break
            self.line_received.emit(line.rstrip())

        self._process.wait()
        self.finished_ok.emit()

    def stop(self):
        self._stop_requested = True
        if self._process and self._process.poll() is None:
            self._process.terminate()


class ToolsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None

        layout = QVBoxLayout()

        form = QFormLayout()

        self.tool_combo = QComboBox()
        self.tool_combo.addItems(["Ping", "Traceroute", "tcping"])
        self.tool_combo.currentTextChanged.connect(self._on_tool_changed)
        form.addRow("工具", self.tool_combo)

        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("例如 8.8.8.8 或 google.com")
        form.addRow("目標主機", self.host_input)

        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(443)
        self.port_label = QLabel("Port")
        form.addRow(self.port_label, self.port_input)

        self.count_input = QSpinBox()
        self.count_input.setRange(1, 100)
        self.count_input.setValue(4)
        self.count_label = QLabel("次數")
        form.addRow(self.count_label, self.count_input)

        self.ip_version_combo = QComboBox()
        self.ip_version_combo.addItems(["自動", "強制 IPv4", "強制 IPv6"])
        self.ip_version_label = QLabel("IP 版本")
        form.addRow(self.ip_version_label, self.ip_version_combo)

        self.packet_size_input = QSpinBox()
        self.packet_size_input.setRange(1, 65500)
        self.packet_size_input.setValue(32)
        self.packet_size_label = QLabel("封包大小 (bytes)")
        form.addRow(self.packet_size_label, self.packet_size_input)

        self.trace_ip_version_combo = QComboBox()
        self.trace_ip_version_combo.addItems(["自動", "強制 IPv4", "強制 IPv6"])
        self.trace_ip_version_label = QLabel("IP 版本")
        form.addRow(self.trace_ip_version_label, self.trace_ip_version_combo)

        self.resolve_hostname_checkbox = QCheckBox("解析主機名稱 (較慢)")
        self.resolve_hostname_checkbox.setChecked(False)
        form.addRow("", self.resolve_hostname_checkbox)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        self.run_btn = QPushButton("執行")
        self.run_btn.clicked.connect(self.run_tool)
        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self.stop_tool)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.run_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        self.output_box.setStyleSheet("font-family: Consolas, monospace;")
        layout.addWidget(self.output_box, stretch=1)

        self.setLayout(layout)
        self._on_tool_changed(self.tool_combo.currentText())

    def _on_tool_changed(self, tool_name):
        is_tcping = (tool_name == "tcping")
        self.port_input.setVisible(is_tcping)
        self.port_label.setVisible(is_tcping)

        is_ping_or_tcping = tool_name in ("Ping", "tcping")
        self.count_input.setVisible(is_ping_or_tcping)
        self.count_label.setVisible(is_ping_or_tcping)

        is_ping = (tool_name == "Ping")
        self.ip_version_combo.setVisible(is_ping)
        self.ip_version_label.setVisible(is_ping)
        self.packet_size_input.setVisible(is_ping)
        self.packet_size_label.setVisible(is_ping)

        is_trace = (tool_name == "Traceroute")
        self.trace_ip_version_combo.setVisible(is_trace)
        self.trace_ip_version_label.setVisible(is_trace)
        self.resolve_hostname_checkbox.setVisible(is_trace)

    def run_tool(self):
        host = self.host_input.text().strip()
        if not host:
            QMessageBox.warning(self, "提示", "請輸入目標主機")
            return

        tool_name = self.tool_combo.currentText()

        try:
            if tool_name == "Ping":
                ip_version_map = {"自動": "auto", "強制 IPv4": "ipv4", "強制 IPv6": "ipv6"}
                ip_version = ip_version_map[self.ip_version_combo.currentText()]
                command = network_tools.build_ping_command(
                    host,
                    self.count_input.value(),
                    ip_version=ip_version,
                    packet_size=self.packet_size_input.value()
                )
            elif tool_name == "Traceroute":
                ip_version_map = {"自動": "auto", "強制 IPv4": "ipv4", "強制 IPv6": "ipv6"}
                ip_version = ip_version_map[self.trace_ip_version_combo.currentText()]
                command = network_tools.build_tracert_command(
                    host,
                    ip_version=ip_version,
                    resolve_hostname=self.resolve_hostname_checkbox.isChecked()
                )
            elif tool_name == "tcping":
                command = network_tools.build_tcping_command(
                    host, self.port_input.value(), self.count_input.value()
                )
            else:
                return
        except FileNotFoundError:
            QMessageBox.critical(
                self, "找不到 tcping",
                "系統上沒有偵測到 tcping 執行檔。\n\n"
                "請至 https://github.com/bubenshchykov/tcping/releases 下載,\n"
                "並將 tcping.exe 放到系統PATH內的資料夾(或跟本程式同一層目錄)。"
            )
            return

        self.output_box.clear()
        self.output_box.append(f"$ {' '.join(command)}\n")

        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        self.worker = CommandWorker(command)
        self.worker.line_received.connect(self._append_line)
        self.worker.failed.connect(self._on_failed)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def stop_tool(self):
        if self.worker:
            self.worker.stop()

    def _append_line(self, line):
        self.output_box.append(line)

    def _on_failed(self, error_message):
        self.output_box.append(f"\n⚠️ {error_message}")

    def _on_finished(self):
        self.output_box.append("\n--- 執行結束 ---")
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)