import urllib.request
import json


class PublicIPError(Exception):
    pass


def get_public_ip_info(ip=None, timeout=5):
    """
    查詢公網IP與地理位置資訊
    ip: 指定要查詢的IP,留空(None)則查詢自己目前的公網IP
    回傳: ip, city, region, country, isp, lat, lon
    """
    target = ip.strip() if ip else ""
    url = f"https://ipapi.co/{target}/json/" if target else "https://ipapi.co/json/"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "network_tool"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        raise PublicIPError(f"查詢失敗,請檢查網路連線或IP格式: {e}")

    if data.get("error"):
        raise PublicIPError(data.get("reason", "API回傳錯誤"))

    return {
        "ip": data.get("ip"),
        "city": data.get("city"),
        "region": data.get("region"),
        "country": data.get("country_name"),
        "isp": data.get("org"),
        "lat": data.get("latitude"),
        "lon": data.get("longitude"),
    }