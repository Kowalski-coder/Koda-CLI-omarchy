#!/usr/bin/env python3
"""
Koda CLI status and limits extractor for Omarchy Linux.
Fetches real-time quota from Koda Auth API with local credentials and cache fallback.
Supports automatic token refresh via deviceCode, persistent caching, and multilingual formatting.
"""

import sys
import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone

CREDS_FILE = os.path.expanduser("~/.config/koda/credentials.json")
CACHE_FILE = os.path.expanduser("~/.cache/omarchy/koda-cache.json")


def resolve_language(cli_args):
    lang = "en"
    if "--lang" in cli_args:
        idx = cli_args.index("--lang")
        if idx + 1 < len(cli_args):
            lang = cli_args[idx + 1].strip()
    else:
        lang_file = os.path.expanduser("~/.config/omarchy/language")
        if os.path.exists(lang_file):
            try:
                with open(lang_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        lang = content
            except Exception:
                pass
        else:
            lang = os.environ.get("OMARCHY_LANGUAGE", os.environ.get("LANG", "en"))

    return "ru" if lang.lower().startswith("ru") else "en"


def format_reset_time(iso_str, lang="en"):
    if not iso_str:
        return ""
    try:
        clean_str = iso_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        local_dt = dt.astimezone()
        now = datetime.now().astimezone()
        diff_days = (local_dt.date() - now.date()).days
        time_str = local_dt.strftime("%H:%M")

        if diff_days == 0:
            return f"Сегодня в {time_str}" if lang == "ru" else f"Today at {time_str}"
        elif diff_days == 1:
            return f"Завтра в {time_str}" if lang == "ru" else f"Tomorrow at {time_str}"
        else:
            if lang == "ru":
                months_ru = ["янв", "фев", "мар", "апр", "мая", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]
                m_name = months_ru[local_dt.month - 1] if 1 <= local_dt.month <= 12 else str(local_dt.month)
                return f"{local_dt.day} {m_name} {time_str}"
            else:
                months_en = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                m_name = months_en[local_dt.month - 1] if 1 <= local_dt.month <= 12 else str(local_dt.month)
                return f"{m_name} {local_dt.day}, {time_str}"
    except Exception:
        return iso_str[:16].replace("T", " ")


def format_model_group_name(mg, lang="en"):
    low = mg.lower()
    if "base" in low:
        return "Koda base"
    elif "pro" in low:
        return "Koda PRO"
    elif "other" in low or "external" in low:
        return "Сторонние модели" if lang == "ru" else "Third-party models"
    else:
        return mg.replace("-", " ").title()


def format_period_label(period, lang="en"):
    if lang == "ru":
        if period == "daily":
            return "в день"
        elif period == "monthly":
            return "в месяц"
        elif period == "balance":
            return "баланс"
        return period
    else:
        if period == "daily":
            return "daily"
        elif period == "monthly":
            return "monthly"
        elif period == "balance":
            return "balance"
        return period


def is_token_expired_or_soon(expires_at_str):
    if not expires_at_str:
        return False
    try:
        exp_clean = expires_at_str.replace("Z", "+00:00")
        exp_dt = datetime.fromisoformat(exp_clean)
        now_utc = datetime.now(timezone.utc)
        return (exp_dt - now_utc).total_seconds() <= 120
    except Exception:
        return False


def refresh_token(base_url, device_code, creds_path, creds_data):
    if not device_code:
        return None
    try:
        req = urllib.request.Request(
            f"{base_url}/auth/device/token",
            data=json.dumps({"deviceCode": device_code}).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "omarchy-koda-widget/1.0",
            },
        )
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            data = json.loads(resp.read().decode())
            new_token = data.get("token") or data.get("accessToken")
            if not new_token:
                return None

            kauth = creds_data.setdefault("kodaAuth", {})
            kauth["accessToken"] = new_token
            if data.get("expiresAt"):
                kauth["expiresAt"] = data["expiresAt"]
            if data.get("tier"):
                kauth["tier"] = data["tier"]
            if data.get("user"):
                kauth["user"] = data["user"]
            if data.get("usage"):
                kauth["usage"] = data["usage"]
            if data.get("id"):
                kauth["id"] = data["id"]
            if data.get("linked") is not None:
                kauth["linked"] = data["linked"]

            try:
                tmp_path = creds_path + ".tmp"
                fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
                with open(fd, "w", encoding="utf-8") as f:
                    json.dump(creds_data, f, indent=2, ensure_ascii=False)
                os.replace(tmp_path, creds_path)
            except Exception:
                pass

            return new_token
    except Exception:
        return None


def save_cache(raw_pools, extra_balance, tier, user, email):
    try:
        cache_dir = os.path.dirname(CACHE_FILE)
        os.makedirs(cache_dir, mode=0o700, exist_ok=True)
        try:
            os.chmod(cache_dir, 0o700)
        except Exception:
            pass

        tmp = CACHE_FILE + ".tmp"
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with open(fd, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "tier": tier,
                    "user": user,
                    "email": email,
                    "raw_pools": raw_pools,
                    "extra_balance": extra_balance,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
        os.replace(tmp, CACHE_FILE)
    except Exception:
        pass


def load_cache():
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def query_account_limits(base, token):
    req = urllib.request.Request(
        f"{base}/account/limits",
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": "omarchy-koda-widget/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=4.0) as resp:
        return json.loads(resp.read().decode())


def build_groups(raw_pools, extra_balance, lang):
    seen_keys = set()
    groups = []

    for item in raw_pools:
        mg = item.get("model_group", "")
        cur = float(item.get("current_calls", 0))
        m = float(item.get("max_calls", 0))
        period = item.get("period", "")
        next_ref = item.get("next_refresh", "")

        key = (mg, period)
        if key in seen_keys:
            continue
        seen_keys.add(key)

        if m <= 0 and cur <= 0:
            continue

        rem = max(0.0, m - cur)
        label = format_model_group_name(mg, lang)
        pct = (cur / m) if m > 0 else 0.0

        groups.append(
            {
                "name": label,
                "model_group": mg,
                "used": round(cur, 1),
                "max": round(m, 1),
                "remaining": round(rem, 1),
                "percent": round(pct, 3),
                "period": period,
                "period_label": format_period_label(period, lang),
                "reset_text": format_reset_time(next_ref, lang),
            }
        )

    if extra_balance > 0:
        extra_name = "Доп. баланс" if lang == "ru" else "Extra balance"
        groups.append(
            {
                "name": extra_name,
                "model_group": "balance",
                "used": 0.0,
                "max": extra_balance,
                "remaining": extra_balance,
                "percent": 1.0,
                "period": "balance",
                "period_label": format_period_label("balance", lang),
                "reset_text": "",
            }
        )

    return groups


def get_status(lang="en"):
    err_not_found = (
        "Файл авторизации Koda не найден (~/.config/koda/credentials.json)"
        if lang == "ru"
        else "Koda credentials file not found (~/.config/koda/credentials.json)"
    )
    err_auth_required = (
        "Требуется авторизация (koda)"
        if lang == "ru"
        else "Authentication required (`koda`)"
    )

    if not os.path.exists(CREDS_FILE):
        return {
            "ok": False,
            "error": err_not_found,
            "authenticated": False,
            "groups": [],
        }

    try:
        with open(CREDS_FILE, "r", encoding="utf-8") as f:
            creds = json.load(f)
    except Exception as e:
        return {
            "ok": False,
            "error": f"Error reading credentials: {e}",
            "authenticated": False,
            "groups": [],
        }

    kauth = creds.get("kodaAuth", {})
    token = kauth.get("accessToken")
    expires_at = kauth.get("expiresAt")
    device_code = kauth.get("deviceCode")
    base = kauth.get("baseUrl", "https://auth.kodacode.ru").rstrip("/")
    user = kauth.get("user", {})
    tier = kauth.get("tier", "Free")
    fallback_usage = kauth.get("usage", {})

    username = user.get("label") or user.get("firstName") or user.get("email") or "Koda User"
    email = user.get("email", "")

    result = {
        "ok": True,
        "authenticated": bool(token),
        "source": "cache",
        "user": username,
        "email": email,
        "tier": tier,
        "tooltip_text": "Koda CLI",
        "groups": [],
    }

    if not token and not device_code:
        result["error"] = err_auth_required
        result["authenticated"] = False
        return result

    # 1. Proactive Token Refresh if expired or expiring soon
    if is_token_expired_or_soon(expires_at) and device_code:
        new_token = refresh_token(base, device_code, CREDS_FILE, creds)
        if new_token:
            token = new_token
            result["authenticated"] = True

    # 2. Query Live Limits
    data = None
    if token:
        try:
            data = query_account_limits(base, token)
        except urllib.error.HTTPError as he:
            if he.code == 401 and device_code:
                new_token = refresh_token(base, device_code, CREDS_FILE, creds)
                if new_token:
                    token = new_token
                    try:
                        data = query_account_limits(base, token)
                    except Exception as e2:
                        result["network_warning"] = str(e2)
            else:
                result["network_warning"] = str(he)
        except Exception as e:
            result["network_warning"] = str(e)

    # 3. Process Live Data if available
    raw_pools = []
    extra_balance = 0.0

    if data and isinstance(data, dict) and "limits" in data:
        lims = data.get("limits", {})
        sub = lims.get("active_subscription") or lims.get("paid_tier") or lims.get("base_tier") or tier
        result["tier"] = sub.capitalize()
        result["source"] = "live"

        if isinstance(lims.get("base_usage"), list):
            raw_pools.extend(lims["base_usage"])
        if isinstance(lims.get("paid_usage"), list):
            raw_pools.extend(lims["paid_usage"])
        if isinstance(lims.get("business_usage"), list):
            raw_pools.extend(lims["business_usage"])

        extra_balance = float(lims.get("balance", 0))
        result["groups"] = build_groups(raw_pools, extra_balance, lang)
        save_cache(raw_pools, extra_balance, result["tier"], result["user"], result["email"])

    # 4. Fallback if live query failed
    if not result["groups"]:
        cached = load_cache()
        if cached:
            cached_pools = cached.get("raw_pools", [])
            cached_extra = float(cached.get("extra_balance", 0))
            if cached_pools or cached_extra > 0:
                result["groups"] = build_groups(cached_pools, cached_extra, lang)
                result["source"] = "cache"
                if cached.get("tier"):
                    result["tier"] = cached["tier"]
                result["cached_at"] = cached.get("timestamp", "")
            elif cached.get("groups"):
                # Migration fallback for existing older caches
                result["groups"] = cached["groups"]
                result["source"] = "cache"
                if cached.get("tier"):
                    result["tier"] = cached["tier"]
                result["cached_at"] = cached.get("timestamp", "")

        if not result["groups"] and fallback_usage:
            rem = float(fallback_usage.get("remaining", 0))
            m = float(fallback_usage.get("max", 0))
            period = fallback_usage.get("period", "daily")
            result["groups"].append(
                {
                    "name": "Koda base",
                    "model_group": "all",
                    "used": round(max(0.0, m - rem), 1),
                    "max": round(m, 1),
                    "remaining": round(rem, 1),
                    "percent": round((m - rem) / m, 3) if m > 0 else 0.0,
                    "period": period,
                    "period_label": format_period_label(period, lang),
                    "reset_text": "",
                }
            )

    # Construct clean tooltip text
    tips = [f"{g['name']}: {g['remaining']:.1f}" for g in result["groups"]]
    if tips:
        result["tooltip_text"] = "Koda CLI: " + " · ".join(tips)
    else:
        result["tooltip_text"] = "Koda CLI"

    return result


if __name__ == "__main__":
    lang = resolve_language(sys.argv)
    status = get_status(lang)
    print(json.dumps(status, ensure_ascii=False, indent=2))
