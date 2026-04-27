import streamlit as st
import json
import os
from datetime import date, timedelta, datetime
import requests

st.set_page_config(page_title="Macro Tracker", page_icon="🔥", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; background-color: #0f0f0f; color: #f0f0f0; }
h1, h2, h3 { font-family: 'Space Mono', monospace; }
.stApp { background: #0f0f0f; }
.hero-block { background:#111; border:1px solid #222; border-radius:16px; padding:24px 16px 16px; margin:12px 0 4px; text-align:center; }
.hero-kcal { font-family:'Space Mono',monospace; font-size:3.8rem; font-weight:700; color:#e8ff5a; line-height:1; letter-spacing:-2px; }
.hero-kcal-label { font-size:0.7rem; color:#555; text-transform:uppercase; letter-spacing:3px; margin-bottom:16px; }
.macro-row { display:flex; justify-content:space-around; margin-top:14px; border-top:1px solid #1e1e1e; padding-top:14px; }
.macro-pill { text-align:center; flex:1; }
.macro-pill-val { font-family:'Space Mono',monospace; font-size:1.35rem; font-weight:700; color:#f0f0f0; }
.macro-pill-label { font-size:0.65rem; color:#555; text-transform:uppercase; letter-spacing:1.5px; }
.macro-pill-sep { width:1px; background:#1e1e1e; }
.gauge-wrap { margin:10px 0; }
.gauge-bar-bg { background:#1a1a1a; border-radius:999px; height:16px; width:100%; overflow:hidden; border:1px solid #2a2a2a; }
.gauge-bar-fill { height:100%; border-radius:999px; }
.gauge-label { display:flex; justify-content:space-between; font-size:0.72rem; color:#666; margin-bottom:3px; }
.color-ok   { background:linear-gradient(90deg,#e8ff5a,#a8cc00); }
.color-over { background:linear-gradient(90deg,#ff5a5a,#cc0000); }
.color-low  { background:linear-gradient(90deg,#5a8fff,#0055cc); }
.food-item { background:#161616; border:1px solid #252525; border-radius:8px; padding:10px 14px; margin:4px 0; display:flex; justify-content:space-between; align-items:center; font-size:0.85rem; }
.food-kcal { color:#e8ff5a; font-family:'Space Mono',monospace; font-weight:700; }
.meal-card { background:#141414; border:1px solid #2a2a2a; border-radius:12px; padding:14px; margin:8px 0; }
.meal-name { font-family:'Space Mono',monospace; font-size:0.9rem; color:#e8ff5a; font-weight:700; }
.meal-meta { font-size:0.72rem; color:#555; margin-top:4px; }
.stButton > button { background:#e8ff5a !important; color:#0f0f0f !important; border:none !important; border-radius:8px !important; font-family:'Space Mono',monospace !important; font-weight:700 !important; font-size:0.85rem !important; padding:10px 20px !important; width:100% !important; }
.stButton > button:hover { background:#d4eb3a !important; }
.stSelectbox > div > div, .stNumberInput > div > div > input, .stTextInput > div > div > input { background:#1a1a1a !important; border:1px solid #333 !important; color:#f0f0f0 !important; border-radius:8px !important; }
.stMultiSelect > div { background:#1a1a1a !important; border:1px solid #333 !important; border-radius:8px !important; }
.section-title { font-family:'Space Mono',monospace; font-size:0.65rem; letter-spacing:2px; text-transform:uppercase; color:#444; margin:22px 0 8px 0; border-bottom:1px solid #1a1a1a; padding-bottom:6px; }
div[data-testid="stExpander"] { background:#1a1a1a; border:1px solid #2a2a2a; border-radius:12px; }
.tag-src { font-size:0.65rem; color:#444; margin-left:6px; }
.notice { background:#141414; border:1px solid #2a2a2a; border-radius:10px; padding:10px 12px; color:#777; font-size:0.78rem; margin:8px 0; }
</style>
""", unsafe_allow_html=True)

# ── FILES ────────────────────────────────────────────────────────────────────
DB_FILE       = "foods_db.json"
LOG_FILE      = "daily_log.json"
SETTINGS_FILE = "settings.json"
MEALS_FILE    = "meals.json"

DEFAULT_FOODS = {
    "Riz basmati cru":            {"kcal":356,"proteines":7.6,"glucides":78.0,"lipides":0.9,"fibres":1.0,"source":"Ciqual"},
    "Lentilles vertes crues":     {"kcal":311,"proteines":24.0,"glucides":45.0,"lipides":1.4,"fibres":11.4,"source":"Ciqual"},
    "Filet de poulet cru":        {"kcal":110,"proteines":23.0,"glucides":0.0,"lipides":1.5,"fibres":0.0,"source":"Ciqual"},
    "Pâtes crues":                {"kcal":358,"proteines":12.5,"glucides":70.2,"lipides":1.8,"fibres":3.0,"source":"Ciqual"},
    "Thon en conserve au naturel":{"kcal":116,"proteines":25.5,"glucides":0.0,"lipides":1.0,"fibres":0.0,"source":"Ciqual"},
    "Brocoli surgelé":            {"kcal":35,"proteines":2.8,"glucides":4.0,"lipides":0.4,"fibres":2.6,"source":"Ciqual"},
    "Épinards surgelés":          {"kcal":20,"proteines":2.4,"glucides":0.8,"lipides":0.4,"fibres":2.1,"source":"Ciqual"},
    "Chou-fleur surgelé":         {"kcal":25,"proteines":2.0,"glucides":3.0,"lipides":0.3,"fibres":1.8,"source":"Ciqual"},
    "Haricots verts surgelés":    {"kcal":31,"proteines":1.8,"glucides":4.7,"lipides":0.2,"fibres":3.4,"source":"Ciqual"},
}

def load_json(f, d):
    if os.path.exists(f):
        with open(f) as fp: return json.load(fp)
    return d

def save_json(f, data):
    with open(f, "w") as fp: json.dump(data, fp, ensure_ascii=False, indent=2)

def today_key(): return str(date.today())

def calc_macros(food, grams):
    r = grams / 100
    return {"kcal":round(food["kcal"]*r,1),"proteines":round(food["proteines"]*r,1),
            "glucides":round(food["glucides"]*r,1),"lipides":round(food["lipides"]*r,1),
            "fibres":round(food.get("fibres",0)*r,1)}

def sum_macros(entries):
    t = {"kcal":0,"proteines":0,"glucides":0,"lipides":0,"fibres":0}
    for e in entries:
        for k in t: t[k] += e.get(k, 0)
    return {k: round(v,1) for k,v in t.items()}

def gauge_html(label, value, target, unit="g"):
    if not target: return ""
    pct = min(value / target * 100, 100)
    cls = "color-ok" if 85 <= pct <= 105 else ("color-over" if pct > 105 else "color-low")
    return f"""<div class="gauge-wrap">
      <div class="gauge-label"><span>{label}</span><span>{value:.0f} / {target} {unit}</span></div>
      <div class="gauge-bar-bg"><div class="gauge-bar-fill {cls}" style="width:{pct:.1f}%"></div></div>
    </div>"""

def search_openfoodfacts(query):
    """Recherche stable Open Food Facts, sans message jaune et avec conversion kJ -> kcal."""
    def _fetch(q, lang=None):
        headers = {"User-Agent": "MacroTracker/1.0 (contact: streamlit-app)"}
        params = {
            "search_terms": q,
            "page_size": 10,
            "fields": "product_name,product_name_fr,product_name_en,nutriments",
        }
        if lang:
            params["lc"] = lang
        try:
            r = requests.get("https://world.openfoodfacts.org/api/v2/search", params=params, headers=headers, timeout=10)
            if r.status_code != 200:
                return []
            results = []
            for p in r.json().get("products", []):
                n = p.get("nutriments", {}) or {}
                name = p.get("product_name_fr") or p.get("product_name") or p.get("product_name_en") or ""
                kcal = n.get("energy-kcal_100g")
                if kcal in (None, "") and n.get("energy_100g") not in (None, ""):
                    kcal = float(n.get("energy_100g", 0)) / 4.184
                if not name or kcal in (None, "", 0):
                    continue
                results.append({
                    "name": name.strip(),
                    "kcal": round(float(kcal), 1),
                    "proteines": round(float(n.get("proteins_100g") or 0), 1),
                    "glucides": round(float(n.get("carbohydrates_100g") or 0), 1),
                    "lipides": round(float(n.get("fat_100g") or 0), 1),
                    "fibres": round(float(n.get("fiber_100g") or 0), 1),
                    "source": "Open Food Facts",
                })
            return results
        except Exception:
            return []

    results = _fetch(query, lang="fr") or _fetch(query)
    seen, deduped = set(), []
    for r in results:
        key = r["name"].lower()
        if key not in seen:
            seen.add(key)
            deduped.append(r)
    return deduped[:8]


# ── SMART FOOD SUGGESTIONS ───────────────────────────────────────────────────
def _norm(s):
    return (s or "").lower().replace("é", "e").replace("è", "e").replace("ê", "e").replace("à", "a").replace("ù", "u").replace("ï", "i").replace("î", "i")

def food_category(name, data):
    """Catégorise un aliment avec mots-clés + macros pour générer des vrais plats."""
    n = _norm(name)
    kcal = float(data.get("kcal", 0) or 0)
    p = float(data.get("proteines", 0) or 0)
    c = float(data.get("glucides", 0) or 0)
    f = float(data.get("lipides", 0) or 0)
    fiber = float(data.get("fibres", 0) or 0)
    protein_kw = ["poulet", "thon", "dinde", "boeuf", "steak", "saumon", "truite", "oeuf", "skyr", "fromage blanc", "tofu", "tempeh", "proteine"]
    carb_kw = ["riz", "pates", "pâte", "semoule", "quinoa", "avoine", "flocon", "pain", "patate", "pomme de terre", "lentille", "haricot rouge", "pois chiche", "wrap"]
    veg_kw = ["brocoli", "epinard", "chou", "haricot vert", "courgette", "carotte", "salade", "tomate", "concombre", "legume", "légume"]
    fat_kw = ["huile", "olive", "avocat", "amande", "noix", "beurre", "cacahuete", "fromage", "saumon", "oeuf"]
    if any(k in n for k in veg_kw) or (kcal <= 90 and fiber >= 1.5 and c <= 12):
        return "veg"
    if any(k in n for k in fat_kw) or f >= 10:
        return "fat"
    if any(k in n for k in protein_kw) or (p >= 15 and p * 4 >= kcal * 0.35):
        return "protein"
    if any(k in n for k in carb_kw) or c >= 20:
        return "carb"
    return "other"

def portion_grid(name, cat):
    n = _norm(name)
    if cat == "protein":
        if "oeuf" in n:
            return [50, 100, 150, 200]
        if "thon" in n or "skyr" in n or "fromage blanc" in n:
            return [100, 150, 200, 250, 300]
        return [100, 130, 160, 200, 240, 280, 320]
    if cat == "carb":
        if "cru" in n or "crues" in n or "flocon" in n or "avoine" in n:
            return [40, 60, 80, 100, 120, 150]
        return [120, 160, 200, 250, 300, 350]
    if cat == "veg":
        return [100, 150, 200, 250, 300, 400]
    if cat == "fat":
        if "huile" in n or "beurre" in n:
            return [5, 10, 15, 20, 25]
        return [20, 30, 50, 80, 100, 150]
    return [50, 100, 150, 200]

def meal_title(items, kcal_gap):
    names = " ".join(_norm(i["nom"]) for i in items)
    cats = {i.get("cat") for i in items}
    if "riz" in names and any(k in names for k in ["poulet", "thon", "saumon", "dinde"]):
        return "Bol riz protéiné"
    if "pates" in names or "pâte" in names:
        return "Assiette pâtes équilibrée"
    if "lentille" in names:
        return "Bowl lentilles complet"
    if "protein" in cats and "carb" in cats and "veg" in cats:
        return "Assiette complète"
    if kcal_gap < 300:
        return "Collation intelligente"
    if "protein" in cats and "veg" in cats:
        return "Repas léger protéiné"
    return "Repas ajusté à tes macros"

def reason_for_combo(combo, gaps):
    bits = []
    if gaps["prot"] > 15 and combo["proteines"] >= min(gaps["prot"] * 0.7, gaps["prot"] + 10):
        bits.append("corrige surtout ton manque de protéines")
    if gaps["gluc"] > 30 and combo["glucides"] >= min(gaps["gluc"] * 0.55, gaps["gluc"] + 20):
        bits.append("remonte bien les glucides")
    if gaps["lip"] > 10 and combo["lipides"] >= min(gaps["lip"] * 0.45, gaps["lip"] + 10):
        bits.append("ajoute un peu de lipides utiles")
    if abs(combo["kcal"] - gaps["kcal"]) <= max(80, gaps["kcal"] * 0.12):
        bits.append("tombe proche des calories restantes")
    if not bits:
        bits.append("reste cohérent avec tes objectifs du jour")
    return "Ce plat " + ", ".join(bits[:2]) + "."

def generate_smart_suggestions(foods_db, totals, settings, style="Auto"):
    kcal_gap = max(0, float(settings["objectif_kcal"] - totals["kcal"]))
    gaps = {
        "kcal": kcal_gap,
        "prot": max(0, float(settings["objectif_prot"] - totals["proteines"])),
        "gluc": max(0, float(settings["objectif_gluc"] - totals["glucides"])),
        "lip":  max(0, float(settings["objectif_lip"] - totals["lipides"])),
    }
    if kcal_gap <= 40:
        return []
    categorized = {"protein": [], "carb": [], "veg": [], "fat": [], "other": []}
    for name, data in foods_db.items():
        if float(data.get("kcal", 0) or 0) <= 0:
            continue
        cat = food_category(name, data)
        categorized[cat].append((name, data, cat))
    categorized["protein"].sort(key=lambda x: (-(x[1].get("proteines", 0) / max(x[1].get("kcal", 1), 1)), x[0]))
    categorized["carb"].sort(key=lambda x: (-(x[1].get("glucides", 0)), x[0]))
    categorized["veg"].sort(key=lambda x: (-(x[1].get("fibres", 0)), x[0]))
    categorized["fat"].sort(key=lambda x: (-(x[1].get("lipides", 0)), x[0]))
    proteins = categorized["protein"][:7] or categorized["other"][:4]
    carbs = categorized["carb"][:7] or categorized["other"][:4]
    vegs = categorized["veg"][:6]
    fats = categorized["fat"][:5]
    templates = []
    if kcal_gap < 300:
        templates += [["protein"], ["carb"], ["protein", "carb"], ["protein", "fat"]]
    elif style == "Riche en protéines" or gaps["prot"] > 25:
        templates += [["protein", "carb", "veg"], ["protein", "veg", "fat"], ["protein", "carb"], ["protein", "carb", "veg", "fat"]]
    elif style == "Léger / sèche":
        templates += [["protein", "veg"], ["protein", "veg", "fat"], ["protein", "carb", "veg"]]
    elif style == "Rapide":
        templates += [["protein", "carb"], ["protein"], ["carb", "fat"], ["protein", "carb", "fat"]]
    else:
        templates += [["protein", "carb", "veg"], ["protein", "carb"], ["protein", "carb", "veg", "fat"], ["carb", "protein"], ["protein", "veg", "fat"]]
    pools = {"protein": proteins, "carb": carbs, "veg": vegs, "fat": fats, "other": categorized["other"][:5]}
    suggestions = []
    seen_signatures = set()
    from itertools import product
    for tpl in templates:
        if any(not pools.get(cat) for cat in tpl):
            continue
        for foods_choice in product(*[pools[cat] for cat in tpl]):
            names = [f[0] for f in foods_choice]
            if len(set(names)) < len(names):
                continue
            grids = [portion_grid(name, cat) for name, _, cat in foods_choice]
            for grams_choice in product(*grids):
                entries = []
                total = {"kcal": 0, "proteines": 0, "glucides": 0, "lipides": 0, "fibres": 0}
                for (name, data, cat), grams in zip(foods_choice, grams_choice):
                    m = calc_macros(data, grams)
                    for k in total:
                        total[k] += m.get(k, 0)
                    entries.append({"nom": name, "grammes": grams, "cat": cat, **m})
                total = {k: round(v, 1) for k, v in total.items()}
                if total["kcal"] < kcal_gap * 0.55 and kcal_gap > 300:
                    continue
                if total["kcal"] > kcal_gap * 1.25 + 80:
                    continue
                kcal_diff = abs(total["kcal"] - kcal_gap)
                prot_after_gap = max(0, gaps["prot"] - total["proteines"])
                gluc_after_gap = max(0, gaps["gluc"] - total["glucides"])
                lip_after_gap = max(0, gaps["lip"] - total["lipides"])
                over_gluc = max(0, total["glucides"] - gaps["gluc"] - 25) if gaps["gluc"] > 0 else max(0, total["glucides"] - 90)
                over_lip = max(0, total["lipides"] - gaps["lip"] - 10) if gaps["lip"] > 0 else max(0, total["lipides"] - 25)
                portion_penalty = sum(max(0, it["grammes"] - 350) * 0.4 for it in entries)
                variety_bonus = -25 if len({it["cat"] for it in entries}) >= 3 else 0
                veg_bonus = -15 if any(it["cat"] == "veg" for it in entries) and kcal_gap > 350 else 0
                score = (kcal_diff * 1.15 + prot_after_gap * (10 if gaps["prot"] > 15 else 4) + gluc_after_gap * (2.0 if gaps["gluc"] > 30 else 0.8) + lip_after_gap * (3.0 if gaps["lip"] > 8 else 1.0) + over_gluc * 1.6 + over_lip * 4.0 + portion_penalty + variety_bonus + veg_bonus)
                sig = tuple(sorted((e["nom"], e["grammes"]) for e in entries))
                if sig in seen_signatures:
                    continue
                seen_signatures.add(sig)
                combo = {"items": entries, **total, "score": round(score, 2)}
                combo["titre"] = meal_title(entries, kcal_gap)
                combo["raison"] = reason_for_combo(combo, gaps)
                combo["tag"] = "meilleur équilibre" if len(entries) >= 3 else ("rapide" if len(entries) <= 2 else "complet")
                suggestions.append(combo)
    suggestions.sort(key=lambda x: x["score"])
    final = []
    main_seen = set()
    for s in suggestions:
        main = tuple(sorted(i["nom"] for i in s["items"][:3]))
        if main in main_seen:
            continue
        main_seen.add(main)
        final.append(s)
        if len(final) >= 5:
            break
    return final

# ── LOAD STATE ────────────────────────────────────────────────────────────────
foods_db  = load_json(DB_FILE, DEFAULT_FOODS)
if not os.path.exists(DB_FILE): save_json(DB_FILE, foods_db)
daily_log = load_json(LOG_FILE, {})
meals_db  = load_json(MEALS_FILE, {})

# ── SETTINGS : session_state comme seule source de vérité ───────────────────
# On N'utilise PAS de fichier — filesystem Streamlit Cloud est éphémère.
# Les objectifs survivent aux reruns via st.session_state.
_SS = st.session_state  # raccourci

if "_settings_init" not in _SS:
    _SS["objectif_kcal"] = 2000
    _SS["objectif_prot"] = 150
    _SS["objectif_gluc"] = 250
    _SS["objectif_lip"]  = 65
    _SS["_settings_init"] = True

# Classe proxy pour garder la syntaxe settings["x"] partout dans le code
class _SettingsProxy:
    def __getitem__(self, k):   return _SS[k]
    def __setitem__(self, k, v): _SS[k] = v
    def get(self, k, d=None):   return _SS.get(k, d)

settings = _SettingsProxy()

today = today_key()
if today not in daily_log: daily_log[today] = []
totaux = sum_macros(daily_log[today])

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("# 🔥 MACRO TRACKER")
st.markdown(f"<p style='color:#444;font-size:0.75rem;font-family:Space Mono,monospace;margin-top:-12px'>{today}</p>", unsafe_allow_html=True)

# ── HERO ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero-block">
  <div class="hero-kcal">{totaux['kcal']}</div>
  <div class="hero-kcal-label">calories</div>
  <div class="macro-row">
    <div class="macro-pill"><div class="macro-pill-val">{totaux['proteines']}g</div><div class="macro-pill-label">💪 Prot</div></div>
    <div class="macro-pill-sep"></div>
    <div class="macro-pill"><div class="macro-pill-val">{totaux['glucides']}g</div><div class="macro-pill-label">⚡ Gluc</div></div>
    <div class="macro-pill-sep"></div>
    <div class="macro-pill"><div class="macro-pill-val">{totaux['lipides']}g</div><div class="macro-pill-label">🥑 Lip</div></div>
    <div class="macro-pill-sep"></div>
    <div class="macro-pill"><div class="macro-pill-val">{totaux['fibres']}g</div><div class="macro-pill-label">🌿 Fib</div></div>
  </div>
</div>""", unsafe_allow_html=True)

# ── JAUGES ────────────────────────────────────────────────────────────────────
st.markdown(
    gauge_html("🔥 Calories", totaux["kcal"], settings["objectif_kcal"], "kcal") +
    gauge_html("💪 Protéines", totaux["proteines"], settings["objectif_prot"], "g") +
    gauge_html("⚡ Glucides", totaux["glucides"], settings["objectif_gluc"], "g") +
    gauge_html("🥑 Lipides", totaux["lipides"], settings["objectif_lip"], "g"),
    unsafe_allow_html=True
)

# ── TABS ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(["➕ Aliment", "🍽️ Repas", "📋 Base", "📊 Historique", "⚙️ Réglages"])

# ═══════════════════════════════════════════════════
# TAB 1 — ALIMENT
# ═══════════════════════════════════════════════════
with tab1:
    # ── BOUTON REMPLIS TES CALORIES ──────────────────────────────────────────
    kcal_manquant = settings["objectif_kcal"] - totaux["kcal"]
    if kcal_manquant > 0:
        col_fill, col_fill_info = st.columns([2, 3])
        with col_fill:
            if st.button(f"🍽️ Propose-moi quoi manger", key="btn_fill_top"):
                st.session_state["show_fill"] = True
        with col_fill_info:
            st.markdown(f"<div style='padding:10px 0;font-size:0.78rem;color:#666'>Il te manque <span style='color:#e8ff5a;font-family:Space Mono,monospace;font-weight:700'>{round(kcal_manquant)} kcal</span></div>", unsafe_allow_html=True)

        if st.session_state.get("show_fill"):
            st.markdown('<div class="section-title">💡 Suggestions pour compléter</div>', unsafe_allow_html=True)
            sug_mode = st.radio("Basé sur :", ["Suggestions intelligentes", "Mes repas", "Claude AI 🤖"],
                                horizontal=True, label_visibility="collapsed", key="sug_mode_top")
            TOLERANCE = 0.30

            if sug_mode == "Suggestions intelligentes":
                prot_gap = max(0, settings["objectif_prot"] - totaux["proteines"])
                gluc_gap = max(0, settings["objectif_gluc"] - totaux["glucides"])
                lip_gap  = max(0, settings["objectif_lip"]  - totaux["lipides"])
                st.markdown(f"""
                <div class="notice" style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;text-align:center">
                    <div><strong style="color:#e8ff5a">{round(kcal_manquant)}</strong><br><span style="font-size:0.68rem;color:#555">kcal restantes</span></div>
                    <div><strong>{round(prot_gap)}g</strong><br><span style="font-size:0.68rem;color:#555">prot</span></div>
                    <div><strong>{round(gluc_gap)}g</strong><br><span style="font-size:0.68rem;color:#555">gluc</span></div>
                    <div><strong>{round(lip_gap)}g</strong><br><span style="font-size:0.68rem;color:#555">lip</span></div>
                </div>
                """, unsafe_allow_html=True)
                style_choice = st.selectbox(
                    "Type de proposition",
                    ["Auto", "Riche en protéines", "Léger / sèche", "Rapide"],
                    label_visibility="collapsed",
                    key="smart_style_choice"
                )
                combos = generate_smart_suggestions(foods_db, totaux, settings, style=style_choice)
                if not combos:
                    st.markdown('<div class="notice">Je n’ai pas assez d’aliments adaptés dans ta base pour proposer un vrai plat cohérent. Ajoute au moins une protéine, un féculent et idéalement un légume dans la base.</div>', unsafe_allow_html=True)
                for i, combo in enumerate(combos):
                    col_s, col_b = st.columns([5, 1])
                    with col_s:
                        items_html = "".join([
                            f"<div style='display:flex;justify-content:space-between;border-top:1px solid #202020;padding:4px 0'>"
                            f"<span style='color:#888'>{it['nom']}</span><span style='color:#555'>{it['grammes']}g</span></div>"
                            for it in combo["items"]
                        ])
                        st.markdown(f"""
                        <div class="meal-card" style="margin:6px 0">
                            <div style="display:flex;justify-content:space-between;align-items:center;gap:8px">
                                <div class="meal-name">🍽️ {combo['titre']}</div>
                                <span style="font-size:0.62rem;color:#0f0f0f;background:#e8ff5a;border-radius:999px;padding:3px 8px;font-weight:700">{combo['tag']}</span>
                            </div>
                            <div class="meal-meta" style="margin:6px 0 8px;color:#777">{combo['raison']}</div>
                            {items_html}
                            <div style="display:flex;gap:12px;flex-wrap:wrap;font-size:0.72rem;margin-top:8px;color:#666">
                                <span style="color:#e8ff5a;font-weight:700">🔥 {round(combo['kcal'])} kcal</span>
                                <span>💪 P {combo['proteines']}g</span>
                                <span>⚡ G {combo['glucides']}g</span>
                                <span>🥑 L {combo['lipides']}g</span>
                                <span>🌿 F {combo['fibres']}g</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_b:
                        if st.button("➕", key=f"smart_fill_food_{i}"):
                            for it in combo["items"]:
                                entry = {k: it[k] for k in ("kcal", "proteines", "glucides", "lipides", "fibres")}
                                entry.update({"nom": it["nom"], "grammes": it["grammes"], "repas": combo["titre"]})
                                daily_log[today].append(entry)
                            save_json(LOG_FILE, daily_log)
                            st.session_state["show_fill"] = False
                            st.rerun()

            elif sug_mode == "Mes repas":
                suggestions_meals = []
                for mname, mdata in meals_db.items():
                    entries = [calc_macros(foods_db[i["food"]], i["grams"])
                               for i in mdata["items"] if i["food"] in foods_db and i["grams"]>0]
                    if not entries: continue
                    pt = sum_macros(entries)
                    if pt["kcal"] <= 0: continue
                    scale = kcal_manquant / pt["kcal"]
                    scaled_kcal = round(pt["kcal"] * scale)
                    if abs(scaled_kcal - kcal_manquant) / max(kcal_manquant,1) <= TOLERANCE and 0.3 <= scale <= 2.0:
                        suggestions_meals.append({"nom":mname,"scale":round(scale,2),"kcal":scaled_kcal,
                            "proteines":round(pt["proteines"]*scale,1),"glucides":round(pt["glucides"]*scale,1),
                            "lipides":round(pt["lipides"]*scale,1),"items":mdata["items"]})
                suggestions_meals.sort(key=lambda x: abs(x["kcal"]-kcal_manquant))
                if not suggestions_meals:
                    st.info("Aucun repas enregistré ne correspond. Essaie Claude AI 🤖.")
                for i, s in enumerate(suggestions_meals[:4]):
                    scale_txt = f"×{s['scale']}" if s['scale'] != 1.0 else "quantité normale"
                    col_s, col_b = st.columns([4,1])
                    with col_s:
                        st.markdown(f"""
                        <div class="meal-card" style="margin:4px 0">
                            <div class="meal-name">{s['nom']} <span style="color:#444;font-size:0.7rem">({scale_txt})</span></div>
                            <div class="meal-meta"><span style="color:#e8ff5a">{s['kcal']} kcal</span> · P {s['proteines']}g G {s['glucides']}g L {s['lipides']}g</div>
                        </div>""", unsafe_allow_html=True)
                    with col_b:
                        if st.button("➕", key=f"fill_meal_{i}"):
                            for item in s["items"]:
                                if item["food"] in foods_db:
                                    g_scaled = max(1, round(item["grams"]*s["scale"]))
                                    e = calc_macros(foods_db[item["food"]], g_scaled)
                                    e.update({"nom":item["food"],"grammes":g_scaled,"repas":s["nom"]})
                                    daily_log[today].append(e)
                            save_json(LOG_FILE, daily_log)
                            st.session_state["show_fill"] = False
                            st.rerun()

            else:  # Claude AI
                prot_rest = max(0, round(settings["objectif_prot"] - totaux["proteines"]))
                gluc_rest = max(0, round(settings["objectif_gluc"] - totaux["glucides"]))
                lip_rest  = max(0, round(settings["objectif_lip"]  - totaux["lipides"]))
                foods_list = ", ".join(list(foods_db.keys())[:20])
                # Clé API depuis st.secrets (ajoute ANTHROPIC_API_KEY dans secrets Streamlit)
                api_key = st.secrets.get("ANTHROPIC_API_KEY", "") if hasattr(st, "secrets") else ""
                if not api_key:
                    st.markdown('<div class="notice">Clé Claude manquante : ajoute ANTHROPIC_API_KEY dans les Secrets Streamlit pour utiliser cette option IA.</div>', unsafe_allow_html=True)
                elif st.button("✨ Générer une suggestion IA", key="btn_ai_fill"):
                    with st.spinner("Claude réfléchit..."):
                        try:
                            import json as _json
                            prompt = f"""Tu es un coach nutrition expert. L'utilisateur a mangé {round(totaux['kcal'])} kcal et doit atteindre {settings['objectif_kcal']} kcal.
Déficits : {round(kcal_manquant)} kcal, {prot_rest}g protéines, {gluc_rest}g glucides, {lip_rest}g lipides.
Aliments disponibles : {foods_list}.
Propose un repas complet avec 2 ou 3 aliments concrets avec grammages précis pour combler ces déficits.
Réponds UNIQUEMENT en JSON valide sans markdown ni backticks :
{{"suggestion":"Titre repas","description":"explique en 1 phrase pourquoi c'est adapté","kcal":300,"proteines":25,"glucides":30,"lipides":8,"portions":"150g poulet + 100g riz + 200g brocoli","items":[{{"nom":"Filet de poulet cru","grammes":150}},{{"nom":"Riz basmati cru","grammes":80}}]}}"""
                            resp = requests.post(
                                "https://api.anthropic.com/v1/messages",
                                headers={"Content-Type": "application/json", "x-api-key": api_key, "anthropic-version": "2023-06-01"},
                                json={"model": "claude-haiku-4-5-20251001", "max_tokens": 400,
                                      "messages": [{"role": "user", "content": prompt}]},
                                timeout=20
                            )
                            data = resp.json()
                            if "error" in data:
                                st.error(f"API : {data['error']['message']}")
                            else:
                                raw = data["content"][0]["text"].strip().replace("```json","").replace("```","").strip()
                                st.session_state["ai_suggestion"] = _json.loads(raw)
                        except Exception as e:
                            st.error(f"Erreur : {e}")

                if "ai_suggestion" in st.session_state:
                    s = st.session_state["ai_suggestion"]
                    st.markdown(f"""
                    <div style="background:#141414;border:1px solid #2a2a2a;border-radius:12px;padding:16px;margin:8px 0">
                        <div style="font-family:Space Mono,monospace;font-size:1rem;color:#e8ff5a;font-weight:700;margin-bottom:4px">✨ {s.get('suggestion','?')}</div>
                        <div style="font-size:0.78rem;color:#888;margin-bottom:6px">{s.get('description','')}</div>
                        <div style="font-size:0.72rem;color:#666;margin-bottom:10px">📦 {s.get('portions','')}</div>
                        <div style="display:flex;gap:12px;font-size:0.75rem">
                            <span style="color:#e8ff5a">🔥 {s.get('kcal','?')} kcal</span>
                            <span>💪 P {s.get('proteines','?')}g</span>
                            <span>⚡ G {s.get('glucides','?')}g</span>
                            <span>🥑 L {s.get('lipides','?')}g</span>
                        </div>
                    </div>""", unsafe_allow_html=True)
                    if st.button("➕ Ajouter au journal", key="btn_add_ai"):
                        entry = {"nom":s.get("suggestion","Suggestion IA"),"grammes":0,
                                 "kcal":float(s.get("kcal",0)),"proteines":float(s.get("proteines",0)),
                                 "glucides":float(s.get("glucides",0)),"lipides":float(s.get("lipides",0)),"fibres":0.0}
                        daily_log[today].append(entry)
                        save_json(LOG_FILE, daily_log)
                        del st.session_state["ai_suggestion"]
                        st.session_state["show_fill"] = False
                        st.rerun()

            if st.button("✕ Fermer", key="btn_close_fill"):
                st.session_state["show_fill"] = False
                st.rerun()

        st.markdown("---")

    st.markdown('<div class="section-title">Ajouter un aliment</div>', unsafe_allow_html=True)
    food_names = sorted(foods_db.keys())
    selected = st.selectbox("Aliment", food_names, label_visibility="collapsed", key="sel_food")
    grams = st.number_input("Grammes", min_value=1, max_value=2000, value=100, step=5, key="inp_grams")
    if selected:
        preview = calc_macros(foods_db[selected], grams)
        src = foods_db[selected].get("source","")
        st.markdown(f"""
        <div class="food-item">
            <span>{selected} ({grams}g)<span class="tag-src">{src}</span></span>
            <span class="food-kcal">{preview['kcal']} kcal</span>
        </div>
        <div style='display:flex;gap:10px;font-size:0.73rem;color:#555;margin:4px 0 10px 4px'>
            <span>P {preview['proteines']}g</span><span>G {preview['glucides']}g</span>
            <span>L {preview['lipides']}g</span><span>F {preview['fibres']}g</span>
        </div>""", unsafe_allow_html=True)
    if st.button("➕ Ajouter au journal", key="btn_add_food"):
        entry = calc_macros(foods_db[selected], grams)
        entry.update({"nom":selected,"grammes":grams})
        daily_log[today].append(entry)
        save_json(LOG_FILE, daily_log)
        st.rerun()

    # ── REPAS ÉPINGLÉS ────────────────────────────────
    pinned = {n: m for n, m in meals_db.items() if m.get("pinned")}
    if pinned:
        st.markdown('<div class="section-title">⭐ Repas rapides</div>', unsafe_allow_html=True)
        for mname, mdata in pinned.items():
            # Calcul total du repas avec grammes par défaut
            entries_preview = []
            for item in mdata["items"]:
                if item["food"] in foods_db and item["grams"] > 0:
                    e = calc_macros(foods_db[item["food"]], item["grams"])
                    entries_preview.append(e)
            pt = sum_macros(entries_preview) if entries_preview else {"kcal":0,"proteines":0,"glucides":0,"lipides":0,"fibres":0}
            col_pin, col_btn = st.columns([4, 1])
            with col_pin:
                st.markdown(f"""
                <div class="meal-card" style="margin:4px 0">
                    <div class="meal-name">⭐ {mname}</div>
                    <div class="meal-meta">{pt['kcal']} kcal &nbsp;|&nbsp; P {pt['proteines']}g G {pt['glucides']}g L {pt['lipides']}g</div>
                </div>""", unsafe_allow_html=True)
            with col_btn:
                if st.button("➕", key=f"pin_add_{mname}"):
                    for item in mdata["items"]:
                        if item["food"] in foods_db and item["grams"] > 0:
                            e = calc_macros(foods_db[item["food"]], item["grams"])
                            e.update({"nom": item["food"], "grammes": item["grams"], "repas": mname})
                            daily_log[today].append(e)
                    save_json(LOG_FILE, daily_log)
                    st.rerun()

    if daily_log[today]:
        st.markdown('<div class="section-title">Journal du jour</div>', unsafe_allow_html=True)
        for i, entry in enumerate(reversed(daily_log[today])):
            idx = len(daily_log[today]) - 1 - i
            col_f, col_d = st.columns([5,1])
            with col_f:
                meal_tag = f" <span style='color:#333;font-size:0.65rem'>[{entry['repas']}]</span>" if "repas" in entry else ""
                st.markdown(f"""
                <div class="food-item">
                    <span>{entry.get('nom','?')} <span style='color:#333'>({entry.get('grammes','?')}g)</span>{meal_tag}</span>
                    <span class="food-kcal">{entry['kcal']} kcal</span>
                </div>""", unsafe_allow_html=True)
            with col_d:
                if st.button("✕", key=f"del_{idx}"):
                    daily_log[today].pop(idx)
                    save_json(LOG_FILE, daily_log)
                    st.rerun()

    st.markdown("---")
    if st.button("🗑️ Effacer le journal du jour"):
        daily_log[today] = []
        save_json(LOG_FILE, daily_log)
        st.rerun()


with tab2:
    meal_sub = st.radio("", ["Utiliser", "Créer", "Gérer"], horizontal=True,
                        label_visibility="collapsed", key="meal_sub")

    if meal_sub == "Utiliser":
        st.markdown('<div class="section-title">Ajouter un repas au journal</div>', unsafe_allow_html=True)
        if not meals_db:
            st.info("Aucun repas sauvegardé. Va dans « Créer ».")
        else:
            meal_choice = st.selectbox("Repas", list(meals_db.keys()), label_visibility="collapsed", key="sel_meal_use")
            if meal_choice:
                st.markdown("**Personnalise les quantités :**")
                meal_preview_entries = []
                for item in meals_db[meal_choice]["items"]:
                    fname = item["food"]
                    if fname not in foods_db:
                        st.markdown(f'<div class="notice">{fname} absent de la base.</div>', unsafe_allow_html=True)
                        continue
                    g = st.number_input(fname, min_value=0, max_value=2000,
                                        value=item["grams"], step=5, key=f"use_{meal_choice}_{fname}")
                    if g > 0:
                        e = calc_macros(foods_db[fname], g)
                        e.update({"nom":fname,"grammes":g,"repas":meal_choice})
                        meal_preview_entries.append(e)
                if meal_preview_entries:
                    pt = sum_macros(meal_preview_entries)
                    st.markdown(f"""
                    <div class="meal-card">
                        <div class="meal-name">{meal_choice}</div>
                        <div class="meal-meta">{pt['kcal']} kcal &nbsp;|&nbsp; P {pt['proteines']}g &nbsp; G {pt['glucides']}g &nbsp; L {pt['lipides']}g</div>
                    </div>""", unsafe_allow_html=True)
                if st.button("➕ Ajouter ce repas", key="btn_add_meal"):
                    for e in meal_preview_entries:
                        daily_log[today].append(e)
                    save_json(LOG_FILE, daily_log)
                    st.success(f"✅ {meal_choice} ajouté !")
                    st.rerun()

    elif meal_sub == "Créer":
        st.markdown('<div class="section-title">Nouveau repas</div>', unsafe_allow_html=True)
        meal_name_new = st.text_input("Nom du repas", placeholder="ex: Petit-déj classique", key="meal_name_new")
        selected_foods = st.multiselect("Aliments", sorted(foods_db.keys()), key="meal_foods_sel")
        meal_items = []
        for fname in selected_foods:
            g = st.number_input(f"{fname} (g)", min_value=0, max_value=2000, value=100, step=5, key=f"newmeal_{fname}")
            meal_items.append({"food":fname,"grams":g})
        if selected_foods:
            pe = [calc_macros(foods_db[i["food"]], i["grams"]) for i in meal_items if i["grams"]>0]
            if pe:
                pt = sum_macros(pe)
                st.markdown(f"""
                <div class="meal-card">
                    <div class="meal-name">{meal_name_new or "Nouveau repas"}</div>
                    <div class="meal-meta">{pt['kcal']} kcal | P {pt['proteines']}g G {pt['glucides']}g L {pt['lipides']}g</div>
                </div>""", unsafe_allow_html=True)
        if st.button("💾 Sauvegarder le repas", key="btn_save_meal"):
            if not meal_name_new: st.error("Donne un nom.")
            elif not meal_items:  st.error("Ajoute au moins un aliment.")
            else:
                meals_db[meal_name_new] = {"items":meal_items}
                save_json(MEALS_FILE, meals_db)
                st.success(f"✅ « {meal_name_new} » sauvegardé !")
                st.rerun()

    else:  # Gérer
        st.markdown('<div class="section-title">Mes repas</div>', unsafe_allow_html=True)
        if not meals_db:
            st.info("Aucun repas.")
        else:
            for mname, mdata in list(meals_db.items()):
                is_pinned = mdata.get("pinned", False)
                col_m, col_pin, col_d = st.columns([4, 1, 1])
                with col_m:
                    items_str = ", ".join([f"{i['food']} ({i['grams']}g)" for i in mdata["items"]])
                    pin_badge = "⭐ " if is_pinned else ""
                    st.markdown(f"""
                    <div class="meal-card">
                        <div class="meal-name">{pin_badge}{mname}</div>
                        <div class="meal-meta">{items_str}</div>
                    </div>""", unsafe_allow_html=True)
                with col_pin:
                    pin_label = "★" if is_pinned else "☆"
                    if st.button(pin_label, key=f"pin_{mname}", help="Épingler / désépingler"):
                        meals_db[mname]["pinned"] = not is_pinned
                        save_json(MEALS_FILE, meals_db)
                        st.rerun()
                with col_d:
                    if st.button("✕", key=f"del_meal_{mname}"):
                        del meals_db[mname]
                        save_json(MEALS_FILE, meals_db)
                        st.rerun()

# ═══════════════════════════════════════════════════
# TAB 3 — BASE D'ALIMENTS
# ═══════════════════════════════════════════════════
with tab3:
    base_sub = st.radio("", ["Voir / Supprimer", "Rechercher", "Ajout manuel"],
                        horizontal=True, label_visibility="collapsed", key="base_sub")

    if base_sub == "Voir / Supprimer":
        st.markdown('<div class="section-title">Base d\'aliments</div>', unsafe_allow_html=True)
        fltr = st.text_input("Filtrer", placeholder="recherche...", label_visibility="collapsed", key="filter_db")
        for fname, fdata in sorted(foods_db.items()):
            if fltr.lower() not in fname.lower(): continue
            col_f, col_d = st.columns([5,1])
            with col_f:
                st.markdown(f"""
                <div class="food-item" style='flex-direction:column;align-items:flex-start'>
                    <span style='font-weight:600'>{fname}<span class="tag-src">{fdata.get('source','')}</span></span>
                    <span style='color:#555;font-size:0.72rem'>{fdata['kcal']} kcal | P:{fdata['proteines']}g G:{fdata['glucides']}g L:{fdata['lipides']}g</span>
                </div>""", unsafe_allow_html=True)
            with col_d:
                if st.button("✕", key=f"del_db_{fname}"):
                    del foods_db[fname]
                    save_json(DB_FILE, foods_db)
                    st.rerun()

    elif base_sub == "Rechercher":
        st.markdown('<div class="section-title">Open Food Facts</div>', unsafe_allow_html=True)
        sq = st.text_input("Aliment", placeholder="ex: Avocat, Saumon...", label_visibility="collapsed", key="sq")
        if st.button("🔎 Rechercher", key="btn_search"):
            if sq:
                with st.spinner("Recherche..."):
                    st.session_state["search_results"] = search_openfoodfacts(sq)
                if not st.session_state.get("search_results"):
                    st.markdown('<div class="notice">Aucun résultat. Essaie un nom plus court ou ajoute manuellement.</div>', unsafe_allow_html=True)
        if st.session_state.get("search_results"):
            for i, r in enumerate(st.session_state["search_results"]):
                col_r, col_b = st.columns([4,1])
                with col_r:
                    st.markdown(f"""
                    <div class="food-item" style='flex-direction:column;align-items:flex-start'>
                        <span style='font-weight:600'>{r['name']}</span>
                        <span style='color:#555;font-size:0.72rem'>{r['kcal']} kcal | P:{r['proteines']}g G:{r['glucides']}g L:{r['lipides']}g</span>
                    </div>""", unsafe_allow_html=True)
                with col_b:
                    if st.button("＋", key=f"add_sr_{i}"):
                        foods_db[r["name"]] = {k:v for k,v in r.items() if k!="name"}
                        save_json(DB_FILE, foods_db)
                        st.success(f"✅ {r['name']} ajouté !")
                        st.rerun()

    else:
        st.markdown('<div class="section-title">Ajout manuel</div>', unsafe_allow_html=True)
        m_name = st.text_input("Nom de l'aliment", key="m_name")
        mc1, mc2 = st.columns(2)
        m_kcal = mc1.number_input("kcal / 100g", min_value=0.0, value=0.0, key="m_kcal")
        m_prot = mc2.number_input("Protéines (g)", min_value=0.0, value=0.0, key="m_prot")
        mc3, mc4 = st.columns(2)
        m_gluc = mc3.number_input("Glucides (g)", min_value=0.0, value=0.0, key="m_gluc")
        m_lip  = mc4.number_input("Lipides (g)", min_value=0.0, value=0.0, key="m_lip")
        if st.button("💾 Sauvegarder", key="btn_save_manual"):
            if m_name:
                foods_db[m_name] = {"kcal":m_kcal,"proteines":m_prot,"glucides":m_gluc,"lipides":m_lip,"fibres":0.0,"source":"Manuel"}
                save_json(DB_FILE, foods_db)
                st.success(f"✅ {m_name} ajouté !")
                st.rerun()
            else: st.error("Entre un nom.")

# ═══════════════════════════════════════════════════
# TAB 4 — HISTORIQUE
# ═══════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-title">Historique semaine</div>', unsafe_allow_html=True)

    all_dates = sorted(daily_log.keys(), reverse=True)
    if not all_dates:
        st.info("Aucune donnée enregistrée.")
    else:
        def get_monday(d_str):
            d = datetime.strptime(d_str, "%Y-%m-%d").date()
            return d - timedelta(days=d.weekday())

        mondays = sorted(set(get_monday(d) for d in all_dates), reverse=True)
        monday_labels = [f"Semaine du {m.strftime('%d %b %Y')}" for m in mondays]
        sel_week_label = st.selectbox("Semaine", monday_labels, label_visibility="collapsed", key="sel_week")
        sel_monday = mondays[monday_labels.index(sel_week_label)]

        week_days = [sel_monday + timedelta(days=i) for i in range(7)]
        day_labels = [d.strftime("%a %d") for d in week_days]
        kcal_vals, prot_vals, gluc_vals, lip_vals = [], [], [], []
        obj_kcal = settings["objectif_kcal"]

        for d in week_days:
            entries = daily_log.get(str(d), [])
            t = sum_macros(entries) if entries else {"kcal":0,"proteines":0,"glucides":0,"lipides":0,"fibres":0}
            kcal_vals.append(t["kcal"])
            prot_vals.append(t["proteines"])
            gluc_vals.append(t["glucides"])
            lip_vals.append(t["lipides"])

        # Barres calories
        st.markdown('<div class="section-title">Calories / jour</div>', unsafe_allow_html=True)
        max_kcal = max(max(kcal_vals, default=0), obj_kcal) * 1.15 or 2500
        bars_html = '<div style="display:flex;align-items:flex-end;gap:6px;height:120px;margin:8px 0 4px">'
        for i, (val, label) in enumerate(zip(kcal_vals, day_labels)):
            pct = (val / max_kcal) * 100 if max_kcal else 0
            is_today = str(week_days[i]) == today
            color = "#e8ff5a" if is_today else ("#ff5a5a" if val > obj_kcal * 1.05 else "#3a3a3a" if val == 0 else "#5a8fff")
            border = "2px solid #e8ff5a" if is_today else "none"
            bars_html += f"""<div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:3px">
                <span style="font-family:Space Mono,monospace;font-size:0.6rem;color:#888">{int(val) if val else ''}</span>
                <div style="width:100%;height:{max(pct,2):.1f}%;background:{color};border-radius:4px 4px 0 0;border:{border};min-height:3px"></div>
                <span style="font-size:0.6rem;color:#555;white-space:nowrap">{label}</span>
            </div>"""
        bars_html += '</div>'
        obj_pct = (obj_kcal / max_kcal * 100) if max_kcal else 50
        bars_html += f"""<div style="position:relative;margin-top:-148px;height:120px;pointer-events:none">
          <div style="position:absolute;top:{100-obj_pct:.1f}%;width:100%;border-top:1px dashed #444"></div>
          <span style="position:absolute;top:{max(100-obj_pct-5,0):.1f}%;right:0;font-size:0.6rem;color:#444">obj {obj_kcal}</span>
        </div><div style="height:20px"></div>"""
        st.markdown(bars_html, unsafe_allow_html=True)

        # Sparklines macros
        st.markdown('<div class="section-title">Macros / jour</div>', unsafe_allow_html=True)

        def sparkline(values, color, label):
            if not any(values): return ""
            mx = max(values) or 1
            pts = " ".join([f"{i*16+8},{int(40-(v/mx)*34)}" for i,v in enumerate(values)])
            dots = "".join([f'<circle cx="{i*16+8}" cy="{int(40-(v/mx)*34)}" r="3" fill="{color}"/>' for i,v in enumerate(values)])
            val_labels = "".join([f'<text x="{i*16+8}" y="{int(40-(v/mx)*34)-5}" text-anchor="middle" font-size="7" fill="{color}">{int(v) if v else ""}</text>' for i,v in enumerate(values)])
            day_ticks = "".join([f'<text x="{i*16+8}" y="56" text-anchor="middle" font-size="7" fill="#555">{day_labels[i].split()[0]}</text>' for i in range(7)])
            return f"""<div style="margin:10px 0 4px">
              <div style="font-size:0.7rem;color:{color};font-family:Space Mono,monospace;margin-bottom:2px">{label}</div>
              <svg width="100%" viewBox="0 0 120 64" preserveAspectRatio="none" style="height:64px">
                <polyline points="{pts}" fill="none" stroke="{color}" stroke-width="1.5" opacity="0.6"/>
                {dots}{val_labels}{day_ticks}
              </svg></div>"""

        st.markdown(
            sparkline(prot_vals, "#e8ff5a", "💪 Protéines") +
            sparkline(gluc_vals, "#5a8fff", "⚡ Glucides") +
            sparkline(lip_vals,  "#ff8c5a", "🥑 Lipides"),
            unsafe_allow_html=True
        )

        # Résumé
        st.markdown('<div class="section-title">Résumé de la semaine</div>', unsafe_allow_html=True)
        days_logged = sum(1 for v in kcal_vals if v > 0)
        avg_kcal = round(sum(kcal_vals) / days_logged, 0) if days_logged else 0
        avg_prot = round(sum(prot_vals) / days_logged, 1) if days_logged else 0
        total_kcal_week = round(sum(kcal_vals), 0)
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin:8px 0">
          <div style="background:#1a1a1a;border:1px solid #2a2a2a;border-radius:10px;padding:12px;text-align:center">
            <div style="font-family:Space Mono,monospace;font-size:1.3rem;font-weight:700;color:#e8ff5a">{int(avg_kcal)}</div>
            <div style="font-size:0.65rem;color:#555;text-transform:uppercase;letter-spacing:1px">moy kcal/j</div>
          </div>
          <div style="background:#1a1a1a;border:1px solid #2a2a2a;border-radius:10px;padding:12px;text-align:center">
            <div style="font-family:Space Mono,monospace;font-size:1.3rem;font-weight:700;color:#f0f0f0">{avg_prot}g</div>
            <div style="font-size:0.65rem;color:#555;text-transform:uppercase;letter-spacing:1px">moy prot/j</div>
          </div>
          <div style="background:#1a1a1a;border:1px solid #2a2a2a;border-radius:10px;padding:12px;text-align:center">
            <div style="font-family:Space Mono,monospace;font-size:1.3rem;font-weight:700;color:#5a8fff">{days_logged}/7</div>
            <div style="font-size:0.65rem;color:#555;text-transform:uppercase;letter-spacing:1px">jours trackés</div>
          </div>
        </div>
        <div style="font-size:0.72rem;color:#444;text-align:center;margin-top:4px">Total semaine : {int(total_kcal_week)} kcal</div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════
# TAB 5 — RÉGLAGES + CALCULATEUR
# ═══════════════════════════════════════════════════
with tab5:
    settings_sub = st.radio("", ["🧮 Calculateur", "✏️ Manuel"], horizontal=True,
                            label_visibility="collapsed", key="settings_sub")

    if settings_sub == "🧮 Calculateur":
        st.markdown('<div class="section-title">Ton profil</div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        sexe    = c1.selectbox("Sexe", ["Homme", "Femme"], key="calc_sexe")
        age     = c2.number_input("Âge", min_value=15, max_value=80, value=25, key="calc_age")
        c3, c4  = st.columns(2)
        poids   = c3.number_input("Poids (kg)", min_value=30.0, max_value=250.0, value=75.0, step=0.5, key="calc_poids")
        taille  = c4.number_input("Taille (cm)", min_value=140, max_value=230, value=175, key="calc_taille")

        bf = st.number_input("% de graisse corporelle (optionnel — laisse 0 si inconnu)",
                             min_value=0.0, max_value=60.0, value=0.0, step=0.5, key="calc_bf")

        st.markdown('<div class="section-title">Activité</div>', unsafe_allow_html=True)

        travail = st.selectbox("Type de travail", [
            "Sédentaire (bureau, télétravail)",
            "Légèrement actif (debout, déplacements)",
            "Actif (travail physique modéré)",
            "Très actif (travail physique intense)"
        ], key="calc_travail")

        sport = st.selectbox("Séances de sport / semaine", [
            "0 — Aucune",
            "1-2 — Légère activité",
            "3-4 — Activité modérée",
            "5-6 — Activité intense",
            "7+ — Athlète / double séance"
        ], key="calc_sport")

        st.markdown('<div class="section-title">Objectif</div>', unsafe_allow_html=True)
        objectif = st.selectbox("Objectif", [
            "Maintien — Garder son poids actuel",
            "Sèche — Perdre du gras, préserver le muscle",
            "Prise de masse — Gagner du muscle (surplus propre)",
            "Recomposition corporelle — Perdre du gras ET gagner du muscle"
        ], key="calc_obj")

        if st.button("🧮 Calculer mes besoins", key="btn_calc"):

            # ── BMR ───────────────────────────────────────────────
            # Katch-McArdle si % gras renseigné, sinon Mifflin-St Jeor
            if bf > 0:
                lbm = poids * (1 - bf / 100)
                bmr = 370 + (21.6 * lbm)
                formule = f"Katch-McArdle (LBM = {lbm:.1f} kg)"
            else:
                if sexe == "Homme":
                    bmr = 10 * poids + 6.25 * taille - 5 * age + 5
                else:
                    bmr = 10 * poids + 6.25 * taille - 5 * age - 161
                formule = "Mifflin-St Jeor"

            # ── FACTEUR ACTIVITÉ ──────────────────────────────────
            # Facteur travail
            travail_map = {
                "Sédentaire (bureau, télétravail)": 0.0,
                "Légèrement actif (debout, déplacements)": 0.1,
                "Actif (travail physique modéré)": 0.2,
                "Très actif (travail physique intense)": 0.35,
            }
            # Facteur sport
            sport_map = {
                "0 — Aucune": 1.2,
                "1-2 — Légère activité": 1.375,
                "3-4 — Activité modérée": 1.55,
                "5-6 — Activité intense": 1.725,
                "7+ — Athlète / double séance": 1.9,
            }
            # TDEE = BMR × facteur sport, puis ajustement travail additif
            tdee_base = bmr * sport_map[sport]
            tdee = tdee_base + (bmr * travail_map[travail])
            tdee = round(tdee)

            # ── CALORIES PAR OBJECTIF ─────────────────────────────
            obj_key = objectif.split("—")[0].strip()
            if obj_key == "Maintien":
                kcal_cible = tdee
                deficit_label = "= TDEE"
            elif obj_key == "Sèche":
                # Déficit 20% — optimal pour préserver masse maigre (max -500 kcal)
                deficit = min(round(tdee * 0.20), 500)
                kcal_cible = tdee - deficit
                deficit_label = f"−{deficit} kcal (−20% TDEE)"
            elif obj_key == "Prise de masse":
                # Surplus 10% — lean bulk
                surplus = round(tdee * 0.10)
                kcal_cible = tdee + surplus
                deficit_label = f"+{surplus} kcal (+10% TDEE)"
            else:  # Recomposition
                # Légère déficit −200 kcal max
                kcal_cible = tdee - 200
                deficit_label = "−200 kcal (recomp)"

            # ── MACROS PAR OBJECTIF ───────────────────────────────
            # Toutes les valeurs basées sur littérature scientifique
            if obj_key == "Maintien":
                # Prot 1.6g/kg — maintenance muscle + santé générale
                ratio_prot = 1.6
                prot_g = round(poids * ratio_prot)
                lip_g  = round(poids * 1.0)   # 1g/kg — santé hormonale
            elif obj_key == "Sèche":
                # Prot haute 2.0g/kg pour préserver masse maigre en déficit
                ratio_prot = 2.0
                prot_g = round(poids * ratio_prot)
                lip_g  = round(poids * 0.8)   # min 0.8g/kg pour hormones
            elif obj_key == "Prise de masse":
                # Prot 1.8g/kg — soutien synthèse protéique
                ratio_prot = 1.8
                prot_g = round(poids * ratio_prot)
                lip_g  = round(poids * 1.0)   # 1g/kg
            else:  # Recomposition
                # Prot max 2.2g/kg — protéger masse maigre + construire
                ratio_prot = 2.2
                prot_g = round(poids * ratio_prot)
                lip_g  = round(poids * 0.9)

            # Glucides = calories restantes après prot + lip
            prot_kcal = prot_g * 4
            lip_kcal  = lip_g * 9
            gluc_kcal = kcal_cible - prot_kcal - lip_kcal
            gluc_g    = max(round(gluc_kcal / 4), 50)  # min 50g glucides

            # Recalcul kcal réel (arrondi cohérent)
            kcal_reel = prot_g * 4 + gluc_g * 4 + lip_g * 9

            st.session_state["last_calc_to_apply"] = {"kcal": kcal_reel, "prot": prot_g, "gluc": gluc_g, "lip": lip_g}

            # ── AFFICHAGE RÉSULTAT ────────────────────────────────
            st.markdown(f"""
            <div style="background:#111;border:1px solid #222;border-radius:16px;padding:20px;margin:16px 0">
              <div style="font-family:Space Mono,monospace;font-size:0.65rem;color:#444;letter-spacing:2px;text-transform:uppercase;margin-bottom:12px">
                Formule : {formule}
              </div>

              <div style="display:flex;justify-content:space-between;margin-bottom:6px">
                <span style="color:#888;font-size:0.8rem">BMR (métabolisme de base)</span>
                <span style="font-family:Space Mono,monospace;color:#f0f0f0">{round(bmr)} kcal</span>
              </div>
              <div style="display:flex;justify-content:space-between;margin-bottom:16px">
                <span style="color:#888;font-size:0.8rem">TDEE (dépense totale)</span>
                <span style="font-family:Space Mono,monospace;color:#f0f0f0">{tdee} kcal</span>
              </div>

              <div style="border-top:1px solid #1e1e1e;padding-top:16px;margin-bottom:16px">
                <div style="font-size:0.7rem;color:#555;margin-bottom:6px">{objectif.split('—')[0].strip().upper()} &nbsp;·&nbsp; {deficit_label}</div>
                <div style="font-family:Space Mono,monospace;font-size:2.8rem;font-weight:700;color:#e8ff5a;line-height:1">{kcal_reel}</div>
                <div style="font-size:0.65rem;color:#555;letter-spacing:2px;text-transform:uppercase">calories / jour</div>
              </div>

              <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px">
                <div style="background:#1a1a1a;border-radius:10px;padding:12px;text-align:center">
                  <div style="font-family:Space Mono,monospace;font-size:1.2rem;font-weight:700;color:#e8ff5a">{prot_g}g</div>
                  <div style="font-size:0.62rem;color:#555;text-transform:uppercase;letter-spacing:1px">💪 Protéines</div>
                  <div style="font-size:0.6rem;color:#333;margin-top:2px">{ratio_prot}g/kg</div>
                </div>
                <div style="background:#1a1a1a;border-radius:10px;padding:12px;text-align:center">
                  <div style="font-family:Space Mono,monospace;font-size:1.2rem;font-weight:700;color:#5a8fff">{gluc_g}g</div>
                  <div style="font-size:0.62rem;color:#555;text-transform:uppercase;letter-spacing:1px">⚡ Glucides</div>
                  <div style="font-size:0.6rem;color:#333;margin-top:2px">calories restantes</div>
                </div>
                <div style="background:#1a1a1a;border-radius:10px;padding:12px;text-align:center">
                  <div style="font-family:Space Mono,monospace;font-size:1.2rem;font-weight:700;color:#ff8c5a">{lip_g}g</div>
                  <div style="font-size:0.62rem;color:#555;text-transform:uppercase;letter-spacing:1px">🥑 Lipides</div>
                  <div style="font-size:0.6rem;color:#333;margin-top:2px">{round(lip_g*9/kcal_reel*100)}% kcal</div>
                </div>
              </div>

              <div style="margin-top:14px;padding:10px;background:#0d0d0d;border-radius:8px;font-size:0.72rem;color:#555;line-height:1.6">
                ⚠️ Ces valeurs sont des <strong style="color:#666">estimations scientifiques</strong> (±10%). Ajuste après 2–3 semaines selon tes résultats réels. Aucun calculateur ne remplace le suivi terrain.
              </div>
            </div>
            """, unsafe_allow_html=True)


        if "last_calc_to_apply" in st.session_state:
            if st.button("✅ Appliquer ces objectifs", key="btn_apply_calc"):
                r = st.session_state["last_calc_to_apply"]
                st.session_state["objectif_kcal"] = int(r["kcal"])
                st.session_state["objectif_prot"] = int(r["prot"])
                st.session_state["objectif_gluc"] = int(r["gluc"])
                st.session_state["objectif_lip"]  = int(r["lip"])
                st.success("Objectifs appliqués aux jauges.")
                st.rerun()

    else:  # Manuel
        st.markdown('<div class="section-title">Objectifs manuels</div>', unsafe_allow_html=True)
        o1, o2 = st.columns(2)
        new_kcal = o1.number_input("Calories (kcal)", value=int(st.session_state["objectif_kcal"]), step=50, key="o_kcal")
        new_prot = o2.number_input("Protéines (g)", value=int(st.session_state["objectif_prot"]), step=5, key="o_prot")
        o3, o4 = st.columns(2)
        new_gluc = o3.number_input("Glucides (g)", value=int(st.session_state["objectif_gluc"]), step=10, key="o_gluc")
        new_lip  = o4.number_input("Lipides (g)", value=int(st.session_state["objectif_lip"]), step=5, key="o_lip")
        if st.button("💾 Sauvegarder", key="btn_save_settings"):
            st.session_state["objectif_kcal"] = new_kcal
            st.session_state["objectif_prot"] = new_prot
            st.session_state["objectif_gluc"] = new_gluc
            st.session_state["objectif_lip"]  = new_lip
            st.success("✅ Objectifs mis à jour !")
            st.rerun()
