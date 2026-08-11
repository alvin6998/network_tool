# Network Config Tool

一個像家用路由器管理頁面的 Windows 網路設定工具，用 Python + PySide6 打造。
提供圖形化介面管理網卡 IP / DNS 設定，並內建常用網路診斷工具。

## 功能

### Dashboard
- 顯示目前選擇網卡的連線狀態總覽（IP、Gateway、DHCP/Static 模式）

### IPv4 / DNS
- DHCP／Static 一鍵切換
- 手動設定 IP、子網路遮罩、預設閘道
- DNS 伺服器動態新增／刪除（不限筆數，不會像系統內建工具只能填 2 筆）
- 開啟時自動讀取並回填目前系統設定
- 切換網卡時自動重新載入對應設定
- 套用成功／失敗皆有明確視窗提示

### Public IP
- 查詢自己目前的公網 IP 與地理位置（城市／地區／國家／ISP）
- 也可查詢任意指定 IP 的地理位置
- 背景執行緒查詢，不卡 UI
- 查詢後有冷卻時間限制，避免頻繁呼叫導致 API 額度用盡

### Tools
- **Ping**：可調整次數、封包大小，支援強制 IPv4／IPv6
- **Traceroute**：支援強制 IPv4／IPv6，可選是否解析主機名稱
- **tcping**：TCP 連線測試（需額外安裝，見下方說明），可調整次數與 Port
- 所有工具皆為背景執行緒即時串流輸出，並支援中途停止

### 其他
- 啟動時自動請求系統管理員權限（UAC），修改網路設定所需
- 自動偵測系統 OEM 編碼，避免中文 Windows 下工具輸出亂碼

## 專案結構

```
network_tool/
├── main.py                  # 進入點，含 UAC 自動提權邏輯
├── core/
│   ├── netinfo.py           # 讀取網卡資訊、目前IP/DNS/Gateway設定
│   ├── netconfig.py         # 套用IP/DNS設定（netsh）
│   ├── validators.py        # IP格式驗證（ipaddress模組）
│   ├── public_ip.py         # 公網IP與地理位置查詢
│   └── network_tools.py     # Ping/Traceroute/tcping指令組建
├── ui/
│   ├── main_window.py        # 主視窗，左側導覽 + 右側頁面
│   ├── ipv4_panel.py         # IPv4/DNS設定頁面
│   ├── public_ip_panel.py    # 公網IP查詢頁面
│   └── tools_page.py         # Ping/Traceroute/tcping工具頁面
└── requirements.txt
```

## 需求

- Windows 10 / 11
- Python 3.10+
- 系統管理員權限（程式會自動請求）

### Python 套件

```bash
pip install -r requirements.txt
```

`requirements.txt`：
```
PySide6
psutil
```

### tcping（選用）

tcping 功能需要額外下載可執行檔（作者：Eli Fulkerson），並放到系統 PATH 或本程式同一層目錄：

- GitHub: https://github.com/elifulkerson/tcping
- 官方下載站（含雜湊驗證）: https://download.elifulkerson.com/files/tcping 
- 或使用 Chocolatey 安裝: `choco install tcping`

未安裝時，程式會提示下載連結，不影響其他功能使用。

> 注意：若下載 64 位元版本，檔名為 `tcping64.exe`，需自行重新命名為
> `tcping.exe`，或修改 `core/network_tools.py` 中的 `find_tcping()`
> 一併搜尋 `tcping64.exe`。

## 執行

```bash
python main.py
```

程式啟動時會跳出 UAC 對話框請求系統管理員權限，這是修改網路設定的必要步驟。

## 授權

本專案採用 [AGPL-3.0](LICENSE) 授權。

## 已知限制

- 目前僅支援 IPv4 設定；IPv6 尚未實作
- 僅支援 Windows（依賴 `netsh` 與 Windows 主控台工具）
- 在獲取本機 IP 地址時，程式可能會暫時凍結，原因是會在背景呼叫 PowerShell（啟動較慢，之後考慮改用其他方式取得資訊）