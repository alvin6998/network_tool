import subprocess

class NetConfigError(Exception):
    pass

def _run_netsh(args):
    result = subprocess.run(
        ["netsh"] + args,
        capture_output=True, text=True, encoding="utf-8",
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    if result.returncode != 0:
        raise NetConfigError(result.stderr.strip() or result.stdout.strip())
    return result.stdout

def set_static_ip(interface_name, ip, subnet_mask, gateway):
    """設定固定IP"""
    _run_netsh([
        "interface", "ip", "set", "address",
        f"name={interface_name}",
        "static", ip, subnet_mask, gateway
    ])

def set_dhcp_ip(interface_name):
    """切回自動取得IP (DHCP)"""
    _run_netsh([
        "interface", "ip", "set", "address",
        f"name={interface_name}", "source=dhcp"
    ])

def set_static_dns(interface_name, dns_list):
    """
    設定固定DNS,dns_list是字串陣列,例如 ["1.1.1.1", "8.8.8.8", "61.31.233.1"]
    第一筆會被設成 primary,其餘依序用 index 加入
    """
    if not dns_list:
        return

    _run_netsh([
        "interface", "ip", "set", "dns",
        f"name={interface_name}", "static", dns_list[0], "primary"
    ])

    for i, dns in enumerate(dns_list[1:], start=2):
        _run_netsh([
            "interface", "ip", "add", "dns",
            f"name={interface_name}", dns, f"index={i}"
        ])

def set_dhcp_dns(interface_name):
    """切回自動取得DNS"""
    _run_netsh([
        "interface", "ip", "set", "dns",
        f"name={interface_name}", "source=dhcp"
    ])