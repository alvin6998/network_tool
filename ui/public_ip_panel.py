from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QPushButton,
    QMessageBox, QLineEdit
)
from PySide6.QtCore import QThread, Signal, QTimer
from core import public_ip, validators

CONTINENT_NAMES = {
    "AS": "亞洲",
    "EU": "歐洲",
    "NA": "北美洲",
    "SA": "南美洲",
    "AF": "非洲",
    "OC": "大洋洲",
    "AN": "南極洲",
}


class PublicIPWorker(QThread):
    """背景執行緒,負責打API,避免卡住主UI"""
    success = Signal(dict)
    failed = Signal(str)

    def __init__(self, ip=None):
        super().__init__()
        self.ip = ip

    def run(self):
        try:
            info = public_ip.get_public_ip_info(ip=self.ip)
            self.success.emit(info)
        except public_ip.PublicIPError as e:
            self.failed.emit(str(e))
        except Exception as e:
            self.failed.emit(f"未知錯誤: {e}")


class PublicIPPanel(QWidget):
    COOLDOWN_SECONDS = 30

    def __init__(self):
        super().__init__()
        self.worker = None
        self.remaining_cooldown = 0

        layout = QVBoxLayout()

        # ---------- 查詢目標輸入 ----------
        target_form = QFormLayout()
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("留空 = 查詢自己的公網IP")
        target_form.addRow("查詢目標", self.target_input)
        layout.addLayout(target_form)

        self.query_btn = QPushButton("查詢")
        self.query_btn.clicked.connect(self.query)
        layout.addWidget(self.query_btn)

        # ---------- 結果顯示 ----------
        form = QFormLayout()
        self.ip_label = QLabel("-")
        self.location_label = QLabel("-")
        self.postal_label = QLabel("-")
        self.latlon_label = QLabel("-")
        self.timezone_label = QLabel("-")
        self.utc_offset_label = QLabel("-")
        self.country_code_label = QLabel("-")
        self.calling_code_label = QLabel("-")
        self.currency_label = QLabel("-")
        self.languages_label = QLabel("-")
        self.continent_label = QLabel("-")
        self.in_eu_label = QLabel("-")
        self.asn_label = QLabel("-")
        self.isp_label = QLabel("-")

        form.addRow("IP", self.ip_label)
        form.addRow("地理位置", self.location_label)
        form.addRow("郵遞區號", self.postal_label)
        form.addRow("經緯度", self.latlon_label)
        form.addRow("時區", self.timezone_label)
        form.addRow("UTC偏移", self.utc_offset_label)
        form.addRow("國碼", self.country_code_label)
        form.addRow("國際冠碼", self.calling_code_label)
        form.addRow("貨幣", self.currency_label)
        form.addRow("語言", self.languages_label)
        form.addRow("洲別", self.continent_label)
        form.addRow("歐盟成員", self.in_eu_label)
        form.addRow("ASN", self.asn_label)
        form.addRow("ISP", self.isp_label)
        layout.addLayout(form)

        self.setLayout(layout)

        self.cooldown_timer = QTimer(self)
        self.cooldown_timer.timeout.connect(self._tick_cooldown)

    def query(self):
        if self.worker is not None and self.worker.isRunning():
            return

        target = self.target_input.text().strip()
        if target and not validators.is_valid_ipv4(target):
            QMessageBox.warning(self, "提示", f"IP格式不正確: {target}")
            return

        self.query_btn.setEnabled(False)
        self.query_btn.setText("查詢中...")

        self.worker = PublicIPWorker(ip=target if target else None)
        self.worker.success.connect(self._on_success)
        self.worker.failed.connect(self._on_failed)
        self.worker.finished.connect(self._start_cooldown)
        self.worker.start()

    def _on_success(self, info):
        self.ip_label.setText(info["ip"] or "-")

        location_parts = [p for p in [info["city"], info["region"], info["country"]] if p]
        deduped = []
        for part in location_parts:
            if not deduped or deduped[-1] != part:
                deduped.append(part)
        self.location_label.setText(", ".join(deduped) if deduped else "-")

        self.postal_label.setText(info.get("postal") or "-")

        lat, lon = info.get("lat"), info.get("lon")
        self.latlon_label.setText(f"{lat}, {lon}" if lat is not None and lon is not None else "-")

        self.timezone_label.setText(info.get("timezone") or "-")
        self.utc_offset_label.setText(info.get("utc_offset") or "-")

        country_code = info.get("country_code")
        country_code_iso3 = info.get("country_code_iso3")
        if country_code and country_code_iso3:
            self.country_code_label.setText(f"{country_code} / {country_code_iso3}")
        else:
            self.country_code_label.setText(country_code or country_code_iso3 or "-")

        self.calling_code_label.setText(info.get("country_calling_code") or "-")

        currency = info.get("currency")
        currency_name = info.get("currency_name")
        if currency and currency_name:
            self.currency_label.setText(f"{currency} ({currency_name})")
        else:
            self.currency_label.setText(currency or currency_name or "-")

        self.languages_label.setText(info.get("languages") or "-")
        continent_code = info.get("continent_code")
        if continent_code:
            continent_name = CONTINENT_NAMES.get(continent_code)
            self.continent_label.setText(
                f"{continent_name} ({continent_code})" if continent_name else continent_code
            )
        else:
            self.continent_label.setText("-")

        in_eu = info.get("in_eu")
        self.in_eu_label.setText("是" if in_eu else ("否" if in_eu is not None else "-"))

        self.asn_label.setText(info.get("asn") or "-")
        self.isp_label.setText(info.get("isp") or "-")

    def _on_failed(self, error_message):
        for label in [
            self.ip_label, self.location_label, self.postal_label,
            self.latlon_label, self.timezone_label, self.utc_offset_label,
            self.country_code_label, self.calling_code_label,
            self.currency_label, self.languages_label, self.continent_label,
            self.in_eu_label, self.asn_label, self.isp_label,
        ]:
            label.setText("-")
        QMessageBox.critical(self, "錯誤", error_message)

    def _start_cooldown(self):
        self.remaining_cooldown = self.COOLDOWN_SECONDS
        self._tick_cooldown()
        self.cooldown_timer.start(1000)

    def _tick_cooldown(self):
        if self.remaining_cooldown <= 0:
            self.cooldown_timer.stop()
            self.query_btn.setEnabled(True)
            self.query_btn.setText("查詢")
            return

        self.query_btn.setText(f"請稍候 ({self.remaining_cooldown}s)")
        self.remaining_cooldown -= 1