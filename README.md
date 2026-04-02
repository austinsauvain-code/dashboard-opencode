# 📊 Dashboard Generator — OpenCode + Oh-My-OpenCode

[![License: MIT](https://img.shields.io/badge/License-MIT-5046E5.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-8490A7)](#)
[![Status](https://img.shields.io/badge/Status-Stable-059669)](#)
[![Stars](https://img.shields.io/github/stars/raissartheau/seo-dashboard-opencode?style=social)](#)

> **Transformez n'importe quel fichier de données en dashboard analytique professionnel — directement depuis votre terminal.**

Un générateur de dashboards HTML autonomes, alimenté par l'IA via [OpenCode](https://opencode.ai). Zéro dépendance externe, zéro CDN, zéro configuration complexe. Déposez un CSV, Excel ou ZIP, lancez une commande, obtenez un rapport visuel complet avec KPIs, graphiques SVG et recommandations actionnables.

---

## 📑 Table des matières

- [✨ Fonctionnalités](#-fonctionnalités)
- [📸 Aperçu](#-aperçu)
- [⚡ Démarrage rapide](#-démarrage-rapide)
- [🔧 Comment ça marche](#-comment-ça-marche)
- [📋 Formats supportés](#-formats-supportés)
- [🏷️ Détection automatique de domaine](#️-détection-automatique-de-domaine)
- [🤖 Bot Telegram](#-bot-telegram)
- [📁 Structure du projet](#-structure-du-projet)
- [🛠️ Commandes utiles](#️-commandes-utiles)
- [🧠 Le fichier AGENTS.md](#-le-fichier-agentsmd)
- [🏗️ Stack technique](#️-stack-technique)
- [🤝 Contribuer](#-contribuer)
- [📜 Licence](#-licence)

---

## ✨ Fonctionnalités

### Core
- 📄 **Dashboard HTML autonome** — un seul fichier, tout est inline (HTML + CSS + JS)
- 📊 **Graphiques SVG natifs** — line charts, donuts, barres, scatter plots sans aucune librairie
- 🌙 **Mode sombre automatique** — via `prefers-color-scheme`
- 📱 **Responsive** — CSS Grid/Flexbox, du mobile au desktop
- 🇫🇷 **Interface 100% français** — nombres formatés `fr-FR`, vocabulaire adapté

### Data
- 🔍 **Détection automatique du domaine** — 7 domaines reconnus (ads, ventes, RH, SEO, analytics, support, CRM)
- 📈 **KPIs calculés** — Total, Moyenne, Min, Max, évolution vs période précédente
- 🎯 **Recommandations intelligentes** — anomalies détectées, priorisées, avec estimation d'impact
- 🛡️ **Gestion des cas limites** — fichiers vides, colonnes manquantes, volumes extrêmes

### Design
- 🎨 **Design system cohérent** — palette indigo/violet, cartes avec bordures colorées
- 🔤 **Typographie soignée** — Plus Jakarta Sans + JetBrains Mono
- 📐 **6 sections structurées** — Header, Tabs, KPIs, Graphiques, Tableau, Recommandations

### Telegram
- 💬 **Bot Telegram intégré** — générez des dashboards depuis vos messages
- 📎 **Envoi de fichiers** — déposez un CSV/XLSX directement dans le chat

---

## 📸 Aperçu

> **📷 À capturer pour illustrer le README :**
> 1. **Vue d'ensemble** — Dashboard complet avec header, KPIs et grille de graphiques
> 2. **Onglet Recommandations** — Jauge de santé + cartes priorisées avec bordures colorées
> 3. **Mode sombre** — Capture du même dashboard en dark mode
> 4. **Mobile** — Capture responsive sur écran étroit
> 5. **Bot Telegram** — Capture d'un échange avec le bot (envoi fichier → réception dashboard)

---

## ⚡ Démarrage rapide

### Installation (WSL / Linux)

```bash
# Option A — Installation automatique
bash setup.sh

# Option B — Installation manuelle
sudo apt update && sudo apt install -y curl git unzip python3 python3-pip
pip3 install pandas openpyxl
curl -fsSL https://bun.sh/install | bash
curl -fsSL https://opencode.ai/install | bash
bunx oh-my-opencode install
```

### Utiliser en CLI

```bash
# 1. Déposer un fichier
cp mon-export.csv input/

# 2. Générer le dashboard
opencode -p "Génère un dashboard à partir du fichier dans input/"

# 3. Ouvrir le résultat
explorer.exe output/dashboard*.html   # Windows
xdg-open output/dashboard*.html       # Linux
open output/dashboard*.html           # macOS
```

### Utiliser via Telegram

```bash
# 1. Configurer le bot
cp telegram-bot/.env.example telegram-bot/.env
# Éditer .env avec votre BOT_TOKEN Telegram

# 2. Lancer le bot
cd telegram-bot
pip install -r requirements.txt
python bot.py

# 3. Envoyer un fichier CSV/XLSX dans le chat Telegram
#    → Le bot répond avec le dashboard généré
```

---

## 🔧 Comment ça marche

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────────┐
│  1. Déposez  │────▶│  2. Analysez  │────▶│  3. Visualisez       │
│  votre CSV   │     │  avec OpenCode│     │  Dashboard HTML      │
│  dans input/ │     │  (IA locale)  │     │  dans output/        │
└─────────────┘     └──────────────┘     └─────────────────────┘
```

1. **Déposez** un fichier `.csv`, `.xlsx` ou `.zip` dans le dossier `input/`
2. **Lancez** OpenCode — il lit `AGENTS.md`, analyse vos données et calcule les KPIs
3. **Ouvrez** le fichier HTML généré dans `output/` — tout est autonome, aucun serveur requis

---

## 📋 Formats supportés

| Format | Extension | Notes |
|---|---|---|
| CSV | `.csv` | Séparateurs auto-détectés (`,` `;` `\t`) |
| Excel | `.xlsx`, `.xls` | Requiert `pandas` + `openpyxl` |
| ZIP | `.zip` | Extrait et analyse tous les fichiers internes |

---

## 🏷️ Détection automatique de domaine

Le système identifie le domaine métier en analysant les noms de colonnes :

| Domaine | Signaux détectés | Vocabulaire utilisé |
|---|---|---|
| 📢 Publicité digitale | CPC, CTR, Impressions, Conversions | ROAS, CPA, enchères, audiences |
| 🛒 Ventes / E-commerce | CA, Quantité, Produit, Catégorie | Marge, panier moyen, cross-sell |
| 👥 Ressources Humaines | Salaire, Département, Évaluation | Rétention, équité salariale, GPEC |
| 🌐 Analytics Web | Sessions, Pages vues, Rebond, Sources | UX, parcours, entonnoir |
| 🎧 Support client | Tickets, Résolution, Satisfaction, SLA | SLA, escalade, CSAT |
| 🤝 CRM / B2B | Leads, Pipeline, Étape, Probabilité | Pipeline, win rate, nurturing |
| 🔍 SEO | Position, Requêtes, Clics, Impressions | Snippet, hreflang, méta-données |

---

## 🤖 Bot Telegram

Le projet inclut un bot Telegram pour générer des dashboards depuis une conversation.

### Commandes

| Commande | Description |
|---|---|
| `/start` | Message d'accueil et instructions |
| `/help` | Liste des commandes et formats supportés |
| `/status` | État du système et fichiers en attente |

### Utilisation

1. Envoyez un fichier `.csv`, `.xlsx` ou `.zip` directement dans le chat
2. Le bot analyse le fichier et génère le dashboard
3. Il vous renvoie le fichier HTML prêt à être ouvert

### Configuration

```bash
cd telegram-bot
cp .env.example .env
# Renseigner BOT_TOKEN dans .env
python bot.py
```

> ⚠️ Ne jamais commiter le fichier `.env` — il est dans `.gitignore`.

---

## 📁 Structure du projet

```
dashboard-generator/
├── AGENTS.md              ← Cerveau du système (instructions IA)
├── opencode.json          ← Configuration OpenCode
├── setup.sh               ← Installeur automatique WSL/Linux
├── scripts/
│   └── parse-data.py      ← Parseur universel CSV/Excel/ZIP
├── telegram-bot/
│   ├── bot.py             ← Bot Telegram
│   ├── requirements.txt   ← Dépendances Python
│   └── .env.example       ← Template de configuration
├── input/                 ← Déposez vos fichiers ici
└── output/                ← Dashboards générés ici
```

### Le fichier AGENTS.md

C'est le cerveau du système. Il contient :

- Le workflow complet d'analyse en 6 étapes
- Les règles de détection de domaine (7 domaines)
- Le design system (couleurs, composants, typographie)
- Les règles de génération des recommandations
- Les contraintes techniques (zéro CDN, SVG natif, français uniquement)

Quand vous lancez `opencode` dans ce dossier, il lit ce fichier et sait exactement comment transformer vos données en dashboard.

---

## 🛠️ Commandes utiles

```bash
# Parser un fichier sans générer le dashboard (JSON brut)
python3 scripts/parse-data.py input/fichier.csv --output output/analyse.json --pretty

# Parser un mois spécifique
python3 scripts/parse-data.py input/export.zip --mois mars --output output/analyse.json

# Parser une feuille Excel spécifique
python3 scripts/parse-data.py input/rapport.xlsx --sheet "Q1 2026" --output output/analyse.json

# Raccourcis bash (ajoutés par setup.sh)
dash "Génère un dashboard pour le fichier dans input/"
parse-data input/fichier.csv
```

---

## 🏗️ Stack technique

| Couche | Technologie |
|---|---|
| **Moteur IA** | [OpenCode](https://opencode.ai) + [Oh-My-OpenCode](https://github.com/oh-my-opencode) |
| **LLM** | Anthropic Claude (configurable) |
| **Parseur de données** | Python 3 + pandas + openpyxl |
| **Génération HTML** | JavaScript natif (inline) |
| **Graphiques** | SVG natif + CSS pur (zéro librairie) |
| **Bot** | Python + `python-telegram-bot` |
| **Runtime** | Bun (installation, utilitaires) |
| **Platforme** | WSL / Linux / macOS |

---

## 🤝 Contribuer

1. Forkez le projet
2. Créez une branche (`git checkout -b feature/ma-fonctionnalite`)
3. Committez vos changements (`git commit -m 'Ajout: ma fonctionnalité'`)
4. Poussez (`git push origin feature/ma-fonctionnalite`)
5. Ouvrez une Pull Request

Les contributions les plus utiles : nouveaux types de graphiques, support de formats additionnels, améliorations du bot Telegram.

---

## 📜 Licence

Distribué sous licence **MIT**. Voir [`LICENSE`](LICENSE) pour plus d'informations.

---

<p align="center">
  <em>Dashboard Generator — Propulsé par OpenCode & Oh-My-OpenCode</em>
</p>
