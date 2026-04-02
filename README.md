# 📊 Dashboard Generator — OpenCode + Oh-My-OpenCode

Génère automatiquement des **dashboards analytiques professionnels en HTML** à partir de n'importe quel fichier de données (CSV, Excel, ZIP), directement depuis votre terminal.

Fonctionne avec **tout type de données** : ventes, RH, publicité digitale, SEO, analytics web, support client, CRM…

---

## 🚀 Installation (Windows WSL)

### Option A — Installation automatique

```bash
# Télécharger et extraire le projet
cd ~
unzip seo-dashboard-opencode.zip
cd seo-dashboard-opencode

# Lancer l'installeur complet
bash setup.sh
```

### Option B — Installation manuelle

```bash
# 1. WSL (PowerShell Administrateur)
wsl --install

# 2. Dépendances (dans le terminal Ubuntu WSL)
sudo apt update && sudo apt install -y curl git unzip tmux python3 python3-pip
pip3 install --break-system-packages pandas openpyxl

# 3. Bun
curl -fsSL https://bun.sh/install | bash && source ~/.bashrc

# 4. OpenCode
curl -fsSL https://opencode.ai/install | bash && source ~/.bashrc

# 5. Oh-My-OpenCode
bunx oh-my-opencode install

# 6. Configurer un provider LLM
opencode    # puis taper /connect dans le TUI
```

---

## 🎯 Utilisation

### 1. Déposer votre fichier

```bash
cp /mnt/c/Users/VOUS/Downloads/mon-fichier.csv ~/seo-dashboard-opencode/input/
# ou .xlsx, .zip — tout est supporté
```

### 2. Générer le dashboard

```bash
cd ~/seo-dashboard-opencode

# Mode interactif (recommandé) — OpenCode lit AGENTS.md et sait quoi faire
opencode

# Mode direct (non-interactif)
opencode -p "Génère un dashboard à partir du fichier dans input/"

# Avec précisions
opencode -p "Analyse le fichier de ventes dans input/ pour le mois de mars, focus sur les KPIs de CA et panier moyen"
```

### 3. Ouvrir le résultat

```bash
explorer.exe output/dashboard*.html
```

---

## 📁 Structure du projet

```
dashboard-generator/
├── AGENTS.md              ← Instructions pour OpenCode (LE fichier clé)
├── opencode.json          ← Config OpenCode du projet
├── setup.sh               ← Installeur automatique WSL
├── scripts/
│   └── parse-data.py      ← Parseur universel (CSV/Excel/ZIP)
├── input/                 ← Déposer vos fichiers ici
└── output/                ← Dashboards générés ici
```

### Le fichier AGENTS.md

C'est le cerveau du système. Il contient :
- Le workflow complet d'analyse (6 étapes)
- Les règles de détection de domaine (ads, ventes, RH, SEO, analytics, support, CRM)
- Le design system (couleurs, composants, typographie)
- Les règles de génération des recommandations
- Les contraintes techniques (zéro CDN, SVG natif, français uniquement)

Quand vous lancez `opencode` dans ce dossier, il lit ce fichier et sait exactement comment transformer vos données en dashboard.

---

## 🔧 Commandes utiles

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

## 📋 Types de fichiers supportés

| Format | Extension | Notes |
|---|---|---|
| CSV | `.csv` | Séparateurs auto-détectés (`,` `;` `\t`) |
| Excel | `.xlsx`, `.xls` | Requiert pandas + openpyxl |
| ZIP | `.zip` | Extrait et analyse tous les CSV/Excel |

## 🏷️ Domaines auto-détectés

| Domaine | Signaux détectés | Exemple de fichier |
|---|---|---|
| Publicité digitale | CPC, CTR, Impressions, Conversions | Export Google Ads |
| Ventes / E-commerce | CA, Quantité, Produit, Catégorie | Export Shopify |
| RH | Salaire, Département, Évaluation | Fichier SIRH |
| Analytics Web | Sessions, Pages vues, Rebond | Export GA4 |
| Support client | Tickets, Satisfaction, SLA | Export Zendesk |
| CRM / B2B | Pipeline, Leads, Probabilité | Export Salesforce |
| SEO | Position, Requêtes, Impressions | Export Search Console |
