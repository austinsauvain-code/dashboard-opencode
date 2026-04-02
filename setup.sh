#!/bin/bash
# ============================================================
#  setup.sh — Installation complète OpenCode + Oh-My-OpenCode
#  Pour Windows WSL (Ubuntu)
# ============================================================

set -e
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  📊 Dashboard Generator — Setup                      ║"
echo "║  OpenCode + Oh-My-OpenCode sur WSL                  ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# --- Couleurs ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
fail() { echo -e "${RED}❌ $1${NC}"; }

# --- 1. Vérifier WSL ---
echo "🔍 Vérification de l'environnement..."
if grep -qEi "(Microsoft|WSL)" /proc/version &> /dev/null; then
    ok "WSL détecté"
else
    warn "Pas de WSL détecté — le script devrait quand même fonctionner sur Linux natif"
fi

# --- 2. Dépendances système ---
echo ""
echo "📦 Installation des dépendances système..."
sudo apt update -qq
sudo apt install -y -qq curl git unzip tmux python3 python3-pip > /dev/null 2>&1
ok "Dépendances système installées"

# --- 3. Bun ---
echo ""
echo "🍞 Installation de Bun..."
if command -v bun &> /dev/null; then
    ok "Bun déjà installé ($(bun --version))"
else
    curl -fsSL https://bun.sh/install | bash > /dev/null 2>&1
    export BUN_INSTALL="$HOME/.bun"
    export PATH="$BUN_INSTALL/bin:$PATH"
    ok "Bun installé"
fi

# --- 4. OpenCode ---
echo ""
echo "🖥️  Installation d'OpenCode..."
if command -v opencode &> /dev/null; then
    ok "OpenCode déjà installé ($(opencode --version 2>/dev/null || echo 'version inconnue'))"
else
    curl -fsSL https://opencode.ai/install | bash > /dev/null 2>&1
    ok "OpenCode installé"
fi

# --- 5. Oh-My-OpenCode ---
echo ""
echo "🔌 Installation d'Oh-My-OpenCode..."
echo "   (lancement de l'installeur interactif)"
echo ""
bunx oh-my-opencode install

# --- 6. Dossiers du projet ---
echo ""
echo "📁 Création des dossiers..."
mkdir -p input output
ok "Dossiers input/ et output/ créés"

# --- 7. Vérification ---
echo ""
echo "🩺 Diagnostic..."
bunx oh-my-opencode doctor 2>/dev/null || warn "Doctor a signalé des avertissements (voir ci-dessus)"

# --- 8. Raccourcis bash ---
echo ""
echo "⚡ Ajout des raccourcis bash..."
BASHRC="$HOME/.bashrc"

# Alias seo-dash
if ! grep -q "alias dash=" "$BASHRC" 2>/dev/null; then
    echo '' >> "$BASHRC"
    echo '# === Dashboard Generator ===' >> "$BASHRC"
    echo "alias dash='cd $(pwd) && opencode -p'" >> "$BASHRC"
    echo "alias parse-data='python3 $(pwd)/scripts/parse-data.py'" >> "$BASHRC"
    ok "Raccourcis ajoutés à ~/.bashrc"
    echo "   dash \"votre prompt\"       → lance OpenCode dans le projet"
    echo "   parse-data fichier.csv    → parse n'importe quel fichier en JSON"
else
    ok "Raccourcis déjà présents"
fi

# --- Fin ---
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  🎉 Installation terminée !                         ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "📋 Prochaines étapes :"
echo ""
echo "   1. Configurer votre provider LLM :"
echo "      opencode"
echo "      → taper /connect et suivre les instructions"
echo ""
echo "   2. Déposer n'importe quel fichier de données dans input/ :"
echo "      cp /mnt/c/Users/VOUS/Downloads/mon-fichier.csv input/"
echo "      (CSV, Excel .xlsx, ou ZIP — tout est supporté)"
echo ""
echo "   3. Générer un dashboard :"
echo "      opencode -p \"Génère un dashboard à partir du fichier dans input/\""
echo ""
echo "   4. Ouvrir le résultat :"
echo "      explorer.exe output/dashboard*.html"
echo ""
echo "   Rechargez votre terminal : source ~/.bashrc"
echo ""
