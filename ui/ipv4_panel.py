from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QRadioButton, QLineEdit, QPushButton, QButtonGroup,
    QMessageBox, QLabel
)
from core import netconfig, validators, netinfo

class DnsRow(QWidget):
    """單一一筆DNS輸入列,包含輸入框+刪除按鈕"""
    def __init__(self, on_remove, value=""):
        super().__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.input = QLineEdit()
        self.input.setText(value)
        self.input.setPlaceholderText("例如 1.1.1.1")
        layout.addWidget(self.input)

        self.remove_btn = QPushButton("－")
        self.remove_btn.setFixedWidth(30)
        self.remove_btn.clicked.connect(lambda: on_remove(self))
        layout.addWidget(self.remove_btn)

        self.setLayout(layout)

    def text(self):
        return self.input.text().strip()

    def set_enabled(self, enabled):
        self.input.setEnabled(enabled)
        self.remove_btn.setEnabled(enabled)

class IPv4Panel(QWidget):
    def __init__(self, get_current_interface):
        super().__init__()
        self.get_current_interface = get_current_interface
        self.dns_rows = []

        layout = QVBoxLayout()

        # DHCP / Static 切換
        mode_layout = QHBoxLayout()
        self.dhcp_radio = QRadioButton("DHCP (自動)")
        self.static_radio = QRadioButton("Static (手動)")
        self.static_radio.setChecked(True)
        self.mode_group = QButtonGroup()
        self.mode_group.addButton(self.dhcp_radio)
        self.mode_group.addButton(self.static_radio)
        mode_layout.addWidget(self.dhcp_radio)
        mode_layout.addWidget(self.static_radio)
        layout.addLayout(mode_layout)

        self.dhcp_radio.toggled.connect(self._toggle_mode)

        # IP/Mask/Gateway 表單
        form = QFormLayout()
        self.ip_input = QLineEdit()
        self.mask_input = QLineEdit()
        self.mask_input.setText("255.255.255.0")
        self.gateway_input = QLineEdit()

        form.addRow("IP Address", self.ip_input)
        form.addRow("Subnet Mask", self.mask_input)
        form.addRow("Gateway", self.gateway_input)
        layout.addLayout(form)

        # DNS 動態清單區
        layout.addWidget(QLabel("DNS Servers"))
        self.dns_list_layout = QVBoxLayout()
        layout.addLayout(self.dns_list_layout)

        self.add_dns_btn = QPushButton("＋ 新增DNS")
        self.add_dns_btn.clicked.connect(lambda: self.add_dns_row())
        layout.addWidget(self.add_dns_btn)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        apply_btn = QPushButton("套用設定")
        apply_btn.clicked.connect(self.apply_settings)
        layout.addWidget(apply_btn)

        self.setLayout(layout)
        self.form_widgets = [self.ip_input, self.mask_input, self.gateway_input]

        # 預設先給一筆空白DNS,不然畫面一開始DNS區塊會空空的
        self.add_dns_row()

    # ---------- DNS 動態清單相關 ----------

    def add_dns_row(self, value=""):
        row = DnsRow(on_remove=self.remove_dns_row, value=value)
        row.set_enabled(self.static_radio.isChecked())
        self.dns_rows.append(row)
        self.dns_list_layout.addWidget(row)

    def remove_dns_row(self, row):
        if row in self.dns_rows:
            self.dns_rows.remove(row)
            row.setParent(None)
            row.deleteLater()
        # 至少保留一筆空白列,避免整個DNS區塊變成空的
        if not self.dns_rows:
            self.add_dns_row()

    def clear_dns_rows(self):
        for row in self.dns_rows:
            row.setParent(None)
            row.deleteLater()
        self.dns_rows = []

    def get_dns_values(self):
        """回傳所有非空白的DNS輸入值"""
        return [row.text() for row in self.dns_rows if row.text()]

    # ---------- 模式切換 ----------

    def _toggle_mode(self, checked):
        for w in self.form_widgets:
            w.setEnabled(not checked)
        for row in self.dns_rows:
            row.set_enabled(not checked)
        self.add_dns_btn.setEnabled(not checked)

    # ---------- 載入目前設定 ----------

    def load_current_config(self):
        interface = self.get_current_interface()
        if not interface:
            return

        self.ip_input.clear()
        self.mask_input.clear()
        self.gateway_input.clear()
        self.clear_dns_rows()

        try:
            config = netinfo.get_current_config(interface)
        except Exception as e:
            self.status_label.setText(f"⚠️ 讀取目前設定失敗: {e}")
            self.add_dns_row()
            return

        if config["is_dhcp"]:
            self.dhcp_radio.setChecked(True)
        else:
            self.static_radio.setChecked(True)

        if config["ip"]:
            self.ip_input.setText(config["ip"])
        if config["mask"]:
            self.mask_input.setText(config["mask"])
        if config["gateway"]:
            self.gateway_input.setText(config["gateway"])

        dns_list = config["dns"]
        if dns_list:
            for dns in dns_list:
                self.add_dns_row(dns)
        else:
            self.add_dns_row()  # 沒有DNS也給一筆空白列可以填

        self.status_label.setText(f"目前設定已載入(共{len(dns_list)}台DNS)")

    # ---------- 套用設定 ----------

    def apply_settings(self):
        interface = self.get_current_interface()
        if not interface:
            self._show_error("請先選擇網路介面")
            return

        try:
            if self.dhcp_radio.isChecked():
                netconfig.set_dhcp_ip(interface)
                netconfig.set_dhcp_dns(interface)
                self.status_label.setText("✅ 已切換為 DHCP")
                self._show_success("已切換為 DHCP,IP與DNS將自動取得。")
            else:
                self._apply_static(interface)
                self.status_label.setText("✅ 靜態設定已套用")
                self._show_success("靜態IP與DNS設定已成功套用。")
        except netconfig.NetConfigError as e:
            self._show_error(f"套用失敗:\n{e}\n\n(請確認是否以系統管理員身分執行)")
        except Exception as e:
            self._show_error(f"未知錯誤:\n{e}")

    def _show_success(self, message):
        QMessageBox.information(self, "套用成功", message)

    def _show_error(self, message):
        QMessageBox.critical(self, "錯誤", message)

    def _apply_static(self, interface):
        ip = self.ip_input.text().strip()
        mask = self.mask_input.text().strip()
        gateway = self.gateway_input.text().strip()

        for label, value in [("IP", ip), ("Gateway", gateway)]:
            if not validators.is_valid_ipv4(value):
                raise ValueError(f"{label} 格式不正確: {value}")

        if not validators.is_valid_subnet_mask(mask):
            raise ValueError(f"子網路遮罩 格式不正確: {mask}")

        netconfig.set_static_ip(interface, ip, mask, gateway)

        dns_values = self.get_dns_values()
        for dns in dns_values:
            if not validators.is_valid_ipv4(dns):
                raise ValueError(f"DNS 格式不正確: {dns}")

        if dns_values:
            netconfig.set_static_dns(interface, dns_values)