"""
Bot Telegram - Générateur de Dashboards Analytiques
====================================================
Ce bot permet aux utilisateurs de :
- Envoyer des fichiers de données (CSV, XLSX, ZIP)
- Générer des dashboards HTML automatiquement via OpenCode
- Recevoir le dashboard généré directement dans Telegram

Commandes disponibles :
/start - Message de bienvenue et instructions
/dashboard - Générer un dashboard à partir du fichier dans input/
/help - Afficher l'aide

Auteur : Dashboard Generator Team
Version : 1.0.0
"""

import asyncio
import logging
import os
import shutil
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# =============================================================================
# Configuration
# =============================================================================

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Constantes
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".zip"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 Mo
DASHBOARD_TIMEOUT = 300  # 5 minutes pour la génération
POLLING_INTERVAL = 5  # secondes entre les vérifications de fichier généré

# Récupérer le token et le répertoire
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DASHBOARD_DIR = os.getenv("DASHBOARD_DIR", "..")

# Résoudre les chemins absolus
BASE_DIR = Path(__file__).resolve().parent / DASHBOARD_DIR
BASE_DIR = BASE_DIR.resolve()
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"


# =============================================================================
# Gestionnaire d'état utilisateur
# =============================================================================


class UserState:
    """Gère l'état de chaque utilisateur pour le suivi des sessions."""

    def __init__(self):
        self.user_sessions: dict[int, dict] = {}

    def get_session(self, user_id: int) -> dict:
        """Récupère ou crée une session utilisateur."""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                "last_file": None,
                "last_generation": None,
                "is_generating": False,
            }
        return self.user_sessions[user_id]

    def clear_session(self, user_id: int) -> None:
        """Supprime la session d'un utilisateur."""
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]


# Instance globale du gestionnaire d'état
user_state_manager = UserState()


# =============================================================================
# Fonctions utilitaires
# =============================================================================


def validate_file_extension(filename: str) -> bool:
    """Vérifie si l'extension du fichier est autorisée.

    Args:
        filename: Nom du fichier à vérifier

    Returns:
        True si l'extension est autorisée, False sinon
    """
    if not filename:
        return False
    # Protection contre path traversal
    safe_name = Path(filename).name
    if safe_name != filename:
        logger.warning("Tentative de path traversal détectée: %s", filename)
        return False
    extension = Path(filename).suffix.lower()
    return extension in ALLOWED_EXTENSIONS


def get_allowed_extensions_message() -> str:
    """Retourne la liste des extensions autorisées formatée."""
    return ", ".join(sorted(ALLOWED_EXTENSIONS))


def format_file_size(size_bytes: int) -> str:
    """Formate une taille de fichier en unité lisible.

    Args:
        size_bytes: Taille en octets

    Returns:
        Taille formatée (ex: "2,5 Mo")
    """
    if size_bytes < 1024:
        return f"{size_bytes} o"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} Ko"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} Mo"


def ensure_directories() -> bool:
    """Crée les répertoires input/ et output/ s'ils n'existent pas.

    Returns:
        True si les répertoires existent ou ont été créés, False sinon
    """
    try:
        INPUT_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as error:
        logger.error("Impossible de créer les répertoires : %s", error)
        return False


def find_latest_dashboard() -> Optional[Path]:
    """Trouve le fichier HTML le plus récent dans le répertoire output/.

    Returns:
        Chemin du fichier HTML le plus récent, ou None si aucun fichier trouvé
    """
    if not OUTPUT_DIR.exists():
        return None

    html_files = list(OUTPUT_DIR.glob("*.html"))
    if not html_files:
        return None

    return max(html_files, key=lambda f: f.stat().st_mtime)


def cleanup_old_dashboards(keep_count: int = 5) -> int:
    """Supprime les anciens dashboards en gardant les N plus récents.

    Args:
        keep_count: Nombre de dashboards à conserver

    Returns:
        Nombre de fichiers supprimés
    """
    if not OUTPUT_DIR.exists():
        return 0

    html_files = sorted(
        OUTPUT_DIR.glob("*.html"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )

    files_to_delete = html_files[keep_count:]
    deleted_count = 0

    for file_path in files_to_delete:
        try:
            file_path.unlink()
            deleted_count += 1
            logger.info("Ancien dashboard supprimé : %s", file_path.name)
        except OSError as error:
            logger.warning("Impossible de supprimer %s : %s", file_path.name, error)

    return deleted_count


def generate_opencode_command(filename: str) -> list[str]:
    """Génère la commande opencode avec contexte du fichier.

    Args:
        filename: Nom du fichier source à analyser

    Returns:
        Liste des arguments de la commande
    """
    prompt = (
        f"Génère un dashboard à partir du fichier input/{filename}. "
        f"Analyse les données, identifie le domaine, calcule les KPIs, "
        f"crée les visualisations adaptées et génère un HTML autonome dans output/."
    )
    return [
        "opencode",
        "--prompt",
        prompt,
    ]


# =============================================================================
# Gestionnaires de commandes
# =============================================================================


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gère la commande /start - Message de bienvenue.

    Affiche les instructions d'utilisation et les commandes disponibles.
    """
    if update.message is None:
        return

    user_name = update.effective_user.first_name or "Utilisateur"

    welcome_message = (
        f"👋 Bienvenue, {user_name} !\n\n"
        f"📊 *Générateur de Dashboards Analytiques*\n\n"
        f"Je peux transformer vos fichiers de données en dashboards "
        f"professionnels automatiquement.\n\n"
        f"*Comment utiliser ce bot :*\n"
        f"1️⃣ Envoyez-moi un fichier de données (CSV, Excel ou ZIP)\n"
        f"2️⃣ Tapez /dashboard pour générer le dashboard\n"
        f"3️⃣ Recevez votre dashboard HTML directement ici\n\n"
        f"*Formats supportés :*\n"
        f"📄 CSV (.csv)\n"
        f"📊 Excel (.xlsx, .xls)\n"
        f"📦 ZIP (.zip)\n\n"
        f"*Commandes disponibles :*\n"
        f"/start - Message de bienvenue\n"
        f"/dashboard - Générer un dashboard\n"
        f"/help - Afficher cette aide\n\n"
        f"📁 *Répertoire actif :* `{BASE_DIR}`"
    )

    await update.message.reply_text(
        welcome_message,
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )

    logger.info("Commande /start exécutée par l'utilisateur %d", update.effective_user.id)


async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gère la commande /help - Affiche l'aide détaillée."""
    if update.message is None:
        return

    help_message = (
        f"📖 *Aide - Générateur de Dashboards*\n\n"
        f"*Étape 1 : Envoyer un fichier*\n"
        f"Envoyez simplement votre fichier de données dans cette conversation.\n"
        f"Formats acceptés : {get_allowed_extensions_message()}\n"
        f"Taille maximale : {format_file_size(MAX_FILE_SIZE)}\n\n"
        f"*Étape 2 : Générer le dashboard*\n"
        f"Tapez /dashboard pour lancer la génération.\n"
        f"Le processus prend généralement 1 à 3 minutes.\n\n"
        f"*Étape 3 : Recevoir le résultat*\n"
        f"Le dashboard HTML vous sera envoyé automatiquement.\n"
        f"Vous pourrez l'ouvrir dans votre navigateur.\n\n"
        f"*⚠️ Notes importantes :*\n"
        f"• Un seul fichier à la fois dans le dossier input/\n"
        f"• Le fichier précédent sera remplacé\n"
        f"• Les dashboards anciens sont nettoyés automatiquement\n"
        f"• En cas d'erreur, un message détaillé vous sera envoyé"
    )

    await update.message.reply_text(help_message, parse_mode="Markdown")

    logger.info("Commande /help exécutée par l'utilisateur %d", update.effective_user.id)


async def handle_dashboard_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Gère la commande /dashboard - Lance la génération du dashboard.

    Vérifie qu'un fichier est présent dans input/, exécute opencode,
    surveille la génération et envoie le fichier HTML résultant.
    """
    if update.message is None:
        return

    user_id = update.effective_user.id
    session = user_state_manager.get_session(user_id)

    # Vérifier si une génération est déjà en cours
    if session["is_generating"]:
        await update.message.reply_text(
            "⏳ Une génération est déjà en cours. Veuillez patienter..."
        )
        return

    # Vérifier les répertoires
    if not ensure_directories():
        await update.message.reply_text(
            "❌ Erreur : Impossible d'accéder aux répertoires de travail."
        )
        return

    # Vérifier la présence d'un fichier dans input/
    input_files = list(INPUT_DIR.iterdir()) if INPUT_DIR.exists() else []
    if not input_files:
        await update.message.reply_text(
            "❌ Aucun fichier trouvé dans le dossier input/.\n\n"
            "Veuillez d'abord m'envoyer un fichier de données "
            "(CSV, Excel ou ZIP)."
        )
        return

    # Filtrer les fichiers valides
    valid_files = [
        f
        for f in input_files
        if f.is_file() and validate_file_extension(f.name)
    ]
    if not valid_files:
        await update.message.reply_text(
            "❌ Aucun fichier valide trouvé dans input/.\n"
            f"Extensions acceptées : {get_allowed_extensions_message()}"
        )
        return

    # Utiliser le fichier le plus récent
    latest_file = max(valid_files, key=lambda f: f.stat().st_mtime)
    logger.info(
        "Génération demandée par l'utilisateur %d avec le fichier %s",
        user_id,
        latest_file.name,
    )

    # Marquer la session comme en cours de génération
    session["is_generating"] = True

    try:
        # Message de démarrage
        progress_message = await update.message.reply_text(
            f"🚀 *Génération en cours...*\n\n"
            f"📁 Fichier : `{latest_file.name}`\n"
            f"📊 Analyse des données en cours...\n\n"
            f"⏱️ Cela peut prendre quelques minutes."
        )

        # Exécuter la commande opencode
        start_time = time.time()
        dashboard_file = await run_dashboard_generation(
            latest_file.name, progress_message, context
        )

        if dashboard_file is None:
            await progress_message.edit_text(
                "❌ *Échec de la génération*\n\n"
                "Le dashboard n'a pas pu être généré.\n"
                "Vérifiez que :\n"
                "• Le fichier de données est valide\n"
                "• OpenCode est installé et configuré\n"
                "• Les dépendances Python sont installées\n\n"
                f"⏱️ Temps écoulé : {time.time() - start_time:.0f}s"
            )
            return

        # Envoyer le fichier généré
        await progress_message.edit_text(
            f"✅ *Dashboard généré avec succès !*\n\n"
            f"📄 Fichier : `{dashboard_file.name}`\n"
            f"📏 Taille : {format_file_size(dashboard_file.stat().st_size)}\n"
            f"⏱️ Temps de génération : {time.time() - start_time:.0f}s\n\n"
            f"📥 Envoi du fichier..."
        )

        # Vérifier la taille du fichier avant envoi
        MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB (limite Telegram)
        file_size = dashboard_file.stat().st_size
        if file_size > MAX_FILE_SIZE:
            logger.error("Fichier trop volumineux: %d octets", file_size)
            return None

        # Envoyer le fichier HTML
        with open(dashboard_file, "rb") as file_handle:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=file_handle,
                filename=dashboard_file.name,
                caption=(
                    f"📊 Votre dashboard est prêt !\n\n"
                    f"Ouvrez ce fichier HTML dans votre navigateur pour "
                    f"visualiser l'analyse complète.\n\n"
                    f"💡 *Astuce :* Vous pouvez envoyer un nouveau fichier "
                    f"et taper /dashboard pour en générer un autre."
                ),
                parse_mode="Markdown",
            )

        # Nettoyer les anciens fichiers
        deleted = cleanup_old_dashboards()
        if deleted > 0:
            logger.info("%d anciens dashboards supprimés", deleted)

        # Mettre à jour la session
        session["last_generation"] = datetime.now().isoformat()
        session["last_file"] = latest_file.name

    except subprocess.TimeoutExpired:
        await update.message.reply_text(
            "⏱️ *Délai d'attente dépassé*\n\n"
            "La génération a pris trop de temps (> 5 minutes).\n"
            "Vérifiez la taille de votre fichier et réessayez."
        )
    except Exception as error:
        logger.error(
            "Erreur lors de la génération pour l'utilisateur %d : %s",
            user_id,
            error,
            exc_info=True,
        )
        await update.message.reply_text(
            f"❌ *Erreur inattendue*\n\n"
            f"Une erreur s'est produite : `{error}`\n\n"
            f"Veuillez réessayer ou contacter l'administrateur."
        )
    finally:
        session["is_generating"] = False


async def run_dashboard_generation(
    filename: str, progress_message, context: ContextTypes.DEFAULT_TYPE
) -> Optional[Path]:
    """Exécute la génération du dashboard via opencode.

    Args:
        filename: Nom du fichier source à analyser
        progress_message: Message Telegram à mettre à jour avec la progression
        context: Contexte du bot Telegram

    Returns:
        Chemin du fichier HTML généré, ou None en cas d'échec
    """
    # Enregistrer le dashboard actuel avant génération
    dashboard_before = find_latest_dashboard()

    # Construire la commande
    command = generate_opencode_command(filename)
    logger.info("Exécution de la commande : %s", " ".join(command))

    # Exécuter opencode dans le répertoire du dashboard
    process = await asyncio.create_subprocess_exec(
        *command,
        cwd=str(BASE_DIR),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    # Attendre la fin avec timeout
    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(), timeout=DASHBOARD_TIMEOUT
        )

        stdout_output = stdout.decode("utf-8", errors="replace") if stdout else ""
        stderr_output = stderr.decode("utf-8", errors="replace") if stderr else ""
        if process.returncode != 0:
            logger.error("OpenCode erreur (code %d) - stdout: %s, stderr: %s",
                         process.returncode, stdout_output[:500], stderr_output[:500])
            return None
        else:
            logger.info("OpenCode terminé - stdout: %s", stdout_output[:200] if stdout_output else "(vide)")

    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        raise

    # Polling pour détecter le nouveau dashboard (max 30 secondes)
    for attempt in range(30):
        await asyncio.sleep(1)
        dashboard_after = find_latest_dashboard()
        if dashboard_after and (dashboard_before is None or dashboard_after != dashboard_before):
            logger.info("Dashboard détecté après %d secondes", attempt + 1)
            return dashboard_after
    logger.warning("Aucun nouveau dashboard détecté après 30 secondes")
    return None


async def handle_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gère l'upload de fichiers - Sauvegarde dans le dossier input/.

    Accepte les fichiers CSV, XLSX, XLS et ZIP.
    Remplace tout fichier existant dans input/.
    """
    if update.message is None or update.message.document is None:
        return

    user_id = update.effective_user.id
    document = update.message.document
    filename = document.file_name or "fichier_sans_nom"

    # Vérifier l'extension
    if not validate_file_extension(filename):
        await update.message.reply_text(
            f"❌ *Format de fichier non supporté*\n\n"
            f"Le fichier `{filename}` n'est pas dans un format accepté.\n\n"
            f"*Formats acceptés :*\n"
            f"{get_allowed_extensions_message()}"
        )
        return

    # Vérifier la taille
    if document.file_size and document.file_size > MAX_FILE_SIZE:
        await update.message.reply_text(
            f"❌ *Fichier trop volumineux*\n\n"
            f"Taille : {format_file_size(document.file_size)}\n"
            f"Maximum : {format_file_size(MAX_FILE_SIZE)}\n\n"
            f"Veuillez réduire la taille de votre fichier."
        )
        return

    # Vérifier les répertoires
    if not ensure_directories():
        await update.message.reply_text(
            "❌ Erreur : Impossible d'accéder aux répertoires de travail."
        )
        return

    # Nettoyer les fichiers existants dans input/
    try:
        for existing_file in INPUT_DIR.iterdir():
            if existing_file.is_file():
                existing_file.unlink()
                logger.info("Ancien fichier supprimé : %s", existing_file.name)
    except OSError as error:
        logger.warning("Impossible de nettoyer input/ : %s", error)

    # Télécharger et sauvegarder le fichier
    try:
        # Créer un nom de fichier sécurisé
        safe_filename = Path(filename).name
        file_path = INPUT_DIR / safe_filename

        # Message de progression
        progress_msg = await update.message.reply_text(
            f"📥 *Réception du fichier...*\n\n"
            f"📄 Nom : `{safe_filename}`\n"
            f"📏 Taille : {format_file_size(document.file_size or 0)}"
        )

        # Télécharger le fichier
        file_info = await context.bot.get_file(document.file_id)
        await file_info.download_to_drive(str(file_path))

        # Vérifier que le fichier a été téléchargé
        if not file_path.exists():
            await progress_msg.edit_text(
                "❌ *Échec du téléchargement*\n\n"
                "Le fichier n'a pas pu être sauvegardé. Réessayez."
            )
            return

        # Mettre à jour la session
        session = user_state_manager.get_session(user_id)
        session["last_file"] = safe_filename

        # Message de succès
        await progress_msg.edit_text(
            f"✅ *Fichier reçu avec succès !*\n\n"
            f"📄 Nom : `{safe_filename}`\n"
            f"📏 Taille : {format_file_size(file_path.stat().st_size)}\n"
            f"📁 Destination : `input/{safe_filename}`\n\n"
            f"✨ Tapez /dashboard pour générer votre dashboard !"
        )

        logger.info(
            "Fichier %s reçu de l'utilisateur %d (%s)",
            safe_filename,
            user_id,
            format_file_size(file_path.stat().st_size),
        )

    except Exception as error:
        logger.error(
            "Erreur lors du téléchargement du fichier %s : %s",
            filename,
            error,
            exc_info=True,
        )
        await update.message.reply_text(
            f"❌ *Erreur lors du téléchargement*\n\n"
            f"Impossible de sauvegarder le fichier : `{error}`\n\n"
            f"Veuillez réessayer."
        )


async def handle_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gère les erreurs non capturées."""
    logger.error("Erreur non gérée : %s", context.error, exc_info=context.error)

    if not isinstance(update, Update):
        return

    update_obj: Update = update
    chat = update_obj.effective_chat
    if chat is None:
        return

    try:
        await context.bot.send_message(
            chat_id=chat.id,
            text=(
                "⚠️ *Une erreur inattendue s'est produite*\n\n"
                "Veuillez réessayer ou contacter l'administrateur "
                "si le problème persiste."
            ),
            parse_mode="Markdown",
        )
    except Exception:
        logger.error("Impossible d'envoyer le message d'erreur")


# =============================================================================
# Démarrage du bot
# =============================================================================


def main() -> None:
    """Point d'entrée principal du bot Telegram."""
    # Vérifier la configuration
    if not BOT_TOKEN:
        logger.error(
            "TELEGRAM_BOT_TOKEN n'est pas défini dans le fichier .env"
        )
        raise ValueError(
            "Le token du bot Telegram doit être défini dans le fichier .env"
        )

    logger.info("Démarrage du bot Dashboard Generator...")
    logger.info("Répertoire de travail : %s", BASE_DIR)
    logger.info("Token Telegram configuré (longueur: %d caractères)", len(BOT_TOKEN))

    # Vérifier les répertoires
    if not ensure_directories():
        logger.error("Impossible de créer les répertoires requis")
        raise RuntimeError("Répertoires input/ ou output/ inaccessibles")

    # Créer l'application
    application = Application.builder().token(BOT_TOKEN).build()

    # Enregistrer les gestionnaires de commandes
    application.add_handler(CommandHandler("start", handle_start))
    application.add_handler(CommandHandler("help", handle_help))
    application.add_handler(CommandHandler("dashboard", handle_dashboard_command))

    # Enregistrer le gestionnaire de fichiers
    application.add_handler(
        MessageHandler(filters.Document.ALL & ~filters.COMMAND, handle_file_upload)
    )

    # Enregistrer le gestionnaire d'erreurs
    application.add_error_handler(handle_error)

    # Démarrer le bot
    logger.info("Bot démarré - En attente de messages...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
