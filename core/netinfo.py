import psutil
import ipaddress
import pythoncom
import wmi

def _get_wmi():
    """
    每次都建立新連線,因為這個函式可能在Qt背景執行緒被呼叫,
    WMI/COM物件不能跨執行緒共用,一定要先 CoInitialize。
    """
    pythoncom.CoInitialize()
    return wmi.WMI()

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
    用 WMI 取得目前這張網卡完整的IPv4設定 (不受系統語言影響,也不用開PowerShell process)
    回傳: ip, mask, gateway, dns(list), is_dhcp(bool)
    """
    empty = {"ip": None, "mask": None, "gateway": None, "dns": [], "is_dhcp": False}

    try:
        c = _get_wmi()

        # NetConnectionID 就是「網路連線」裡看到的名稱,
        # 對應到 netsh / PowerShell -InterfaceAlias 用的那個名字
        adapters = c.Win32_NetworkAdapter(NetConnectionID=interface_name)
        if not adapters:
            return empty
        idx = adapters[0].InterfaceIndex

        cfgs = c.Win32_NetworkAdapterConfiguration(InterfaceIndex=idx)
        if not cfgs:
            return empty
        cfg = cfgs[0]

        ip_list = cfg.IPAddress or []
        mask_list = cfg.IPSubnet or []
        gateway_list = cfg.DefaultIPGateway or []
        dns_list = list(cfg.DNSServerSearchOrder or [])

        # WMI回傳的IPAddress/IPSubnet裡IPv4和IPv6混在一起,取第一個IPv4的
        ip, mask = None, None
        for addr, m in zip(ip_list, mask_list):
            if _is_ipv4(addr):
                ip, mask = addr, m
                break

        gateway = None
        for gw in gateway_list:
            if _is_ipv4(gw):
                gateway = gw
                break

        return {
            "ip": ip,
            "mask": mask,
            "gateway": gateway,
            "dns": dns_list,
            "is_dhcp": bool(cfg.DHCPEnabled)
        }
    except Exception:
        return empty

def _is_ipv4(addr):
    try:
        return isinstance(ipaddress.ip_address(addr), ipaddress.IPv4Address)
    except ValueError:
        return False

def get_gateway_and_dns(interface_name):
    config = get_current_config(interface_name)
    return {"gateway": config["gateway"], "dns": config["dns"]}