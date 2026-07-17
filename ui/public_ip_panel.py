from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QPushButton,
    QMessageBox, QLineEdit
)
from PySide6.QtCore import QThread, Signal, QTimer
from core import public_ip, validators


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
        self.isp_label = QLabel("-")

        form.addRow("IP", self.ip_label)
        form.addRow("地理位置", self.location_label)
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

        self.isp_label.setText(info["isp"] or "-")

    def _on_failed(self, error_message):
        self.ip_label.setText("-")
        self.location_label.setText("-")
        self.isp_label.setText("-")
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