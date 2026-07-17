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

def is_frozen():
    """判斷目前是打包後的exe,還是直接用python執行的腳本"""
    return getattr(sys, "frozen", False)

def relaunch_as_admin():
    """用系統管理員權限重新啟動自己"""
    if is_frozen():
        # 打包後: sys.executable 就是這支 exe 本身
        target = sys.executable
        params = " ".join([f'"{a}"' for a in sys.argv[1:]])
    else:
        # 開發環境: sys.executable 是 python.exe,要帶上 main.py 路徑
        target = sys.executable
        script = os.path.abspath(sys.argv[0])
        params = " ".join([f'"{script}"'] + [f'"{a}"' for a in sys.argv[1:]])

    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", target, params, os.path.dirname(os.path.abspath(sys.argv[0])), 1
    )


if __name__ == "__main__":
    if os.name == "nt" and not is_admin():
        relaunch_as_admin()
        sys.exit(0)

    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())