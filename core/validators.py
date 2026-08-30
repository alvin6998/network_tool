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

def is_valid_subnet_mask(value):

    """

    驗證子網路遮罩格式,例如 255.255.255.0、255.255.0.0。

    子網路遮罩不是IP位址,不能套用is_valid_ipv4()的規則

    (例如255.255.255.0會被is_reserved誤判為無效)。

    這裡改成用IPv4Network反推:合法的遮罩轉成二進位後,

    必須是「連續的1接連續的0」,不能中間斷開(例如255.0.255.0是無效遮罩)。

    """

    try:

        ip = ipaddress.IPv4Address(value)

    except ValueError:

        return False



    bits = int(ip)

    # 找出從最高位開始有幾個連續的1 (等同prefix length)

    prefix = 32

    while prefix > 0 and not (bits & (1 << (32 - prefix))):

        prefix -= 1



    # 用這個prefix重新產生遮罩,如果跟原本輸入一致,代表是合法的連續遮罩

    try:

        expected = ipaddress.IPv4Network(f"0.0.0.0/{prefix}").netmask

    except ValueError:

        return False



    if str(expected) != value:
        return False
 
    # /0 和 /32 雖然數學上是合法遮罩,但實務上不該讓使用者填這兩種
    if prefix == 0 or prefix == 32:
        return False
 
    return True
