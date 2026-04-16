import streamlit as st
import json
import os
from datetime import date
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
    try:
        r = requests.get("https://world.openfoodfacts.org/cgi/search.pl", params={
            "search_terms":query,"search_simple":1,"action":"process","json":1,"page_size":5,"lc":"fr"
        }, timeout=8)
        results = []
        for p in r.json().get("products",[]):
            n = p.get("nutriments",{})
            name = p.get("product_name_fr") or p.get("product_name","")
            kcal = n.get("energy-kcal_100g") or n.get("energy_100g",0)
            if not name or not kcal: continue
            results.append({"name":name,"kcal":round(float(kcal),1),
                "proteines":round(float(n.get("proteins_100g") or 0),1),
                "glucides":round(float(n.get("carbohydrates_100g") or 0),1),
                "lipides":round(float(n.get("fat_100g") or 0),1),
                "fibres":round(float(n.get("fiber_100g") or 0),1),
                "source":"Open Food Facts"})
        return results
    except: return []

# ── LOAD STATE ────────────────────────────────────────────────────────────────
foods_db  = load_json(DB_FILE, DEFAULT_FOODS)
if not os.path.exists(DB_FILE): save_json(DB_FILE, foods_db)
daily_log = load_json(LOG_FILE, {})
settings  = load_json(SETTINGS_FILE, {"objectif_kcal":2000,"objectif_prot":150,"objectif_gluc":250,"objectif_lip":65})
meals_db  = load_json(MEALS_FILE, {})

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
tab1, tab2, tab3, tab4 = st.tabs(["➕ Aliment", "🍽️ Repas", "📋 Base", "⚙️ Réglages"])

# ═══════════════════════════════════════════════════
# TAB 1 — ALIMENT
# ═══════════════════════════════════════════════════
with tab1:
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

# ═══════════════════════════════════════════════════
# TAB 2 — REPAS
# ═══════════════════════════════════════════════════
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
                        st.warning(f"⚠️ {fname} absent de la base.")
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
                col_m, col_d = st.columns([5,1])
                with col_m:
                    items_str = ", ".join([f"{i['food']} ({i['grams']}g)" for i in mdata["items"]])
                    st.markdown(f"""
                    <div class="meal-card">
                        <div class="meal-name">{mname}</div>
                        <div class="meal-meta">{items_str}</div>
                    </div>""", unsafe_allow_html=True)
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
                    st.warning("Aucun résultat. Essaie un nom plus court ou ajoute manuellement.")
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
# TAB 4 — RÉGLAGES
# ═══════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-title">Objectifs journaliers</div>', unsafe_allow_html=True)
    o1, o2 = st.columns(2)
    new_kcal = o1.number_input("Calories (kcal)", value=settings["objectif_kcal"], step=50, key="o_kcal")
    new_prot = o2.number_input("Protéines (g)", value=settings["objectif_prot"], step=5, key="o_prot")
    o3, o4 = st.columns(2)
    new_gluc = o3.number_input("Glucides (g)", value=settings["objectif_gluc"], step=10, key="o_gluc")
    new_lip  = o4.number_input("Lipides (g)", value=settings["objectif_lip"], step=5, key="o_lip")
    if st.button("💾 Sauvegarder", key="btn_save_settings"):
        settings = {"objectif_kcal":new_kcal,"objectif_prot":new_prot,"objectif_gluc":new_gluc,"objectif_lip":new_lip}
        save_json(SETTINGS_FILE, settings)
        st.success("✅ Objectifs mis à jour !")
        st.rerun()
