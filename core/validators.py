import ipaddress

def is_valid_ipv4(value):
    try:
        ip = ipaddress.IPv4Address(value)
    except ValueError:
        return False

    # 排除不適合當作網卡IP的特殊位址
    if ip.is_unspecified:   # 0.0.0.0
        return False
    if ip.is_multicast:     # 224.0.0.0 ~ 239.255.255.255
        return False
    if ip.is_reserved:      # 保留位址
        return False
    if str(ip) == "255.255.255.255":  # 廣播位址
        return False

    return True