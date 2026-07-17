import sys
import ctypes
import os
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def relaunch_as_admin():
    """用系統管理員權限重新啟動自己,並帶上原本的參數"""
    script = os.path.abspath(sys.argv[0])
    params = " ".join([f'"{script}"'] + [f'"{a}"' for a in sys.argv[1:]])
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, params, os.path.dirname(script), 1
    )


if __name__ == "__main__":
    if os.name == "nt" and not is_admin():
        relaunch_as_admin()
        sys.exit(0)

    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())