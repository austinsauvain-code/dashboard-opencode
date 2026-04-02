# 🤖 Bot Telegram - Générateur de Dashboards Analytiques

Bot Telegram permettant de générer des dashboards HTML professionnels à partir de fichiers de données (CSV, Excel, ZIP), directement depuis une conversation Telegram.

---

## 📋 Prérequis

- Python 3.8 ou supérieur
- Un token de bot Telegram (obtenu via [@BotFather](https://t.me/BotFather))
- Le projet `seo-dashboard-opencode` configuré et fonctionnel
- OpenCode installé et configuré avec un provider LLM

---

## 🚀 Installation

### 1. Installer les dépendances Python

```bash
cd telegram-bot
pip install -r requirements.txt
```

Ou avec un environnement virtuel (recommandé) :

```bash
cd telegram-bot
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configurer le bot

Le fichier `.env` est déjà configuré avec le token du bot. Vérifiez les paramètres :

```bash
# Vérifier le contenu du fichier .env
cat .env

# S'assurer que le répertoire du dashboard est correct
# DASHBOARD_DIR=.. pointe vers le dossier parent (seo-dashboard-opencode)
```

### 3. Vérifier la configuration

```bash
# Vérifier que les répertoires input/ et output/ existent
ls ../input/
ls ../output/

# Vérifier qu'OpenCode est accessible
opencode --version
```

---

## 🎮 Utilisation

### Démarrer le bot

```bash
cd telegram-bot
python bot.py
```

Le bot se connecte à Telegram et commence à écouter les messages.

### Commandes disponibles

| Commande | Description |
|----------|-------------|
| `/start` | Message de bienvenue avec instructions |
| `/help` | Affiche l'aide détaillée |
| `/dashboard` | Génère un dashboard à partir du fichier dans `input/` |

### Workflow d'utilisation

1. **Envoyer un fichier** : Envoyez un fichier CSV, Excel ou ZIP directement dans la conversation
2. **Générer le dashboard** : Tapez `/dashboard` pour lancer la génération
3. **Recevoir le résultat** : Le bot vous envoie le fichier HTML généré

---

## 📁 Structure des fichiers

```
telegram-bot/
├── bot.py              ← Script principal du bot
├── requirements.txt    ← Dépendances Python
├── .env                ← Configuration (token, chemins)
├── .env.example        ← Exemple de configuration
├── README.md           ← Cette documentation
└── bot.log             ← Journal d'activité (généré automatiquement)
```

---

## ⚙️ Configuration

### Variables d'environnement

| Variable | Description | Valeur par défaut |
|----------|-------------|-------------------|
| `TELEGRAM_BOT_TOKEN` | Token du bot Telegram | Requis |
| `DASHBOARD_DIR` | Chemin relatif vers le dossier du dashboard | `..` |

### Formats de fichiers supportés

| Format | Extension | Taille max |
|--------|-----------|------------|
| CSV | `.csv` | 50 Mo |
| Excel | `.xlsx`, `.xls` | 50 Mo |
| ZIP | `.zip` | 50 Mo |

---

## 🔧 Dépannage

### Le bot ne démarre pas

**Symptôme** : Erreur `TELEGRAM_BOT_TOKEN n'est pas défini`

**Solution** :
```bash
# Vérifier que le fichier .env existe et contient le token
cat .env

# Vérifier le format du token (doit commencer par des chiffres)
grep TELEGRAM_BOT_TOKEN .env
```

### OpenCode n'est pas trouvé

**Symptôme** : Erreur `opencode: command not found`

**Solution** :
```bash
# Vérifier qu'OpenCode est installé
which opencode

# Si nécessaire, installer OpenCode
curl -fsSL https://opencode.ai/install | bash
```

### La génération échoue

**Symptôme** : Message "Échec de la génération"

**Solutions** :
1. Vérifier que le fichier dans `input/` est valide
2. Consulter le journal `bot.log` pour les détails d'erreur
3. Tester manuellement : `cd .. && opencode -p "Génère un dashboard..."`
4. Vérifier que les dépendances Python sont installées (`pandas`, `openpyxl`)

### Le fichier HTML n'est pas envoyé

**Symptôme** : La génération réussit mais aucun fichier n'est envoyé

**Solutions** :
1. Vérifier que le dossier `output/` contient des fichiers HTML
2. Vérifier les permissions d'écriture sur `output/`
3. Consulter `bot.log` pour les erreurs de lecture de fichier

### Problèmes de connexion Telegram

**Symptôme** : Le bot ne reçoit pas les messages

**Solutions** :
1. Vérifier la connexion internet
2. Vérifier que le token est valide sur [@BotFather](https://t.me/BotFather)
3. Redémarrer le bot

---

## 📊 Fonctionnalités

### Gestion des fichiers
- ✅ Validation des extensions (CSV, XLSX, XLS, ZIP)
- ✅ Limite de taille (50 Mo)
- ✅ Nettoyage automatique des anciens fichiers
- ✅ Sauvegarde dans le dossier `input/`

### Génération des dashboards
- ✅ Exécution automatique via OpenCode
- ✅ Messages de progression en temps réel
- ✅ Timeout de 5 minutes avec gestion d'erreur
- ✅ Détection automatique du fichier généré

### Gestion des utilisateurs
- ✅ Support multi-utilisateurs
- ✅ Sessions individuelles
- ✅ Prévention des générations simultanées
- ✅ Journalisation des activités

### Robustesse
- ✅ Gestion complète des erreurs
- ✅ Journalisation détaillée (`bot.log`)
- ✅ Nettoyage automatique des anciens dashboards
- ✅ Messages d'erreur explicites en français

---

## 🔒 Sécurité

- Le token du bot est stocké dans `.env` (jamais commité)
- Les fichiers uploadés sont validés (extension et taille)
- Les sessions utilisateur sont isolées
- Les anciens fichiers sont nettoyés automatiquement

---

## 📝 Notes

- Le bot fonctionne en mode polling (pas de webhook)
- Un seul fichier peut être généré à la fois par utilisateur
- Les dashboards anciens sont automatiquement supprimés (5 conservés)
- Tous les messages sont en français

---

## 🆘 Support

Pour toute question ou problème :
1. Consulter le fichier `bot.log` pour les détails d'erreur
2. Vérifier la configuration dans `.env`
3. Tester manuellement la génération avec OpenCode
