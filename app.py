import json
import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import requests
import streamlit as st

try:
    from supabase import create_client, Client
except Exception:  # supabase is optional during local tests
    create_client = None
    Client = None

st.set_page_config(page_title="Macro Tracker", page_icon="🔥", layout="centered", initial_sidebar_state="collapsed")

# ─────────────────────────────────────────────────────────────────────────────
# STYLE
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;600&display=swap');
html, body, [class*="css"] { font-family:'DM Sans', sans-serif; background:#0f0f0f; color:#f0f0f0; }
h1,h2,h3 { font-family:'Space Mono', monospace; }
.stApp { background:#0f0f0f; }
.block { background:#111; border:1px solid #222; border-radius:16px; padding:18px; margin:10px 0; }
.hero { background:#111; border:1px solid #222; border-radius:18px; padding:22px 14px; text-align:center; margin:12px 0; }
.hero-kcal { font-family:'Space Mono', monospace; font-size:3.6rem; font-weight:700; color:#e8ff5a; line-height:1; letter-spacing:-2px; }
.hero-label { font-size:.68rem; color:#555; text-transform:uppercase; letter-spacing:3px; margin-bottom:16px; }
.macro-row { display:grid; grid-template-columns:repeat(4,1fr); gap:8px; border-top:1px solid #1f1f1f; padding-top:14px; }
.macro-pill { background:#151515; border:1px solid #222; border-radius:12px; padding:10px 4px; }
.macro-val { font-family:'Space Mono', monospace; font-size:1.15rem; font-weight:700; }
.macro-label { font-size:.62rem; color:#666; text-transform:uppercase; letter-spacing:1px; }
.gauge-wrap { margin:10px 0; }
.gauge-label { display:flex; justify-content:space-between; font-size:.72rem; color:#777; margin-bottom:4px; }
.gauge-bar-bg { background:#1a1a1a; border:1px solid #2a2a2a; border-radius:999px; height:16px; overflow:hidden; }
.gauge-bar-fill { height:100%; border-radius:999px; }
.color-low { background:linear-gradient(90deg,#5a8fff,#0055cc); }
.color-ok { background:linear-gradient(90deg,#e8ff5a,#a8cc00); }
.color-over { background:linear-gradient(90deg,#ff5a5a,#cc0000); }
.section-title { font-family:'Space Mono', monospace; font-size:.68rem; letter-spacing:2px; text-transform:uppercase; color:#555; margin:22px 0 8px; border-bottom:1px solid #1b1b1b; padding-bottom:6px; }
.food-card, .meal-card { background:#151515; border:1px solid #252525; border-radius:12px; padding:12px 14px; margin:6px 0; }
.food-title { display:flex; justify-content:space-between; gap:10px; align-items:center; }
.food-name { font-weight:600; }
.food-kcal { color:#e8ff5a; font-family:'Space Mono', monospace; font-weight:700; white-space:nowrap; }
.muted { color:#666; font-size:.73rem; }
.stButton > button { background:#e8ff5a !important; color:#0f0f0f !important; border:0 !important; border-radius:10px !important; font-family:'Space Mono', monospace !important; font-weight:700 !important; width:100% !important; }
.stButton > button:hover { background:#d4eb3a !important; }
.stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] { background:#1a1a1a !important; color:#f0f0f0 !important; border-color:#333 !important; }
.small-chip { display:inline-block; padding:3px 8px; border-radius:999px; background:#1b1b1b; color:#777; font-size:.68rem; margin-right:4px; }
.notice { background:#171717; border:1px dashed #333; border-radius:12px; padding:12px; color:#777; font-size:.8rem; }
</style>
""",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# DEFAULT DATA
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_FOODS: Dict[str, Dict[str, Any]] = {
    "Riz basmati cru": {"kcal": 356, "proteines": 7.6, "glucides": 78.0, "lipides": 0.9, "fibres": 1.0, "source": "Ciqual"},
    "Riz basmati cuit": {"kcal": 130, "proteines": 2.7, "glucides": 28.0, "lipides": 0.3, "fibres": 0.4, "source": "Estimation"},
    "Pâtes crues": {"kcal": 358, "proteines": 12.5, "glucides": 70.2, "lipides": 1.8, "fibres": 3.0, "source": "Ciqual"},
    "Pâtes cuites": {"kcal": 150, "proteines": 5.0, "glucides": 30.0, "lipides": 0.9, "fibres": 1.8, "source": "Estimation"},
    "Lentilles vertes crues": {"kcal": 311, "proteines": 24.0, "glucides": 45.0, "lipides": 1.4, "fibres": 11.4, "source": "Ciqual"},
    "Lentilles vertes cuites": {"kcal": 116, "proteines": 9.0, "glucides": 20.0, "lipides": 0.4, "fibres": 7.9, "source": "Estimation"},
    "Filet de poulet cru": {"kcal": 110, "proteines": 23.0, "glucides": 0.0, "lipides": 1.5, "fibres": 0.0, "source": "Ciqual"},
    "Filet de poulet cuit": {"kcal": 165, "proteines": 31.0, "glucides": 0.0, "lipides": 3.6, "fibres": 0.0, "source": "Estimation"},
    "Thon en conserve au naturel": {"kcal": 116, "proteines": 25.5, "glucides": 0.0, "lipides": 1.0, "fibres": 0.0, "source": "Ciqual"},
    "Oeuf entier": {"kcal": 145, "proteines": 12.5, "glucides": 0.7, "lipides": 10.0, "fibres": 0.0, "source": "Ciqual"},
    "Skyr nature": {"kcal": 60, "proteines": 10.0, "glucides": 4.0, "lipides": 0.2, "fibres": 0.0, "source": "Moyenne"},
    "Flocons d'avoine": {"kcal": 370, "proteines": 13.5, "glucides": 58.0, "lipides": 7.0, "fibres": 10.0, "source": "Moyenne"},
    "Graines de chia": {"kcal": 486, "proteines": 16.5, "glucides": 42.0, "lipides": 30.7, "fibres": 34.4, "source": "Moyenne"},
    "Patate douce crue": {"kcal": 86, "proteines": 1.6, "glucides": 20.1, "lipides": 0.1, "fibres": 3.0, "source": "Moyenne"},
    "Brocoli surgelé": {"kcal": 35, "proteines": 2.8, "glucides": 4.0, "lipides": 0.4, "fibres": 2.6, "source": "Ciqual"},
    "Haricots rouges cuits": {"kcal": 127, "proteines": 8.7, "glucides": 22.8, "lipides": 0.5, "fibres": 6.4, "source": "Moyenne"},
    "Huile d'olive": {"kcal": 884, "proteines": 0.0, "glucides": 0.0, "lipides": 100.0, "fibres": 0.0, "source": "Moyenne"},
}
DEFAULT_SETTINGS = {"objectif_kcal": 2600, "objectif_prot": 170, "objectif_gluc": 320, "objectif_lip": 80}
MACRO_KEYS = ["kcal", "proteines", "glucides", "lipides", "fibres"]

# ─────────────────────────────────────────────────────────────────────────────
# SAFE SECRETS / SUPABASE
# ─────────────────────────────────────────────────────────────────────────────
def get_secret(name: str, default: str = "") -> str:
    try:
        return st.secrets.get(name, default)  # type: ignore[attr-defined]
    except Exception:
        return default

@st.cache_resource(show_spinner=False)
def get_supabase() -> Optional[Any]:
    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_ANON_KEY")
    if not url or not key or create_client is None:
        return None
    try:
        return create_client(url, key)
    except Exception:
        return None

sb = get_supabase()
USE_SUPABASE = sb is not None

# ─────────────────────────────────────────────────────────────────────────────
# GENERIC HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def calc_macros(food: Dict[str, Any], grams: float) -> Dict[str, float]:
    ratio = grams / 100
    return {k: round(safe_float(food.get(k, 0)) * ratio, 1) for k in MACRO_KEYS}


def sum_macros(entries: List[Dict[str, Any]]) -> Dict[str, float]:
    total = {k: 0.0 for k in MACRO_KEYS}
    for entry in entries:
        for key in MACRO_KEYS:
            total[key] += safe_float(entry.get(key, 0))
    return {k: round(v, 1) for k, v in total.items()}


def gauge_html(label: str, value: float, target: float, unit: str) -> str:
    if not target:
        return ""
    raw_pct = value / target * 100
    pct = max(0, min(raw_pct, 100))
    cls = "color-ok" if 85 <= raw_pct <= 105 else ("color-over" if raw_pct > 105 else "color-low")
    return f"""
    <div class="gauge-wrap">
        <div class="gauge-label"><span>{label}</span><span>{value:.0f} / {target:.0f} {unit}</span></div>
        <div class="gauge-bar-bg"><div class="gauge-bar-fill {cls}" style="width:{pct:.1f}%"></div></div>
    </div>"""


def today_key() -> str:
    return str(date.today())


def parse_jsonish(text: str) -> Optional[Dict[str, Any]]:
    text = text.strip().replace("```json", "").replace("```", "").strip()
    match = re.search(r"\{.*\}", text, re.S)
    if match:
        text = match.group(0)
    try:
        return json.loads(text)
    except Exception:
        return None


def rerun():
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# LOCAL FALLBACK STORAGE: useful for local/dev, not for real public production.
# ─────────────────────────────────────────────────────────────────────────────
def init_local_state() -> None:
    st.session_state.setdefault("local_foods", dict(DEFAULT_FOODS))
    st.session_state.setdefault("local_entries", [])
    st.session_state.setdefault("local_meals", {})
    st.session_state.setdefault("local_settings", dict(DEFAULT_SETTINGS))

# ─────────────────────────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────────────────────────
def current_user_id() -> str:
    if USE_SUPABASE and st.session_state.get("sb_user"):
        return st.session_state["sb_user"]["id"]
    return "demo-user"


def auth_gate() -> bool:
    init_local_state()
    if not USE_SUPABASE:
        st.sidebar.warning("Mode démo : ajoute SUPABASE_URL et SUPABASE_ANON_KEY pour activer comptes + sauvegarde durable.")
        st.session_state.setdefault("sb_user", {"id": "demo-user", "email": "demo@local"})
        return True

    if st.session_state.get("sb_user"):
        with st.sidebar:
            st.caption(f"Connecté : {st.session_state['sb_user'].get('email', '')}")
            if st.button("Se déconnecter"):
                st.session_state.pop("sb_user", None)
                try:
                    sb.auth.sign_out()
                except Exception:
                    pass
                rerun()
        return True

    st.title("🔥 Macro Tracker")
    st.markdown("Connecte-toi pour garder tes macros, repas et objectifs séparés des autres utilisateurs.")
    mode = st.radio("", ["Connexion", "Créer un compte"], horizontal=True, label_visibility="collapsed")
    email = st.text_input("Email")
    password = st.text_input("Mot de passe", type="password")
    col1, col2 = st.columns(2)
    with col1:
        action = st.button("Continuer")
    with col2:
        demo = st.button("Tester sans compte")
    if demo:
        st.session_state["sb_user"] = {"id": "demo-user", "email": "demo@local"}
        rerun()
    if action:
        if not email or not password:
            st.error("Entre un email et un mot de passe.")
            return False
        try:
            if mode == "Créer un compte":
                res = sb.auth.sign_up({"email": email, "password": password})
            else:
                res = sb.auth.sign_in_with_password({"email": email, "password": password})
            user = res.user
            if user:
                st.session_state["sb_user"] = {"id": user.id, "email": user.email}
                ensure_user_defaults(user.id)
                rerun()
            else:
                st.info("Compte créé. Si Supabase demande une confirmation email, confirme puis reconnecte-toi.")
        except Exception as exc:
            st.error(f"Erreur authentification : {exc}")
    return False

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE CRUD
# ─────────────────────────────────────────────────────────────────────────────
def ensure_user_defaults(user_id: str) -> None:
    if not USE_SUPABASE or user_id == "demo-user":
        return
    try:
        existing = sb.table("settings").select("user_id").eq("user_id", user_id).execute().data
        if not existing:
            sb.table("settings").insert({"user_id": user_id, **DEFAULT_SETTINGS}).execute()
        food_count = sb.table("foods").select("id").eq("user_id", user_id).limit(1).execute().data
        if not food_count:
            rows = [{"user_id": user_id, "name": name, **values} for name, values in DEFAULT_FOODS.items()]
            sb.table("foods").insert(rows).execute()
    except Exception as exc:
        st.warning(f"Initialisation Supabase incomplète : {exc}")


def load_settings(user_id: str) -> Dict[str, float]:
    if USE_SUPABASE and user_id != "demo-user":
        try:
            rows = sb.table("settings").select("*").eq("user_id", user_id).execute().data
            if rows:
                return {k: safe_float(rows[0].get(k, DEFAULT_SETTINGS[k])) for k in DEFAULT_SETTINGS}
            ensure_user_defaults(user_id)
        except Exception as exc:
            st.warning(f"Impossible de charger les objectifs : {exc}")
    return st.session_state["local_settings"]


def save_settings(user_id: str, settings: Dict[str, Any]) -> None:
    clean = {k: safe_float(settings.get(k, DEFAULT_SETTINGS[k])) for k in DEFAULT_SETTINGS}
    if USE_SUPABASE and user_id != "demo-user":
        sb.table("settings").upsert({"user_id": user_id, **clean}, on_conflict="user_id").execute()
    else:
        st.session_state["local_settings"] = clean


def load_foods(user_id: str) -> Dict[str, Dict[str, Any]]:
    if USE_SUPABASE and user_id != "demo-user":
        try:
            rows = sb.table("foods").select("*").eq("user_id", user_id).order("name").execute().data
            if not rows:
                ensure_user_defaults(user_id)
                rows = sb.table("foods").select("*").eq("user_id", user_id).order("name").execute().data
            foods = {}
            for r in rows:
                foods[r["name"]] = {k: safe_float(r.get(k, 0)) for k in MACRO_KEYS}
                foods[r["name"]]["source"] = r.get("source", "")
            return foods
        except Exception as exc:
            st.warning(f"Impossible de charger la base aliments : {exc}")
    return st.session_state["local_foods"]


def upsert_food(user_id: str, name: str, food: Dict[str, Any]) -> None:
    row = {"user_id": user_id, "name": name.strip(), **{k: safe_float(food.get(k, 0)) for k in MACRO_KEYS}, "source": food.get("source", "Manuel")}
    if USE_SUPABASE and user_id != "demo-user":
        sb.table("foods").upsert(row, on_conflict="user_id,name").execute()
    else:
        st.session_state["local_foods"][name.strip()] = {k: row[k] for k in MACRO_KEYS} | {"source": row["source"]}


def delete_food(user_id: str, name: str) -> None:
    if USE_SUPABASE and user_id != "demo-user":
        sb.table("foods").delete().eq("user_id", user_id).eq("name", name).execute()
    else:
        st.session_state["local_foods"].pop(name, None)


def load_entries(user_id: str, start: Optional[str] = None, end: Optional[str] = None) -> List[Dict[str, Any]]:
    if USE_SUPABASE and user_id != "demo-user":
        try:
            q = sb.table("daily_entries").select("*").eq("user_id", user_id).order("entry_date", desc=True).order("created_at", desc=True)
            if start:
                q = q.gte("entry_date", start)
            if end:
                q = q.lte("entry_date", end)
            return q.execute().data or []
        except Exception as exc:
            st.warning(f"Impossible de charger le journal : {exc}")
    entries = st.session_state["local_entries"]
    if start:
        entries = [e for e in entries if e.get("entry_date") >= start]
    if end:
        entries = [e for e in entries if e.get("entry_date") <= end]
    return sorted(entries, key=lambda e: (e.get("entry_date", ""), e.get("id", 0)), reverse=True)


def add_entry(user_id: str, food_name: str, grams: float, macros: Dict[str, Any], entry_date: str, meal_name: str = "") -> None:
    row = {"user_id": user_id, "entry_date": entry_date, "food_name": food_name, "grams": grams, "meal_name": meal_name or None, **{k: safe_float(macros.get(k, 0)) for k in MACRO_KEYS}}
    if USE_SUPABASE and user_id != "demo-user":
        sb.table("daily_entries").insert(row).execute()
    else:
        row["id"] = int(datetime.now().timestamp() * 1000)
        row["created_at"] = datetime.now().isoformat()
        st.session_state["local_entries"].append(row)


def delete_entry(user_id: str, entry_id: Any) -> None:
    if USE_SUPABASE and user_id != "demo-user":
        sb.table("daily_entries").delete().eq("user_id", user_id).eq("id", entry_id).execute()
    else:
        st.session_state["local_entries"] = [e for e in st.session_state["local_entries"] if str(e.get("id")) != str(entry_id)]


def clear_day(user_id: str, entry_date: str) -> None:
    if USE_SUPABASE and user_id != "demo-user":
        sb.table("daily_entries").delete().eq("user_id", user_id).eq("entry_date", entry_date).execute()
    else:
        st.session_state["local_entries"] = [e for e in st.session_state["local_entries"] if e.get("entry_date") != entry_date]


def load_meals(user_id: str) -> Dict[str, Dict[str, Any]]:
    if USE_SUPABASE and user_id != "demo-user":
        try:
            meals = sb.table("meals").select("id,name,pinned").eq("user_id", user_id).order("name").execute().data or []
            if not meals:
                return {}
            meal_ids = [m["id"] for m in meals]
            items = sb.table("meal_items").select("meal_id,food_name,grams").in_("meal_id", meal_ids).execute().data or []
            by_id: Dict[Any, List[Dict[str, Any]]] = {}
            for it in items:
                by_id.setdefault(it["meal_id"], []).append({"food": it["food_name"], "grams": int(it["grams"])})
            return {m["name"]: {"id": m["id"], "pinned": m.get("pinned", False), "items": by_id.get(m["id"], [])} for m in meals}
        except Exception as exc:
            st.warning(f"Impossible de charger les repas : {exc}")
    return st.session_state["local_meals"]


def save_meal(user_id: str, name: str, items: List[Dict[str, Any]], pinned: bool = False) -> None:
    name = name.strip()
    if USE_SUPABASE and user_id != "demo-user":
        res = sb.table("meals").upsert({"user_id": user_id, "name": name, "pinned": pinned}, on_conflict="user_id,name").execute().data
        meal_rows = sb.table("meals").select("id").eq("user_id", user_id).eq("name", name).execute().data
        if meal_rows:
            meal_id = meal_rows[0]["id"]
            sb.table("meal_items").delete().eq("meal_id", meal_id).execute()
            rows = [{"meal_id": meal_id, "food_name": it["food"], "grams": int(it["grams"])} for it in items if int(it.get("grams", 0)) > 0]
            if rows:
                sb.table("meal_items").insert(rows).execute()
    else:
        st.session_state["local_meals"][name] = {"items": items, "pinned": pinned}


def delete_meal(user_id: str, meal: Dict[str, Any], name: str) -> None:
    if USE_SUPABASE and user_id != "demo-user":
        meal_id = meal.get("id")
        if meal_id:
            sb.table("meal_items").delete().eq("meal_id", meal_id).execute()
            sb.table("meals").delete().eq("user_id", user_id).eq("id", meal_id).execute()
    else:
        st.session_state["local_meals"].pop(name, None)


def toggle_pin_meal(user_id: str, meal: Dict[str, Any], name: str) -> None:
    new_val = not bool(meal.get("pinned"))
    if USE_SUPABASE and user_id != "demo-user":
        sb.table("meals").update({"pinned": new_val}).eq("user_id", user_id).eq("id", meal.get("id")).execute()
    else:
        st.session_state["local_meals"][name]["pinned"] = new_val

# ─────────────────────────────────────────────────────────────────────────────
# EXTERNAL DATA
# ─────────────────────────────────────────────────────────────────────────────
def search_openfoodfacts(query: str) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    params = {"search_terms": query, "search_simple": 1, "action": "process", "json": 1, "page_size": 10, "lc": "fr"}
    try:
        r = requests.get("https://world.openfoodfacts.org/cgi/search.pl", params=params, timeout=10)
        r.raise_for_status()
        products = r.json().get("products", [])
        results: List[Dict[str, Any]] = []
        for p in products:
            n = p.get("nutriments", {}) or {}
            name = p.get("product_name_fr") or p.get("product_name") or p.get("product_name_en") or ""
            kcal = n.get("energy-kcal_100g")
            if kcal is None and n.get("energy_100g") is not None:
                kcal = safe_float(n.get("energy_100g")) / 4.184
            if not name or kcal is None or safe_float(kcal) <= 0:
                continue
            results.append({
                "name": name.strip(),
                "kcal": round(safe_float(kcal), 1),
                "proteines": round(safe_float(n.get("proteins_100g")), 1),
                "glucides": round(safe_float(n.get("carbohydrates_100g")), 1),
                "lipides": round(safe_float(n.get("fat_100g")), 1),
                "fibres": round(safe_float(n.get("fiber_100g")), 1),
                "source": "Open Food Facts",
            })
        seen, clean = set(), []
        for item in results:
            key = item["name"].lower()
            if key not in seen:
                seen.add(key)
                clean.append(item)
        return clean[:8], None
    except Exception as exc:
        return [], f"Open Food Facts indisponible ou réponse invalide : {exc}"


def generate_ai_suggestion(settings: Dict[str, Any], totals: Dict[str, Any], foods: Dict[str, Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    api_key = get_secret("ANTHROPIC_API_KEY")
    if not api_key:
        return None, "Clé ANTHROPIC_API_KEY absente dans Streamlit secrets."
    kcal_gap = max(0, round(settings["objectif_kcal"] - totals["kcal"]))
    prot_gap = max(0, round(settings["objectif_prot"] - totals["proteines"]))
    gluc_gap = max(0, round(settings["objectif_gluc"] - totals["glucides"]))
    lip_gap = max(0, round(settings["objectif_lip"] - totals["lipides"]))
    food_list = ", ".join(list(foods.keys())[:40])
    prompt = f"""Tu es un coach nutrition. Objectif restant aujourd'hui : {kcal_gap} kcal, {prot_gap} g protéines, {gluc_gap} g glucides, {lip_gap} g lipides.
Aliments disponibles : {food_list}.
Propose une suggestion réaliste avec 2 à 4 aliments. Réponds uniquement en JSON valide :
{{"title":"repas", "items":[{{"name":"Filet de poulet cuit","grams":180}},{{"name":"Riz basmati cuit","grams":220}}], "note":"phrase courte"}}
"""
    try:
        res = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type": "application/json", "x-api-key": api_key, "anthropic-version": "2023-06-01"},
            json={"model": "claude-haiku-4-5-20251001", "max_tokens": 500, "messages": [{"role": "user", "content": prompt}]},
            timeout=20,
        )
        data = res.json()
        if "error" in data:
            return None, data["error"].get("message", "Erreur API Anthropic")
        parsed = parse_jsonish(data["content"][0]["text"])
        if not parsed or not isinstance(parsed.get("items"), list):
            return None, "Réponse IA non exploitable. Réessaie."
        return parsed, None
    except Exception as exc:
        return None, f"Erreur IA : {exc}"

# ─────────────────────────────────────────────────────────────────────────────
# SUGGESTIONS
# ─────────────────────────────────────────────────────────────────────────────
def food_category(name: str) -> str:
    n = name.lower()
    if any(k in n for k in ["poulet", "thon", "skyr", "oeuf", "œuf", "saumon", "fromage blanc", "steak"]):
        return "prot"
    if any(k in n for k in ["riz", "pâtes", "patate", "avoine", "pain", "lentille", "haricot"]):
        return "gluc"
    if any(k in n for k in ["brocoli", "épinard", "chou", "haricot vert", "courgette", "carotte"]):
        return "veg"
    if any(k in n for k in ["huile", "beurre", "amande", "noix", "avocat"]):
        return "fat"
    return "other"


def build_suggestions(foods: Dict[str, Dict[str, Any]], settings: Dict[str, Any], totals: Dict[str, Any]) -> List[Dict[str, Any]]:
    kcal_gap = max(0, settings["objectif_kcal"] - totals["kcal"])
    prot_gap = max(0, settings["objectif_prot"] - totals["proteines"])
    if kcal_gap < 60:
        return []
    foods_items = [(n, d) for n, d in foods.items() if safe_float(d.get("kcal")) > 0]
    prots = [(n, d) for n, d in foods_items if food_category(n) == "prot"] or foods_items[:4]
    glucs = [(n, d) for n, d in foods_items if food_category(n) == "gluc"] or foods_items[:4]
    vegs = [(n, d) for n, d in foods_items if food_category(n) == "veg"]
    fats = [(n, d) for n, d in foods_items if food_category(n) == "fat"]
    suggestions = []
    for p_name, p_data in prots[:6]:
        p_grams = min(260, max(80, round((prot_gap or 35) * 100 / max(safe_float(p_data.get("proteines")), 1))))
        p_m = calc_macros(p_data, p_grams)
        remaining = kcal_gap - p_m["kcal"]
        for g_name, g_data in glucs[:6]:
            if g_name == p_name:
                continue
            g_grams = max(40, round(max(remaining, 80) * 0.75 / safe_float(g_data.get("kcal")) * 100))
            if g_grams > 450:
                continue
            g_m = calc_macros(g_data, g_grams)
            combo = [{"name": p_name, "grams": p_grams, **p_m}, {"name": g_name, "grams": g_grams, **g_m}]
            current_kcal = p_m["kcal"] + g_m["kcal"]
            if vegs and current_kcal < kcal_gap * 0.90:
                v_name, v_data = vegs[0]
                v_grams = min(300, max(80, round((kcal_gap - current_kcal) / safe_float(v_data.get("kcal")) * 100)))
                v_m = calc_macros(v_data, v_grams)
                combo.append({"name": v_name, "grams": v_grams, **v_m})
                current_kcal += v_m["kcal"]
            if fats and current_kcal < kcal_gap * 0.85:
                f_name, f_data = fats[0]
                f_grams = min(20, max(5, round((kcal_gap - current_kcal) / safe_float(f_data.get("kcal")) * 100)))
                f_m = calc_macros(f_data, f_grams)
                combo.append({"name": f_name, "grams": f_grams, **f_m})
                current_kcal += f_m["kcal"]
            totals_combo = sum_macros(combo)
            score = abs(totals_combo["kcal"] - kcal_gap) + max(0, prot_gap - totals_combo["proteines"]) * 6
            suggestions.append({"items": combo, "totals": totals_combo, "score": score})
    suggestions.sort(key=lambda s: s["score"])
    return suggestions[:5]

# ─────────────────────────────────────────────────────────────────────────────
# UI PARTS
# ─────────────────────────────────────────────────────────────────────────────
def render_card_entry(entry: Dict[str, Any]) -> None:
    meal = f"<span class='small-chip'>{entry.get('meal_name')}</span>" if entry.get("meal_name") else ""
    st.markdown(
        f"""
        <div class="food-card">
          <div class="food-title">
            <span class="food-name">{entry.get('food_name','?')} <span class="muted">({entry.get('grams',0):g}g)</span> {meal}</span>
            <span class="food-kcal">{safe_float(entry.get('kcal')):.0f} kcal</span>
          </div>
          <div class="muted">P {safe_float(entry.get('proteines')):.1f}g · G {safe_float(entry.get('glucides')):.1f}g · L {safe_float(entry.get('lipides')):.1f}g · Fib {safe_float(entry.get('fibres')):.1f}g</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard(today: str, totals: Dict[str, Any], settings: Dict[str, Any]) -> None:
    st.markdown("# 🔥 MACRO TRACKER")
    st.caption(today)
    st.markdown(
        f"""
        <div class="hero">
          <div class="hero-kcal">{totals['kcal']:.0f}</div>
          <div class="hero-label">calories</div>
          <div class="macro-row">
            <div class="macro-pill"><div class="macro-val">{totals['proteines']:.1f}g</div><div class="macro-label">💪 Prot</div></div>
            <div class="macro-pill"><div class="macro-val">{totals['glucides']:.1f}g</div><div class="macro-label">⚡ Gluc</div></div>
            <div class="macro-pill"><div class="macro-val">{totals['lipides']:.1f}g</div><div class="macro-label">🥑 Lip</div></div>
            <div class="macro-pill"><div class="macro-val">{totals['fibres']:.1f}g</div><div class="macro-label">🌿 Fib</div></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        gauge_html("🔥 Calories", totals["kcal"], settings["objectif_kcal"], "kcal")
        + gauge_html("💪 Protéines", totals["proteines"], settings["objectif_prot"], "g")
        + gauge_html("⚡ Glucides", totals["glucides"], settings["objectif_gluc"], "g")
        + gauge_html("🥑 Lipides", totals["lipides"], settings["objectif_lip"], "g"),
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────────────────────────────────────
if not auth_gate():
    st.stop()

user_id = current_user_id()
ensure_user_defaults(user_id)
settings = load_settings(user_id)
foods = load_foods(user_id)
meals = load_meals(user_id)
today = today_key()
entries_today = [e for e in load_entries(user_id, today, today) if e.get("entry_date") == today]
totals = sum_macros(entries_today)

render_dashboard(today, totals, settings)

with st.sidebar:
    st.markdown("### ⚙️ État")
    if USE_SUPABASE and user_id != "demo-user":
        st.success("Sauvegarde Supabase active")
    else:
        st.info("Mode démo/local")
    st.caption("Les données sont séparées par utilisateur quand Supabase est configuré.")

tab_add, tab_meals, tab_foods, tab_history, tab_settings = st.tabs(["➕ Aliment", "🍽️ Repas", "📋 Base", "📊 Historique", "⚙️ Réglages"])

# ── ADD FOOD ─────────────────────────────────────────────────────────────────
with tab_add:
    kcal_gap = settings["objectif_kcal"] - totals["kcal"]
    prot_gap = settings["objectif_prot"] - totals["proteines"]
    if kcal_gap > 50:
        st.markdown(f"<div class='notice'>Il te manque environ <b>{kcal_gap:.0f} kcal</b> et <b>{max(0, prot_gap):.0f} g de protéines</b>.</div>", unsafe_allow_html=True)
        if st.button("🍽️ Proposer quoi manger"):
            st.session_state["show_suggestions"] = not st.session_state.get("show_suggestions", False)
        if st.session_state.get("show_suggestions"):
            st.markdown('<div class="section-title">Suggestions automatiques</div>', unsafe_allow_html=True)
            for i, sug in enumerate(build_suggestions(foods, settings, totals)):
                items_txt = "<br>".join([f"{it['name']} <span class='muted'>({it['grams']}g)</span>" for it in sug["items"]])
                st.markdown(f"<div class='food-card'>{items_txt}<div class='muted'>{sug['totals']['kcal']:.0f} kcal · P {sug['totals']['proteines']:.1f}g · G {sug['totals']['glucides']:.1f}g · L {sug['totals']['lipides']:.1f}g</div></div>", unsafe_allow_html=True)
                if st.button("Ajouter cette suggestion", key=f"add_sug_{i}"):
                    for it in sug["items"]:
                        add_entry(user_id, it["name"], it["grams"], {k: it[k] for k in MACRO_KEYS}, today, "Suggestion")
                    rerun()
            if st.button("✨ Suggestion Claude IA"):
                suggestion, err = generate_ai_suggestion(settings, totals, foods)
                if err:
                    st.warning(err)
                else:
                    st.session_state["ai_suggestion"] = suggestion
            if st.session_state.get("ai_suggestion"):
                s = st.session_state["ai_suggestion"]
                clean_items = []
                st.markdown(f"<div class='meal-card'><b>✨ {s.get('title','Suggestion IA')}</b><br><span class='muted'>{s.get('note','')}</span></div>", unsafe_allow_html=True)
                for i, it in enumerate(s.get("items", [])):
                    name = st.selectbox("Aliment IA", sorted(foods.keys()), index=sorted(foods.keys()).index(it.get("name")) if it.get("name") in foods else 0, key=f"ai_food_{i}")
                    grams = st.number_input(f"Grammes {i+1}", 1, 2000, int(it.get("grams", 100)), 5, key=f"ai_grams_{i}")
                    clean_items.append((name, grams))
                if st.button("Ajouter la suggestion IA au journal"):
                    for name, grams in clean_items:
                        add_entry(user_id, name, grams, calc_macros(foods[name], grams), today, "IA")
                    st.session_state.pop("ai_suggestion", None)
                    rerun()
    st.markdown('<div class="section-title">Ajouter un aliment</div>', unsafe_allow_html=True)
    if foods:
        selected = st.selectbox("Aliment", sorted(foods.keys()), label_visibility="collapsed")
        grams = st.number_input("Grammes", min_value=1, max_value=3000, value=100, step=5)
        preview = calc_macros(foods[selected], grams)
        render_card_entry({"food_name": selected, "grams": grams, **preview})
        if st.button("➕ Ajouter au journal"):
            add_entry(user_id, selected, grams, preview, today)
            rerun()
    pinned = {n: m for n, m in meals.items() if m.get("pinned")}
    if pinned:
        st.markdown('<div class="section-title">⭐ Repas rapides</div>', unsafe_allow_html=True)
        for name, meal in pinned.items():
            preview_entries = [calc_macros(foods[it["food"]], it["grams"]) for it in meal.get("items", []) if it.get("food") in foods]
            mt = sum_macros(preview_entries)
            st.markdown(f"<div class='meal-card'><b>⭐ {name}</b><br><span class='muted'>{mt['kcal']:.0f} kcal · P {mt['proteines']:.1f}g · G {mt['glucides']:.1f}g · L {mt['lipides']:.1f}g</span></div>", unsafe_allow_html=True)
            if st.button(f"Ajouter {name}", key=f"quick_{name}"):
                for it in meal.get("items", []):
                    if it.get("food") in foods:
                        add_entry(user_id, it["food"], it["grams"], calc_macros(foods[it["food"]], it["grams"]), today, name)
                rerun()
    if entries_today:
        st.markdown('<div class="section-title">Journal du jour</div>', unsafe_allow_html=True)
        for e in entries_today:
            col1, col2 = st.columns([5, 1])
            with col1:
                render_card_entry(e)
            with col2:
                if st.button("✕", key=f"del_entry_{e.get('id')}"):
                    delete_entry(user_id, e.get("id"))
                    rerun()
        if st.button("🗑️ Effacer le journal du jour"):
            clear_day(user_id, today)
            rerun()

# ── MEALS ────────────────────────────────────────────────────────────────────
with tab_meals:
    sub = st.radio("", ["Utiliser", "Créer", "Gérer"], horizontal=True, label_visibility="collapsed")
    if sub == "Utiliser":
        st.markdown('<div class="section-title">Ajouter un repas</div>', unsafe_allow_html=True)
        if not meals:
            st.info("Aucun repas sauvegardé.")
        else:
            meal_name = st.selectbox("Repas", list(meals.keys()), label_visibility="collapsed")
            meal = meals[meal_name]
            temp_items = []
            for it in meal.get("items", []):
                if it.get("food") not in foods:
                    st.warning(f"{it.get('food')} n'est plus dans ta base.")
                    continue
                grams = st.number_input(it["food"], min_value=0, max_value=3000, value=int(it.get("grams", 100)), step=5, key=f"usemeal_{meal_name}_{it['food']}")
                if grams > 0:
                    temp_items.append({"food": it["food"], "grams": grams})
            mt = sum_macros([calc_macros(foods[it["food"]], it["grams"]) for it in temp_items])
            st.markdown(f"<div class='meal-card'><b>{meal_name}</b><br><span class='muted'>{mt['kcal']:.0f} kcal · P {mt['proteines']:.1f}g · G {mt['glucides']:.1f}g · L {mt['lipides']:.1f}g</span></div>", unsafe_allow_html=True)
            if st.button("➕ Ajouter ce repas"):
                for it in temp_items:
                    add_entry(user_id, it["food"], it["grams"], calc_macros(foods[it["food"]], it["grams"]), today, meal_name)
                rerun()
    elif sub == "Créer":
        st.markdown('<div class="section-title">Nouveau repas</div>', unsafe_allow_html=True)
        name = st.text_input("Nom du repas", placeholder="ex : Petit-déj classique")
        chosen = st.multiselect("Aliments", sorted(foods.keys()))
        items = []
        for f in chosen:
            grams = st.number_input(f"{f} (g)", min_value=0, max_value=3000, value=100, step=5, key=f"newmeal_{f}")
            if grams > 0:
                items.append({"food": f, "grams": grams})
        if items:
            mt = sum_macros([calc_macros(foods[it["food"]], it["grams"]) for it in items])
            st.markdown(f"<div class='meal-card'><b>{name or 'Nouveau repas'}</b><br><span class='muted'>{mt['kcal']:.0f} kcal · P {mt['proteines']:.1f}g · G {mt['glucides']:.1f}g · L {mt['lipides']:.1f}g</span></div>", unsafe_allow_html=True)
        pinned = st.checkbox("Épingler en repas rapide")
        if st.button("💾 Sauvegarder le repas"):
            if not name.strip():
                st.error("Donne un nom au repas.")
            elif not items:
                st.error("Ajoute au moins un aliment.")
            else:
                save_meal(user_id, name, items, pinned)
                rerun()
    else:
        st.markdown('<div class="section-title">Mes repas</div>', unsafe_allow_html=True)
        if not meals:
            st.info("Aucun repas.")
        for name, meal in meals.items():
            cols = st.columns([4, 1, 1])
            with cols[0]:
                items_txt = ", ".join([f"{it['food']} ({it['grams']}g)" for it in meal.get("items", [])])
                st.markdown(f"<div class='meal-card'><b>{'⭐ ' if meal.get('pinned') else ''}{name}</b><br><span class='muted'>{items_txt}</span></div>", unsafe_allow_html=True)
            with cols[1]:
                if st.button("★" if meal.get("pinned") else "☆", key=f"pin_{name}"):
                    toggle_pin_meal(user_id, meal, name)
                    rerun()
            with cols[2]:
                if st.button("✕", key=f"meal_del_{name}"):
                    delete_meal(user_id, meal, name)
                    rerun()

# ── FOOD BASE ────────────────────────────────────────────────────────────────
with tab_foods:
    sub = st.radio("", ["Voir", "Rechercher OFF", "Ajout manuel"], horizontal=True, label_visibility="collapsed")
    if sub == "Voir":
        flt = st.text_input("Filtrer", placeholder="riz, poulet...", label_visibility="collapsed")
        for name, food in sorted(foods.items()):
            if flt.lower() not in name.lower():
                continue
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"<div class='food-card'><div class='food-title'><span class='food-name'>{name}</span><span class='food-kcal'>{food['kcal']:.0f} kcal</span></div><div class='muted'>P {food['proteines']}g · G {food['glucides']}g · L {food['lipides']}g · Fib {food.get('fibres',0)}g · {food.get('source','')}</div></div>", unsafe_allow_html=True)
            with col2:
                if st.button("✕", key=f"delete_food_{name}"):
                    delete_food(user_id, name)
                    rerun()
    elif sub == "Rechercher OFF":
        q = st.text_input("Aliment", placeholder="ex : avocat, saumon, yaourt...")
        if st.button("🔎 Rechercher") and q.strip():
            results, err = search_openfoodfacts(q)
            if err:
                st.error(err)
            st.session_state["off_results"] = results
        for i, r in enumerate(st.session_state.get("off_results", [])):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"<div class='food-card'><div class='food-title'><span class='food-name'>{r['name']}</span><span class='food-kcal'>{r['kcal']:.0f} kcal</span></div><div class='muted'>P {r['proteines']}g · G {r['glucides']}g · L {r['lipides']}g · Fib {r['fibres']}g</div></div>", unsafe_allow_html=True)
            with col2:
                if st.button("＋", key=f"off_add_{i}"):
                    upsert_food(user_id, r["name"], {k: r[k] for k in MACRO_KEYS} | {"source": r["source"]})
                    rerun()
    else:
        name = st.text_input("Nom de l'aliment")
        c1, c2 = st.columns(2)
        kcal = c1.number_input("kcal / 100g", min_value=0.0, value=0.0)
        prot = c2.number_input("Protéines / 100g", min_value=0.0, value=0.0)
        c3, c4 = st.columns(2)
        gluc = c3.number_input("Glucides / 100g", min_value=0.0, value=0.0)
        lip = c4.number_input("Lipides / 100g", min_value=0.0, value=0.0)
        fibres = st.number_input("Fibres / 100g", min_value=0.0, value=0.0)
        if st.button("💾 Sauvegarder l'aliment"):
            if not name.strip():
                st.error("Entre un nom.")
            else:
                upsert_food(user_id, name, {"kcal": kcal, "proteines": prot, "glucides": gluc, "lipides": lip, "fibres": fibres, "source": "Manuel"})
                rerun()

# ── HISTORY ──────────────────────────────────────────────────────────────────
with tab_history:
    st.markdown('<div class="section-title">Historique</div>', unsafe_allow_html=True)
    end_date = date.today()
    start_date = end_date - timedelta(days=27)
    all_entries = load_entries(user_id, str(start_date), str(end_date))
    by_day: Dict[str, List[Dict[str, Any]]] = {}
    for e in all_entries:
        by_day.setdefault(e.get("entry_date"), []).append(e)
    if not by_day:
        st.info("Aucun historique pour le moment.")
    else:
        # weekly selector
        mondays = sorted({datetime.strptime(d, "%Y-%m-%d").date() - timedelta(days=datetime.strptime(d, "%Y-%m-%d").date().weekday()) for d in by_day.keys()}, reverse=True)
        labels = [f"Semaine du {m.strftime('%d/%m/%Y')}" for m in mondays]
        chosen = st.selectbox("Semaine", labels, label_visibility="collapsed")
        monday = mondays[labels.index(chosen)]
        days = [monday + timedelta(days=i) for i in range(7)]
        vals = []
        for d in days:
            vals.append(sum_macros(by_day.get(str(d), [])))
        max_kcal = max([v["kcal"] for v in vals] + [settings["objectif_kcal"]]) or 1
        bars = '<div style="display:flex;align-items:flex-end;height:150px;gap:6px;margin:12px 0">'
        for d, v in zip(days, vals):
            h = max(3, v["kcal"] / max_kcal * 120)
            color = "#e8ff5a" if str(d) == today else ("#ff5a5a" if v["kcal"] > settings["objectif_kcal"] * 1.05 else "#5a8fff")
            bars += f"<div style='flex:1;text-align:center'><div style='font-size:.6rem;color:#777'>{v['kcal']:.0f}</div><div style='height:{h}px;background:{color};border-radius:6px 6px 0 0'></div><div style='font-size:.6rem;color:#666'>{d.strftime('%a')[:2]}</div></div>"
        bars += "</div>"
        st.markdown(bars, unsafe_allow_html=True)
        logged = [v for v in vals if v["kcal"] > 0]
        avg = sum_macros(logged) if logged else {k: 0 for k in MACRO_KEYS}
        if logged:
            avg = {k: round(v / len(logged), 1) for k, v in avg.items()}
        st.markdown(f"<div class='block'><b>Moyenne jours trackés</b><br><span class='muted'>{avg['kcal']:.0f} kcal · P {avg['proteines']:.1f}g · G {avg['glucides']:.1f}g · L {avg['lipides']:.1f}g · {len(logged)}/7 jours</span></div>", unsafe_allow_html=True)
        with st.expander("Détail par jour"):
            for d in days:
                day_entries = by_day.get(str(d), [])
                st.markdown(f"**{d.strftime('%d/%m/%Y')}**")
                if not day_entries:
                    st.caption("Aucune entrée")
                for e in day_entries:
                    render_card_entry(e)

# ── SETTINGS ─────────────────────────────────────────────────────────────────
with tab_settings:
    sub = st.radio("", ["🧮 Calculateur", "✏️ Manuel", "🔐 Données"], horizontal=True, label_visibility="collapsed")
    if sub == "🧮 Calculateur":
        st.markdown('<div class="section-title">Calculateur objectifs</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        sex = c1.selectbox("Sexe", ["Homme", "Femme"])
        age = c2.number_input("Âge", 15, 80, 25)
        c3, c4 = st.columns(2)
        weight = c3.number_input("Poids (kg)", 30.0, 250.0, 75.0, 0.5)
        height = c4.number_input("Taille (cm)", 140, 230, 175)
        activity = st.selectbox("Activité", ["Sédentaire", "Légère", "Modérée", "Intense", "Très intense"])
        objective = st.selectbox("Objectif", ["Maintien", "Sèche", "Prise de masse", "Recomposition"])
        if st.button("🧮 Calculer"):
            if sex == "Homme":
                bmr = 10 * weight + 6.25 * height - 5 * age + 5
            else:
                bmr = 10 * weight + 6.25 * height - 5 * age - 161
            mult = {"Sédentaire": 1.25, "Légère": 1.4, "Modérée": 1.55, "Intense": 1.72, "Très intense": 1.9}[activity]
            tdee = round(bmr * mult)
            if objective == "Maintien":
                kcal = tdee
                prot_ratio, lip_ratio = 1.6, 1.0
            elif objective == "Sèche":
                kcal = tdee - min(500, round(tdee * 0.2))
                prot_ratio, lip_ratio = 2.0, 0.8
            elif objective == "Prise de masse":
                kcal = tdee + round(tdee * 0.1)
                prot_ratio, lip_ratio = 1.8, 1.0
            else:
                kcal = tdee - 200
                prot_ratio, lip_ratio = 2.2, 0.9
            prot = round(weight * prot_ratio)
            lip = round(weight * lip_ratio)
            gluc = max(50, round((kcal - prot * 4 - lip * 9) / 4))
            kcal_real = prot * 4 + gluc * 4 + lip * 9
            st.session_state["calc_result"] = {"objectif_kcal": kcal_real, "objectif_prot": prot, "objectif_gluc": gluc, "objectif_lip": lip, "bmr": round(bmr), "tdee": tdee, "prot_ratio": prot_ratio}
        if st.session_state.get("calc_result"):
            r = st.session_state["calc_result"]
            st.markdown(f"<div class='block'><b>Résultat</b><br><span class='muted'>BMR {r['bmr']} kcal · TDEE {r['tdee']} kcal · protéines {r['prot_ratio']}g/kg</span><div class='hero-kcal' style='font-size:2.4rem'>{r['objectif_kcal']:.0f}</div><span class='muted'>P {r['objectif_prot']}g · G {r['objectif_gluc']}g · L {r['objectif_lip']}g</span></div>", unsafe_allow_html=True)
            if st.button("✅ Appliquer ces objectifs"):
                save_settings(user_id, {k: r[k] for k in DEFAULT_SETTINGS})
                st.session_state.pop("calc_result", None)
                rerun()
    elif sub == "✏️ Manuel":
        c1, c2 = st.columns(2)
        kcal = c1.number_input("Calories", value=int(settings["objectif_kcal"]), step=50)
        prot = c2.number_input("Protéines", value=int(settings["objectif_prot"]), step=5)
        c3, c4 = st.columns(2)
        gluc = c3.number_input("Glucides", value=int(settings["objectif_gluc"]), step=10)
        lip = c4.number_input("Lipides", value=int(settings["objectif_lip"]), step=5)
        if st.button("💾 Sauvegarder"):
            save_settings(user_id, {"objectif_kcal": kcal, "objectif_prot": prot, "objectif_gluc": gluc, "objectif_lip": lip})
            rerun()
    else:
        st.markdown('<div class="section-title">Confidentialité et export</div>', unsafe_allow_html=True)
        st.markdown("<div class='notice'>En mode Supabase, chaque entrée est liée à ton user_id. En mode démo/local, rien n'est durable.</div>", unsafe_allow_html=True)
        export = {"settings": settings, "foods": foods, "entries": load_entries(user_id), "meals": meals}
        st.download_button("⬇️ Exporter mes données JSON", json.dumps(export, ensure_ascii=False, indent=2), file_name="macro_tracker_export.json", mime="application/json")
        if st.button("Réinitialiser mes données du jour"):
            clear_day(user_id, today)
            rerun()
