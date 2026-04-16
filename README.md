# 🔥 Macro Tracker

## Installation & lancement

```bash
# 1. Dans le dossier du projet
pip install -r requirements.txt

# 2. Lancer l'app
streamlit run app.py
```

L'app s'ouvre sur http://localhost:8501

## Fichiers générés automatiquement
- `foods_db.json` — ta base d'aliments (modifiable, persist)
- `daily_log.json` — ton journal quotidien par date
- `settings.json` — tes objectifs nutritionnels

## Fonctionnalités
- ✅ 9 aliments pré-chargés (valeurs Ciqual)
- ✅ Jauges de progression (kcal, prot, gluc, lip)
- ✅ Ajout par grammes avec preview en temps réel
- ✅ Suppression par entrée
- ✅ Recherche Open Food Facts (API gratuite, 2M+ produits)
- ✅ Ajout manuel avec sauvegarde permanente
- ✅ Objectifs personnalisables
