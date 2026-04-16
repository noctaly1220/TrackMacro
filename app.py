import streamlit as st
import json
import os
from datetime import date
import requests
from bs4 import BeautifulSoup

# ── CONFIG ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Macro Tracker",
    page_icon="🔥",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── CSS MOBILE-FIRST ─────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0f0f0f;
    color: #f0f0f0;
}
h1, h2, h3 { font-family: 'Space Mono', monospace; }

.stApp { background: #0f0f0f; }

/* Cards */
.macro-card {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 12px;
    padding: 16px;
    margin: 8px 0;
    text-align: center;
}
.macro-value {
    font-family: 'Space Mono', monospace;
    font-size: 1.6rem;
    font-weight: 700;
    color: #e8ff5a;
}
.macro-label {
    font-size: 0.75rem;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* Gauge */
.gauge-wrap { margin: 16px 0; }
.gauge-bar-bg {
    background: #1a1a1a;
    border-radius: 999px;
    height: 22px;
    width: 100%;
    overflow: hidden;
    border: 1px solid #2a2a2a;
}
.gauge-bar-fill {
    height: 100%;
    border-radius: 999px;
    transition: width 0.5s ease;
}
.gauge-label {
    display: flex;
    justify-content: space-between;
    font-size: 0.78rem;
    color: #888;
    margin-bottom: 4px;
}

/* Food items */
.food-item {
    background: #161616;
    border: 1px solid #252525;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 4px 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.85rem;
}
.food-kcal { color: #e8ff5a; font-family: 'Space Mono', monospace; font-weight: 700; }

/* Buttons */
.stButton > button {
    background: #e8ff5a !important;
    color: #0f0f0f !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Space Mono', monospace !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    padding: 10px 20px !important;
    width: 100% !important;
}
.stButton > button:hover { background: #d4eb3a !important; }

/* Selectbox / input */
.stSelectbox > div > div, .stNumberInput > div > div > input, .stTextInput > div > div > input {
    background: #1a1a1a !important;
    border: 1px solid #333 !important;
    color: #f0f0f0 !important;
    border-radius: 8px !important;
}

/* Section titles */
.section-title {
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #555;
    margin: 20px 0 8px 0;
}

/* Danger / success color for gauge */
.color-ok { background: linear-gradient(90deg, #e8ff5a, #a8cc00); }
.color-over { background: linear-gradient(90deg, #ff5a5a, #cc0000); }
.color-low { background: linear-gradient(90deg, #5a8fff, #0055cc); }

div[data-testid="stExpander"] {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

# ── DATA FILES ───────────────────────────────────────────────────────────────
DB_FILE = "foods_db.json"
LOG_FILE = "daily_log.json"
SETTINGS_FILE = "settings.json"

# ── DEFAULT CIQUAL DATABASE ───────────────────────────────────────────────────
DEFAULT_FOODS = {
    "Riz basmati cru": {
        "kcal": 356, "proteines": 7.6, "glucides": 78.0, "lipides": 0.9,
        "fibres": 1.0, "source": "Ciqual"
    },
    "Lentilles vertes crues": {
        "kcal": 311, "proteines": 24.0, "glucides": 45.0, "lipides": 1.4,
        "fibres": 11.4, "source": "Ciqual"
    },
    "Filet de poulet cru": {
        "kcal": 110, "proteines": 23.0, "glucides": 0.0, "lipides": 1.5,
        "fibres": 0.0, "source": "Ciqual"
    },
    "Pâtes crues": {
        "kcal": 358, "proteines": 12.5, "glucides": 70.2, "lipides": 1.8,
        "fibres": 3.0, "source": "Ciqual"
    },
    "Thon en conserve au naturel": {
        "kcal": 116, "proteines": 25.5, "glucides": 0.0, "lipides": 1.0,
        "fibres": 0.0, "source": "Ciqual"
    },
    "Brocoli surgelé": {
        "kcal": 35, "proteines": 2.8, "glucides": 4.0, "lipides": 0.4,
        "fibres": 2.6, "source": "Ciqual"
    },
    "Épinards surgelés": {
        "kcal": 20, "proteines": 2.4, "glucides": 0.8, "lipides": 0.4,
        "fibres": 2.1, "source": "Ciqual"
    },
    "Chou-fleur surgelé": {
        "kcal": 25, "proteines": 2.0, "glucides": 3.0, "lipides": 0.3,
        "fibres": 1.8, "source": "Ciqual"
    },
    "Haricots verts surgelés": {
        "kcal": 31, "proteines": 1.8, "glucides": 4.7, "lipides": 0.2,
        "fibres": 3.4, "source": "Ciqual"
    },
}

# ── HELPERS ──────────────────────────────────────────────────────────────────
def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return default

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def today_key():
    return str(date.today())

def calc_macros(food, grams):
    ratio = grams / 100
    return {
        "kcal": round(food["kcal"] * ratio, 1),
        "proteines": round(food["proteines"] * ratio, 1),
        "glucides": round(food["glucides"] * ratio, 1),
        "lipides": round(food["lipides"] * ratio, 1),
        "fibres": round(food.get("fibres", 0) * ratio, 1),
    }

def gauge_html(label, value, target, unit="g"):
    if target == 0:
        return ""
    pct = min(value / target * 100, 100)
    color_class = "color-ok" if 85 <= pct <= 105 else ("color-over" if pct > 105 else "color-low")
    return f"""
    <div class="gauge-wrap">
      <div class="gauge-label">
        <span>{label}</span>
        <span>{value:.0f} / {target} {unit}</span>
      </div>
      <div class="gauge-bar-bg">
        <div class="gauge-bar-fill {color_class}" style="width:{pct:.1f}%"></div>
      </div>
    </div>
    """

# ── SCRAPING OPEN FOOD FACTS ──────────────────────────────────────────────────
def search_openfoodfacts(query):
    """Recherche sur Open Food Facts (JSON API gratuite, pas de clé)"""
    try:
        url = f"https://world.openfoodfacts.org/cgi/search.pl"
        params = {
            "search_terms": query,
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page_size": 5,
            "lc": "fr"
        }
        r = requests.get(url, params=params, timeout=8)
        data = r.json()
        results = []
        for p in data.get("products", []):
            n = p.get("nutriments", {})
            name = p.get("product_name_fr") or p.get("product_name", "")
            if not name:
                continue
            kcal = n.get("energy-kcal_100g") or n.get("energy_100g", 0)
            prot = n.get("proteins_100g", 0)
            gluc = n.get("carbohydrates_100g", 0)
            lip  = n.get("fat_100g", 0)
            fib  = n.get("fiber_100g", 0)
            if kcal:
                results.append({
                    "name": name,
                    "kcal": round(float(kcal), 1),
                    "proteines": round(float(prot or 0), 1),
                    "glucides": round(float(gluc or 0), 1),
                    "lipides": round(float(lip or 0), 1),
                    "fibres": round(float(fib or 0), 1),
                    "source": "Open Food Facts"
                })
        return results
    except Exception as e:
        return []

# ── LOAD STATE ────────────────────────────────────────────────────────────────
foods_db = load_json(DB_FILE, DEFAULT_FOODS)
if not os.path.exists(DB_FILE):
    save_json(DB_FILE, foods_db)

daily_log = load_json(LOG_FILE, {})
settings = load_json(SETTINGS_FILE, {"objectif_kcal": 2000, "objectif_prot": 150, "objectif_gluc": 250, "objectif_lip": 65})

today = today_key()
if today not in daily_log:
    daily_log[today] = []

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("# 🔥 MACRO TRACKER")
st.markdown(f"<p style='color:#555;font-size:0.8rem;font-family:Space Mono,monospace;margin-top:-12px'>{today}</p>", unsafe_allow_html=True)

# ── TOTAUX DU JOUR ────────────────────────────────────────────────────────────
totaux = {"kcal": 0, "proteines": 0, "glucides": 0, "lipides": 0, "fibres": 0}
for entry in daily_log[today]:
    for k in totaux:
        totaux[k] += entry.get(k, 0)
totaux = {k: round(v, 1) for k, v in totaux.items()}

# Jauges
st.markdown('<div class="section-title">Progression du jour</div>', unsafe_allow_html=True)
gauge_html_all = ""
gauge_html_all += gauge_html("🔥 Calories", totaux["kcal"], settings["objectif_kcal"], "kcal")
gauge_html_all += gauge_html("💪 Protéines", totaux["proteines"], settings["objectif_prot"], "g")
gauge_html_all += gauge_html("⚡ Glucides", totaux["glucides"], settings["objectif_gluc"], "g")
gauge_html_all += gauge_html("🥑 Lipides", totaux["lipides"], settings["objectif_lip"], "g")
st.markdown(gauge_html_all, unsafe_allow_html=True)

# Macros en colonnes
c1, c2, c3, c4 = st.columns(4)
for col, key, label, emoji in [
    (c1, "kcal", "kcal", "🔥"),
    (c2, "proteines", "prot", "💪"),
    (c3, "glucides", "gluc", "⚡"),
    (c4, "lipides", "lip", "🥑"),
]:
    col.markdown(f"""
    <div class="macro-card">
        <div class="macro-value">{totaux[key]}</div>
        <div class="macro-label">{emoji} {label}</div>
    </div>""", unsafe_allow_html=True)

# ── AJOUTER UN ALIMENT ────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Ajouter un aliment</div>', unsafe_allow_html=True)

food_names = sorted(foods_db.keys())
selected = st.selectbox("Aliment", food_names, label_visibility="collapsed")
grams = st.number_input("Grammes", min_value=1, max_value=2000, value=100, step=5)

if selected:
    preview = calc_macros(foods_db[selected], grams)
    src = foods_db[selected].get("source", "")
    st.markdown(f"""
    <div class="food-item">
        <span>{selected} ({grams}g) <span style='color:#444;font-size:0.7rem'>{src}</span></span>
        <span class="food-kcal">{preview['kcal']} kcal</span>
    </div>
    <div style='display:flex;gap:8px;font-size:0.75rem;color:#666;margin-bottom:8px'>
        <span>P: {preview['proteines']}g</span>
        <span>G: {preview['glucides']}g</span>
        <span>L: {preview['lipides']}g</span>
        <span>F: {preview['fibres']}g</span>
    </div>
    """, unsafe_allow_html=True)

if st.button("➕ Ajouter"):
    entry = calc_macros(foods_db[selected], grams)
    entry["nom"] = selected
    entry["grammes"] = grams
    daily_log[today].append(entry)
    save_json(LOG_FILE, daily_log)
    st.rerun()

# ── JOURNAL DU JOUR ───────────────────────────────────────────────────────────
if daily_log[today]:
    st.markdown('<div class="section-title">Journal du jour</div>', unsafe_allow_html=True)
    for i, entry in enumerate(reversed(daily_log[today])):
        idx = len(daily_log[today]) - 1 - i
        col_food, col_del = st.columns([5, 1])
        with col_food:
            st.markdown(f"""
            <div class="food-item">
                <span>{entry['nom']} <span style='color:#444'>({entry['grammes']}g)</span></span>
                <span class="food-kcal">{entry['kcal']} kcal</span>
            </div>""", unsafe_allow_html=True)
        with col_del:
            if st.button("✕", key=f"del_{idx}"):
                daily_log[today].pop(idx)
                save_json(LOG_FILE, daily_log)
                st.rerun()

# ── AJOUTER UN NOUVEL ALIMENT ─────────────────────────────────────────────────
st.markdown('<div class="section-title">Ajouter un nouvel aliment</div>', unsafe_allow_html=True)

with st.expander("🔍 Rechercher & ajouter un aliment"):
    search_q = st.text_input("Nom de l'aliment à rechercher", placeholder="ex: Avocat, Saumon...")
    
    if st.button("🔎 Rechercher sur Open Food Facts"):
        if search_q:
            with st.spinner("Recherche en cours..."):
                results = search_openfoodfacts(search_q)
            if results:
                st.session_state["search_results"] = results
                st.session_state["search_query"] = search_q
            else:
                st.warning("Aucun résultat. Essaie un nom plus générique ou ajoute manuellement.")
                st.session_state["search_results"] = []

    if "search_results" in st.session_state and st.session_state["search_results"]:
        st.markdown("**Résultats — sélectionne pour ajouter :**")
        for i, r in enumerate(st.session_state["search_results"]):
            col_r, col_btn = st.columns([4, 1])
            with col_r:
                st.markdown(f"""
                <div class="food-item" style='flex-direction:column;align-items:flex-start'>
                    <span style='font-weight:600'>{r['name']}</span>
                    <span style='color:#888;font-size:0.72rem'>
                        {r['kcal']} kcal | P:{r['proteines']}g G:{r['glucides']}g L:{r['lipides']}g | {r['source']}
                    </span>
                </div>""", unsafe_allow_html=True)
            with col_btn:
                if st.button("＋", key=f"add_search_{i}"):
                    foods_db[r["name"]] = {k: v for k, v in r.items() if k != "name"}
                    save_json(DB_FILE, foods_db)
                    st.success(f"✅ {r['name']} ajouté à ta base !")
                    st.rerun()

    st.markdown("---")
    st.markdown("**Ou ajoute manuellement :**")
    m_name = st.text_input("Nom", key="m_name")
    mc1, mc2, mc3, mc4 = st.columns(4)
    m_kcal = mc1.number_input("kcal/100g", min_value=0.0, value=0.0, key="m_kcal")
    m_prot = mc2.number_input("Prot (g)", min_value=0.0, value=0.0, key="m_prot")
    m_gluc = mc3.number_input("Gluc (g)", min_value=0.0, value=0.0, key="m_gluc")
    m_lip  = mc4.number_input("Lip (g)", min_value=0.0, value=0.0, key="m_lip")
    if st.button("💾 Sauvegarder l'aliment"):
        if m_name:
            foods_db[m_name] = {
                "kcal": m_kcal, "proteines": m_prot, "glucides": m_gluc,
                "lipides": m_lip, "fibres": 0.0, "source": "Manuel"
            }
            save_json(DB_FILE, foods_db)
            st.success(f"✅ {m_name} ajouté !")
            st.rerun()
        else:
            st.error("Entre un nom.")

# ── OBJECTIFS ─────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Objectifs journaliers</div>', unsafe_allow_html=True)

with st.expander("⚙️ Modifier mes objectifs"):
    o1, o2 = st.columns(2)
    new_kcal = o1.number_input("Calories (kcal)", value=settings["objectif_kcal"], step=50, key="o_kcal")
    new_prot = o2.number_input("Protéines (g)", value=settings["objectif_prot"], step=5, key="o_prot")
    o3, o4 = st.columns(2)
    new_gluc = o3.number_input("Glucides (g)", value=settings["objectif_gluc"], step=10, key="o_gluc")
    new_lip  = o4.number_input("Lipides (g)", value=settings["objectif_lip"], step=5, key="o_lip")
    if st.button("💾 Sauvegarder"):
        settings = {"objectif_kcal": new_kcal, "objectif_prot": new_prot,
                    "objectif_gluc": new_gluc, "objectif_lip": new_lip}
        save_json(SETTINGS_FILE, settings)
        st.success("Objectifs mis à jour !")
        st.rerun()

# ── RESET DU JOUR ──────────────────────────────────────────────────────────────
st.markdown("---")
if st.button("🗑️ Effacer le journal du jour"):
    daily_log[today] = []
    save_json(LOG_FILE, daily_log)
    st.rerun()
