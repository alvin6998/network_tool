import psutil
import subprocess
import ipaddress
import json
import re
import os

POWERSHELL_PATH = os.path.join(
    os.environ.get("SystemRoot", r"C:\Windows"),
    "System32", "WindowsPowerShell", "v1.0", "powershell.exe"
)

def list_interfaces():
    """回傳所有網卡名稱與狀態"""
    stats = psutil.net_if_stats()
    addrs = psutil.net_if_addrs()
    result = []
    for name, stat in stats.items():
        ip = None
        for addr in addrs.get(name, []):
            if addr.family.name == "AF_INET":
                ip = addr.address
        result.append({
            "name": name,
            "is_up": stat.isup,
            "speed": stat.speed,
            "ip": ip
        })
    return result

def get_current_config(interface_name):
    """
    用 PowerShell 取得目前這張網卡完整的IPv4設定 (不受系統語言影響)
    回傳: ip, mask, gateway, dns(list), is_dhcp(bool)
    """
    ps_script = f'''
    $cfg = Get-NetIPConfiguration -InterfaceAlias "{interface_name}"
    $ipObj = Get-NetIPAddress -InterfaceAlias "{interface_name}" -AddressFamily IPv4 -ErrorAction SilentlyContinue
    $dhcpObj = Get-NetIPInterface -InterfaceAlias "{interface_name}" -AddressFamily IPv4 -ErrorAction SilentlyContinue
    $dns = Get-DnsClientServerAddress -InterfaceAlias "{interface_name}" -AddressFamily IPv4 -ErrorAction SilentlyContinue

    $result = [PSCustomObject]@{{
        ip       = $ipObj.IPAddress
        prefix   = $ipObj.PrefixLength
        gateway  = ($cfg.IPv4DefaultGateway).NextHop
        dns      = $dns.ServerAddresses
        is_dhcp  = ($dhcpObj.Dhcp -eq "Enabled")
    }}
    $result | ConvertTo-Json -Compress
    '''

    result = subprocess.run(
        [POWERSHELL_PATH, "-NoProfile", "-Command", ps_script],
        capture_output=True, text=True, encoding="utf-8"
    )

    try:
        data = json.loads(result.stdout.strip())
    except (json.JSONDecodeError, ValueError):
        return {"ip": None, "mask": None, "gateway": None, "dns": [], "is_dhcp": False}

    # PrefixLength (例如 24) 轉成子網路遮罩 (255.255.255.0)
    prefix = data.get("prefix")
    mask = _prefix_to_mask(prefix) if prefix else None

    dns = data.get("dns")
    if dns is None:
        dns_list = []
    elif isinstance(dns, list):
        dns_list = dns
    else:
        dns_list = [dns]  # 只有一台DNS時,PowerShell會回傳字串而不是陣列

    return {
        "ip": data.get("ip"),
        "mask": mask,
        "gateway": data.get("gateway"),
        "dns": dns_list,
        "is_dhcp": bool(data.get("is_dhcp"))
    }

def _prefix_to_mask(prefix_len):
    """把 CIDR 前綴長度 (例如 24) 轉成 255.255.255.0 這種格式"""
    network = ipaddress.IPv4Network(f"0.0.0.0/{int(prefix_len)}")
    return str(network.netmask)

def get_gateway_and_dns(interface_name):
    config = get_current_config(interface_name)
    return {"gateway": config["gateway"], "dns": config["dns"]}