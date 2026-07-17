import subprocess
import shutil


def find_tcping():
    """檢查系統PATH或當前目錄是否有tcping可執行檔"""
    return shutil.which("tcping") or shutil.which("tcping.exe")


def build_ping_command(host, count=4, ip_version="auto", packet_size=32):
    """
    ip_version: "auto" | "ipv4" | "ipv6"
    packet_size: 傳送緩衝區大小 (bytes)
    """
    command = ["ping", "-n", str(count)]

    if ip_version == "ipv4":
        command.append("-4")
    elif ip_version == "ipv6":
        command.append("-6")

    if packet_size and packet_size != 32:
        command.extend(["-l", str(packet_size)])

    command.append(host)
    return command


def build_tracert_command(host, ip_version="auto", resolve_hostname=False):
    """
    ip_version: "auto" | "ipv4" | "ipv6"
    resolve_hostname: False時加上 -d (不解析主機名稱,速度較快)
    """
    command = ["tracert"]

    if not resolve_hostname:
        command.append("-d")

    if ip_version == "ipv4":
        command.append("-4")
    elif ip_version == "ipv6":
        command.append("-6")

    command.append(host)
    return command


def build_tcping_command(host, port, count=4):
    tcping_path = find_tcping()
    if not tcping_path:
        raise FileNotFoundError("tcping")
    return [tcping_path, "-n", str(count), host, str(port)]