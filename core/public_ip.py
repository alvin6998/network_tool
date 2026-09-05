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
        "region_code": data.get("region_code"),
        "country_code": data.get("country_code"),
        "country_code_iso3": data.get("country_code_iso3"),
        "country": data.get("country_name"),
        "country_capital": data.get("country_capital"),
        "country_tld": data.get("country_tld"),
        "continent_code": data.get("continent_code"),
        "in_eu": data.get("in_eu"),
        "postal": data.get("postal"),
        "lat": data.get("latitude"),
        "lon": data.get("longitude"),
        "timezone": data.get("timezone"),
        "utc_offset": data.get("utc_offset"),
        "country_calling_code": data.get("country_calling_code"),
        "currency": data.get("currency"),
        "currency_name": data.get("currency_name"),
        "languages": data.get("languages"),
        "asn": data.get("asn"),
        "isp": data.get("org"),
    }