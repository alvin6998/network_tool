from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget, QLabel, QComboBox
)

from core import netinfo
from ui.ipv4_panel import IPv4Panel
from ui.public_ip_panel import PublicIPPanel
from ui.tools_page import ToolsPage

class DashboardPage(QWidget):
    """首頁總覽"""
    def __init__(self, get_current_interface):
        super().__init__()
        self.get_current_interface = get_current_interface
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Dashboard"))
        self.status_label = QLabel("尚未載入")
        layout.addWidget(self.status_label)
        layout.addStretch()
        self.setLayout(layout)

    def refresh(self):
        interface = self.get_current_interface()
        if not interface:
            self.status_label.setText("尚未選擇網路介面")
            return
        config = netinfo.get_current_config(interface)
        text = (
            f"介面: {interface}\n"
            f"模式: {'DHCP' if config['is_dhcp'] else 'Static'}\n"
            f"IP: {config['ip'] or '-'}\n"
            f"Gateway: {config['gateway'] or '-'}"
        )
        self.status_label.setText(text)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Network Config Tool")
        self.resize(800, 500)

        # ---------- 先準備好選到的網卡狀態,順序要在建立任何頁面之前 ----------
        self.interfaces = [iface["name"] for iface in netinfo.list_interfaces()]
        self._selected_interface = self.interfaces[0] if self.interfaces else None

        # ---------- 頂部:全域網卡選擇器 ----------
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("網路介面"))
        self.interface_combo = QComboBox()
        self.interface_combo.addItems(self.interfaces)
        self.interface_combo.currentTextChanged.connect(self._on_interface_changed)
        top_bar.addWidget(self.interface_combo, stretch=1)

        # ---------- 右側頁面 ----------
        self.stack = QStackedWidget()

        self.dashboard_page = DashboardPage(self._current_interface)
        self.ipv4_page = IPv4Panel(get_current_interface=self._current_interface)
        self.public_ip_page = PublicIPPanel()
        self.tools_page = ToolsPage()

        self.stack.addWidget(self.dashboard_page)   # index 0
        self.stack.addWidget(self.ipv4_page)         # index 1
        self.stack.addWidget(self.public_ip_page)    # index 2
        self.stack.addWidget(self.tools_page)         # index 3

        # ---------- 左側導覽 ----------
        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(160)
        for name in ["Dashboard", "IPv4 / DNS", "Public IP", "Tools"]:
            QListWidgetItem(name, self.nav_list)
        self.nav_list.currentRowChanged.connect(self._on_nav_changed)

        # ---------- 組裝整體版面 ----------
        body_layout = QHBoxLayout()
        body_layout.addWidget(self.nav_list)
        body_layout.addWidget(self.stack, stretch=1)

        root_layout = QVBoxLayout()
        root_layout.addLayout(top_bar)
        root_layout.addLayout(body_layout, stretch=1)

        container = QWidget()
        container.setLayout(root_layout)
        self.setCentralWidget(container)

        # ---------- 一切元件都建立完成後,才觸發第一次選取(會連動refresh) ----------
        self.nav_list.setCurrentRow(0)
        self.ipv4_page.load_current_config()

    def _current_interface(self):
        return self._selected_interface

    def _on_interface_changed(self, name):
        self._selected_interface = name
        # 切換網卡時,重新整理目前頁面的資料
        current_index = self.stack.currentIndex()
        if current_index == 0:
            self.dashboard_page.refresh()
        elif current_index == 1:
            self.ipv4_page.load_current_config()

    def _on_nav_changed(self, index):
        self.stack.setCurrentIndex(index)
        if index == 0:
            self.dashboard_page.refresh()
        elif index == 1:
            self.ipv4_page.load_current_config()