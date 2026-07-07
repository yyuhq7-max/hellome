import discord
from discord.ext import commands
from discord.ext import tasks
from discord import app_commands
import os
import json
import re
import datetime
import random
import asyncio
import threading
import io
import urllib.parse
import aiohttp
from http.server import BaseHTTPRequestHandler, HTTPServer

CONFIG_FILE = "config.json"

# Fonctions pour gérer la configuration persistante du bot
def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

# Table de couleurs réutilisable pour toutes les commandes à embed
COLOR_MAP = {
    "bleu": discord.Color.blue(),
    "vert": discord.Color.green(),
    "rouge": discord.Color.red(),
    "violet": discord.Color.purple(),
    "or": discord.Color.gold(),
    "gris": discord.Color.light_grey(),
    "blurple": discord.Color.blurple(),
    "noir": discord.Color.dark_theme() if hasattr(discord.Color, "dark_theme") else discord.Color.default(),
    "blanc": discord.Color.from_rgb(255, 255, 255),
}

COLOR_CHOICES = [
    app_commands.Choice(name="Bleu", value="bleu"),
    app_commands.Choice(name="Vert", value="vert"),
    app_commands.Choice(name="Rouge", value="rouge"),
    app_commands.Choice(name="Violet", value="violet"),
    app_commands.Choice(name="Or", value="or"),
    app_commands.Choice(name="Gris", value="gris")
]


def parse_color(value: str) -> discord.Color:
    """Convertit une saisie utilisateur (nom de couleur ou code hexadécimal) en discord.Color.
    Retourne discord.Color.blurple() par défaut si la valeur est vide ou invalide."""
    if not value:
        return discord.Color.blurple()

    value = value.strip().lower()

    # Nom de couleur connu (bleu, vert, rouge, etc.)
    if value in COLOR_MAP:
        return COLOR_MAP[value]

    # Code hexadécimal (#RRGGBB ou RRGGBB)
    hex_value = value.lstrip("#")
    if len(hex_value) == 6:
        try:
            return discord.Color(int(hex_value, 16))
        except ValueError:
            pass

    # Valeur non reconnue -> couleur par défaut
    return discord.Color.blurple()


def parse_emoji(value: str):
    """Retourne l'emoji saisi par l'utilisateur, ou None si le champ est vide/invalide."""
    if value and value.strip():
        return value.strip()
    return None


# Conditions Générales d'Utilisation (CGU) / Terms of Service (TOS) du serveur MVP
RULES = {
    "fr": (
        "📜 **CONDITIONS GÉNÉRALES D'UTILISATION - MVP** 📜\n\n"
        "🚚 **Livraison**\n"
        "• Un produit est considéré comme livré dès que les informations d'accès ont été fournies à l'acheteur.\n"
        "• Si un produit n'est pas livré dans un délai raisonnable (jusqu'à 24 heures), il sera remplacé.\n\n"
        "💳 **Paiements**\n"
        "• Tous les paiements doivent être effectués pour le montant exact correspondant au produit sélectionné.\n"
        "• Tout paiement incomplet ou incorrect sera considéré comme un don et ne sera pas remboursé.\n"
        "• Aucun remboursement n'est effectué en aucune circonstance. La seule forme de compensation est un bon d'achat d'une valeur équivalente au paiement effectué.\n\n"
        "🛡️ **Garantie**\n"
        "• Tous les produits sont couverts par une garantie de 24 heures.\n"
        "• Veuillez noter que vous n'êtes éligible à la couverture de la garantie qu'après avoir laissé un avis pour votre achat.\n\n"
        "🔄 **Remplacements**\n"
        "• Les produits achetés sur MVP sont éligibles au remplacement tant qu'ils restent disponibles sur la plateforme.\n"
        "• Un remplacement est accordé dans les cas suivants :\n"
        "  - Identifiants incorrects\n"
        "  - Le compte ne dispose pas de l'abonnement acheté\n"
        "  - Le problème est survenu pendant la période de garantie\n"
        "  - Le compte ne correspond pas à sa description\n"
        "• Toute demande de remplacement doit être accompagnée de preuves valides démontrant le problème (par exemple, une capture d'écran claire ou une vidéo).\n"
        "• Toutes les demandes sont soumises à vérification et à la disponibilité du produit.\n"
        "• MVP se réserve le droit de refuser un remplacement en cas de mauvaise utilisation, de modification du compte, de partage avec des tiers ou de toute modification non autorisée des identifiants fournis.\n\n"
        "⚠️ **Responsabilité**\n"
        "• MVP n'est pas responsable si un produit ne fonctionne pas dans le pays ou la région de l'acheteur.\n"
        "• Nous ne sommes pas non plus responsables des actions de tiers, y compris les révocations de comptes, les restrictions régionales ou les changements de politique des fournisseurs externes.\n\n"
        "✍️ **Modifications**\n"
        "• MVP se réserve le droit de modifier ces Conditions Générales d'Utilisation à tout moment, sans préavis."
    ),
    "en": (
        "📜 **TERMS OF SERVICE - MVP** 📜\n\n"
        "🚚 **Delivery**\n"
        "• A product is considered delivered as soon as the login/access details have been provided to the buyer.\n"
        "• If a product is not delivered within a reasonable timeframe (up to 24 hours), it will be replaced.\n\n"
        "💳 **Payments**\n"
        "• All payments must be made for the exact amount corresponding to the selected product.\n"
        "• Any incomplete or incorrect payment will be considered a donation and will not be refunded.\n"
        "• No refunds are given under any circumstances. The only form of compensation is a store credit of equivalent value to the payment made.\n\n"
        "🛡️ **Warranty**\n"
        "• All products are covered by a 24-hour warranty.\n"
        "• Please note that you are only eligible for warranty coverage after leaving a review for your purchase.\n\n"
        "🔄 **Replacements**\n"
        "• Products purchased on MVP are eligible for replacement as long as they remain available on the platform.\n"
        "• A replacement is granted in the following cases:\n"
        "  - Incorrect credentials\n"
        "  - The account does not have the purchased subscription\n"
        "  - The issue occurred during the warranty period\n"
        "  - The account does not match its description\n"
        "• Any replacement request must be accompanied by valid proof demonstrating the issue (for example, a clear screenshot or video).\n"
        "• All requests are subject to verification and product availability.\n"
        "• MVP reserves the right to refuse a replacement in case of misuse, account modification, sharing with third parties, or any unauthorized modification of the provided credentials.\n\n"
        "⚠️ **Liability**\n"
        "• MVP is not responsible if a product does not work in the buyer's country or region.\n"
        "• We are also not responsible for the actions of third parties, including account revocations, regional restrictions, or policy changes by external providers.\n\n"
        "✍️ **Modifications**\n"
        "• MVP reserves the right to modify these Terms of Service at any time, without prior notice."
    ),
    "es": (
        "📜 **TÉRMINOS DE SERVICIO - MVP** 📜\n\n"
        "🚚 **Entrega**\n"
        "• Un producto se considera entregado tan pronto como se proporcionen los datos de acceso al comprador.\n"
        "• Si un producto no se entrega dentro de un plazo razonable (hasta 24 horas), será reemplazado.\n\n"
        "💳 **Pagos**\n"
        "• Todos los pagos deben realizarse por el monto exacto correspondiente al producto seleccionado.\n"
        "• Cualquier pago incompleto o incorrecto se considerará una donación y no será reembolsado.\n"
        "• No se realizan reembolsos bajo ninguna circunstancia. La única forma de compensación es un cupón de compra de valor equivalente al pago realizado.\n\n"
        "🛡️ **Garantía**\n"
        "• Todos los productos están cubiertos por una garantía de 24 horas.\n"
        "• Tenga en cuenta que solo es elegible para la cobertura de la garantía después de dejar una reseña sobre su compra.\n\n"
        "🔄 **Reemplazos**\n"
        "• Los productos comprados en MVP son elegibles para reemplazo siempre que sigan disponibles en la plataforma.\n"
        "• Se concede un reemplazo en los siguientes casos:\n"
        "  - Credenciales incorrectas\n"
        "  - La cuenta no dispone de la suscripción comprada\n"
        "  - El problema ocurrió durante el período de garantía\n"
        "  - La cuenta no coincide con su descripción\n"
        "• Cualquier solicitud de reemplazo debe ir acompañada de pruebas válidas que demuestren el problema (por ejemplo, una captura de pantalla clara o un video).\n"
        "• Todas las solicitudes están sujetas a verificación y disponibilidad del producto.\n"
        "• MVP se reserva el derecho de rechazar un reemplazo en caso de mal uso, modificación de la cuenta, uso compartido con terceros o cualquier modificación no autorizada de las credenciales proporcionadas.\n\n"
        "⚠️ **Responsabilidad**\n"
        "• MVP no se hace responsable si un producto no funciona en el país o región del comprador.\n"
        "• Tampoco nos hacemos responsables de las acciones de terceros, incluidas las revocaciones de cuentas, restricciones regionales o cambios de política de proveedores externos.\n\n"
        "✍️ **Modificaciones**\n"
        "• MVP se reserva el derecho de modificar estos Términos de Servicio en cualquier momento, sin previo aviso."
    ),
    "de": (
        "📜 **NUTZUNGSBEDINGUNGEN - MVP** 📜\n\n"
        "🚚 **Lieferung**\n"
        "• Ein Produkt gilt als geliefert, sobald die Zugangsdaten dem Käufer bereitgestellt wurden.\n"
        "• Wenn ein Produkt nicht innerhalb einer angemessenen Frist (bis zu 24 Stunden) geliefert wird, wird es ersetzt.\n\n"
        "💳 **Zahlungen**\n"
        "• Alle Zahlungen müssen in der genauen Höhe des ausgewählten Produkts erfolgen.\n"
        "• Jede unvollständige oder fehlerhafte Zahlung wird als Spende betrachtet und nicht zurückerstattet.\n"
        "• Unter keinen Umständen werden Rückerstattungen gewährt. Die einzige Form der Entschädigung ist ein Einkaufsgutschein im gleichen Wert der geleisteten Zahlung.\n\n"
        "🛡️ **Garantie**\n"
        "• Alle Produkte sind durch eine 24-stündige Garantie abgedeckt.\n"
        "• Bitte beachten Sie, dass Sie erst nach Abgabe einer Bewertung für Ihren Kauf Anspruch auf Garantieleistungen haben.\n\n"
        "🔄 **Ersatz**\n"
        "• Auf MVP erworbene Produkte können ersetzt werden, solange sie auf der Plattform verfügbar sind.\n"
        "• Ein Ersatz wird in folgenden Fällen gewährt:\n"
        "  - Falsche Zugangsdaten\n"
        "  - Das Konto verfügt nicht über das gekaufte Abonnement\n"
        "  - Das Problem ist während der Garantiezeit aufgetreten\n"
        "  - Das Konto entspricht nicht der Beschreibung\n"
        "• Jeder Ersatzantrag muss von gültigen Beweisen begleitet sein, die das Problem belegen (z. B. ein klarer Screenshot oder ein Video).\n"
        "• Alle Anträge unterliegen der Überprüfung und der Verfügbarkeit des Produkts.\n"
        "• MVP behält sich das Recht vor, einen Ersatz im Falle von Missbrauch, Kontoänderungen, Weitergabe an Dritte oder unbefugten Änderungen der bereitgestellten Zugangsdaten abzulehnen.\n\n"
        "⚠️ **Haftung**\n"
        "• MVP ist nicht verantwortlich, wenn ein Produkt im Land oder der Region des Käufers nicht funktioniert.\n"
        "• Wir sind auch nicht verantwortlich für die Handlungen Dritter, einschließlich Kontosperrungen, regionaler Einschränkungen oder Richtlinienänderungen externer Anbieter.\n"
        "• MVP behält sich das Recht vor, diese Nutzungsbedingungen jederzeit und ohne Vorankündigung zu ändern."
    )
}

# --- Composants UI pour la sélection de langue ---
class LanguageSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Français", 
                description="Lire les règles du serveur de revente MVP en Français", 
                emoji="🇫🇷", 
                value="fr"
            ),
            discord.SelectOption(
                label="English", 
                description="Read the MVP resell server rules in English", 
                emoji="🇬🇧", 
                value="en"
            ),
            discord.SelectOption(
                label="Español", 
                description="Leer las règles du serveur de revente MVP en Español", 
                emoji="🇪🇸", 
                value="es"
            ),
            discord.SelectOption(
                label="Deutsch", 
                description="Lesen Sie die MVP Resell-Server Regeln auf Deutsch", 
                emoji="🇩🇪", 
                value="de"
            )
        ]
        super().__init__(
            placeholder="Choisissez une langue / Choose a language...", 
            min_values=1, 
            max_values=1, 
            options=options, 
            custom_id="persistent_rules_select"
        )

    async def callback(self, interaction: discord.Interaction):
        selected_lang = self.values[0]
        rules_text = RULES.get(selected_lang, "Règles introuvables.")
        await interaction.response.send_message(rules_text, ephemeral=True)

class RulesView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(LanguageSelect())


# --- Composants UI pour la configuration de l'Autorole ---
class RoleSelect(discord.ui.RoleSelect):
    def __init__(self):
        super().__init__(
            placeholder="Sélectionnez le rôle automatique à attribuer...",
            min_values=1,
            max_values=1,
            custom_id="persistent_autorole_select"
        )

    async def callback(self, interaction: discord.Interaction):
        role = self.values[0]
        
        config = load_config()
        guild_id = str(interaction.guild.id)
        if guild_id not in config:
            config[guild_id] = {}
        config[guild_id]["autorole"] = role.id
        save_config(config)
        
        await interaction.response.send_message(
            f"✅ **Rôle automatique configuré** ! Les nouveaux membres recevront le rôle : **{role.name}**.", 
            ephemeral=True
        )

class AutoroleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RoleSelect())


# --- Modal et Composants pour la configuration du Rôle par Bouton (Self-Role) ---
# Cette modale permet une personnalisation complète : titre, description, couleur,
# texte du bouton et emoji du bouton.
class SelfRoleModal(discord.ui.Modal):
    def __init__(self, role_id: int):
        super().__init__(title="Configuration du Rôle par Bouton")
        self.role_id = role_id

        self.embed_titre = discord.ui.TextInput(
            label="Titre de l'embed",
            placeholder="Ex : Obtenir le rôle Notifications",
            required=False,
            max_length=100
        )
        self.embed_texte = discord.ui.TextInput(
            label="Description de l'embed",
            style=discord.TextStyle.paragraph,
            placeholder="Ex : Cliquez sur le bouton ci-dessous pour obtenir ce rôle.",
            required=False,
            max_length=1000
        )
        self.embed_couleur = discord.ui.TextInput(
            label="Couleur (nom ou hex, ex: bleu / #5865F2)",
            placeholder="bleu, vert, rouge, violet, or, gris ou #RRGGBB",
            required=False,
            max_length=20
        )
        self.bouton_texte = discord.ui.TextInput(
            label="Texte du bouton",
            placeholder="Ex : Obtenir le rôle",
            required=True,
            max_length=80
        )
        self.bouton_emoji = discord.ui.TextInput(
            label="Emoji du bouton (facultatif)",
            placeholder="Ex : 🎭 ou 🔔",
            required=False,
            max_length=50
        )
        self.add_item(self.embed_titre)
        self.add_item(self.embed_texte)
        self.add_item(self.embed_couleur)
        self.add_item(self.bouton_texte)
        self.add_item(self.bouton_emoji)

    async def on_submit(self, interaction: discord.Interaction):
        role = interaction.guild.get_role(self.role_id)
        if not role:
            await interaction.response.send_message("❌ Rôle introuvable.", ephemeral=True)
            return

        embed_color = parse_color(self.embed_couleur.value)
        button_emoji = parse_emoji(self.bouton_emoji.value)

        embed = discord.Embed(
            title=self.embed_titre.value if self.embed_titre.value else f"🎭 Rôle : {role.name}",
            description=self.embed_texte.value if self.embed_texte.value else "Cliquez sur le bouton ci-dessous pour obtenir ou retirer ce rôle.",
            color=embed_color
        )

        try:
            view = SelfRoleView(role.id, self.bouton_texte.value, button_emoji)
        except Exception:
            # Si l'emoji fourni est invalide, on retombe sur l'emoji par défaut
            view = SelfRoleView(role.id, self.bouton_texte.value, None)

        # Sauvegarde de la configuration pour pouvoir ré-enregistrer le bouton après un redémarrage
        config = load_config()
        guild_id = str(interaction.guild.id)
        if guild_id not in config:
            config[guild_id] = {}
        selfroles = config[guild_id].get("selfroles", [])
        # On évite les doublons pour un même rôle
        selfroles = [entry for entry in selfroles if entry.get("role_id") != role.id]
        selfroles.append({
            "role_id": role.id,
            "label": self.bouton_texte.value,
            "emoji": button_emoji
        })
        config[guild_id]["selfroles"] = selfroles
        save_config(config)

        await interaction.response.send_message("✅ Le bouton de rôle a été créé avec succès !", ephemeral=True)
        await interaction.channel.send(embed=embed, view=view)


class SelfRoleButton(discord.ui.Button):
    def __init__(self, role_id: int, label: str, emoji: str = None):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.primary,
            emoji=emoji if emoji else "🎭",
            custom_id=f"selfrole_{role_id}"
        )
        self.role_id = role_id

    async def callback(self, interaction: discord.Interaction):
        role = interaction.guild.get_role(self.role_id)
        if not role:
            await interaction.response.send_message("❌ Ce rôle n'existe plus.", ephemeral=True)
            return

        member = interaction.user
        try:
            if role in member.roles:
                await member.remove_roles(role)
                await interaction.response.send_message(f"➖ Le rôle **{role.name}** vous a été retiré.", ephemeral=True)
            else:
                await member.add_roles(role)
                await interaction.response.send_message(f"➕ Le rôle **{role.name}** vous a été attribué.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Permissions insuffisantes pour gérer ce rôle.", ephemeral=True)


class SelfRoleView(discord.ui.View):
    def __init__(self, role_id: int, label: str, emoji: str = None):
        super().__init__(timeout=None)
        self.add_item(SelfRoleButton(role_id, label, emoji))


class SelfRoleRoleSelect(discord.ui.RoleSelect):
    def __init__(self):
        super().__init__(
            placeholder="Sélectionnez le rôle à attribuer via le bouton...",
            min_values=1,
            max_values=1,
            custom_id="persistent_selfrole_role_select"
        )

    async def callback(self, interaction: discord.Interaction):
        role = self.values[0]
        # Ouvrir la modale pour personnaliser entièrement l'embed et le bouton
        await interaction.response.send_modal(SelfRoleModal(role.id))


class SelfRoleConfigView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelfRoleRoleSelect())


# --- Composants UI pour la configuration de l'Image Fixe (Sticky Image) ---
# Cette fonctionnalité permet de choisir un salon dans lequel une image reste
# toujours affichée tout en bas : dès qu'un nouveau message est envoyé par un
# membre, le bot supprime son précédent message-image puis le renvoie.
DEFAULT_STICKY_IMAGE_URL = "https://cdn.discordapp.com/emojis/1523827663742042182.png?size=4096"

# Cache mémoire simple {url: bytes} pour éviter de retélécharger l'image à chaque message
_sticky_image_bytes_cache = {}


def _guess_image_filename(url: str) -> str:
    """Déduit un nom de fichier (avec extension) à partir de l'URL de l'image."""
    path = urllib.parse.urlparse(url).path
    ext = os.path.splitext(path)[1].lower()
    if ext not in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
        ext = ".png"
    return f"image{ext}"


async def get_sticky_image_file(image_url: str):
    """Télécharge (ou récupère depuis le cache) les octets de l'image et retourne
    un discord.File prêt à être joint à un message. Un vrai fichier joint s'affiche
    en GRAND format dans Discord, contrairement à un simple lien ou un embed."""
    data = _sticky_image_bytes_cache.get(image_url)
    if data is None:
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                if resp.status != 200:
                    return None
                data = await resp.read()
        _sticky_image_bytes_cache[image_url] = data

    filename = _guess_image_filename(image_url)
    return discord.File(io.BytesIO(data), filename=filename)


class StickyImageModal(discord.ui.Modal):
    def __init__(self, channel_id: int):
        super().__init__(title="Configuration de l'Image Fixe")
        self.channel_id = channel_id

        self.image_url = discord.ui.TextInput(
            label="URL de l'image à maintenir en bas",
            placeholder="https://cdn.discordapp.com/emojis/....png",
            default=DEFAULT_STICKY_IMAGE_URL,
            required=True,
            max_length=300
        )
        self.add_item(self.image_url)

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(self.channel_id)
        if not channel:
            await interaction.response.send_message("❌ Le salon sélectionné est introuvable.", ephemeral=True)
            return

        config = load_config()
        guild_id = str(interaction.guild.id)
        if guild_id not in config:
            config[guild_id] = {}
        sticky_images = config[guild_id].get("sticky_images", {})
        sticky_images[str(self.channel_id)] = {
            "image_url": self.image_url.value.strip(),
            "last_message_id": None
        }
        config[guild_id]["sticky_images"] = sticky_images
        save_config(config)

        await interaction.response.send_message(
            f"✅ **Image fixe configurée** pour {channel.mention} ! "
            "Elle restera désormais tout en bas de ce salon après chaque nouveau message.",
            ephemeral=True
        )

        # On envoie immédiatement une première fois l'image pour initialiser le système
        # (fichier joint téléchargé puis réuploadé => s'affiche en GRAND format,
        # sans bordure colorée, contrairement à un lien ou à un embed)
        try:
            image_file = await get_sticky_image_file(self.image_url.value.strip())
            if image_file:
                new_message = await channel.send(file=image_file)
                sticky_images[str(self.channel_id)]["last_message_id"] = new_message.id
                config[guild_id]["sticky_images"] = sticky_images
                save_config(config)
        except discord.Forbidden:
            pass


class StickyImageChannelSelect(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(
            placeholder="Sélectionnez le salon où garder l'image en bas...",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
            custom_id="persistent_stickyimage_channel_select"
        )

    async def callback(self, interaction: discord.Interaction):
        channel = self.values[0]
        await interaction.response.send_modal(StickyImageModal(channel.id))


class StickyImageView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(StickyImageChannelSelect())


class StickyImageResetSelect(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(
            placeholder="Sélectionnez le salon à réinitialiser...",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
            custom_id="persistent_stickyimage_reset_select"
        )

    async def callback(self, interaction: discord.Interaction):
        channel = self.values[0]

        config = load_config()
        guild_id = str(interaction.guild.id)
        sticky_images = config.get(guild_id, {}).get("sticky_images", {})
        channel_key = str(channel.id)

        if channel_key not in sticky_images:
            await interaction.response.send_message(
                f"❌ Aucune image fixe n'est configurée pour {channel.mention}.",
                ephemeral=True
            )
            return

        entry = sticky_images.pop(channel_key)
        config[guild_id]["sticky_images"] = sticky_images
        save_config(config)

        # Suppression du dernier message-image encore présent dans le salon, si possible
        old_message_id = entry.get("last_message_id")
        if old_message_id:
            try:
                old_message = await channel.fetch_message(old_message_id)
                await old_message.delete()
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass

        await interaction.response.send_message(
            f"✅ **Image fixe réinitialisée** pour {channel.mention} ! Le système est désormais désactivé sur ce salon.",
            ephemeral=True
        )


class StickyImageResetView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(StickyImageResetSelect())


# --- Dashboard de configuration central (/setup) ---
class SetupDashboardSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Rôle Automatique (Autorole)",
                value="autorole",
                emoji="👤",
                description="Attribuer un rôle par défaut aux nouveaux membres."
            ),
            discord.SelectOption(
                label="Rôle par Bouton (Self-Role)",
                value="selfrole",
                emoji="🎭",
                description="Créer un bouton permettant d'obtenir un rôle."
            ),
            discord.SelectOption(
                label="Image Fixe (Bas de salon)",
                value="stickyimage",
                emoji="🖼️",
                description="Garder une image toujours affichée en bas d'un salon."
            ),
            discord.SelectOption(
                label="Réinitialiser Image Fixe",
                value="stickyimage_reset",
                emoji="🗑️",
                description="Désactiver le système d'image fixe sur un salon."
            ),
        ]
        super().__init__(
            placeholder="Choisissez le service à configurer...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="persistent_setup_dashboard_select"
        )

    async def callback(self, interaction: discord.Interaction):
        choice = self.values[0]

        if choice == "autorole":
            embed = discord.Embed(
                title="👤 Configuration de l'Autorole",
                description="Choisissez dans le menu déroulant ci-dessous le rôle à attribuer automatiquement aux nouveaux membres dès leur arrivée.",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed, view=AutoroleView(), ephemeral=True)

        elif choice == "selfrole":
            embed = discord.Embed(
                title="🎭 Créer un Rôle par Bouton",
                description="Sélectionnez le rôle que les membres pourront obtenir (ou retirer) en cliquant sur un bouton.\n\n"
                            "Vous pourrez ensuite personnaliser entièrement :\n"
                            "• Le **titre** de l'embed\n"
                            "• La **description** de l'embed\n"
                            "• La **couleur** de l'embed\n"
                            "• Le **texte** du bouton\n"
                            "• L'**emoji** du bouton",
                color=discord.Color.blurple()
            )
            await interaction.response.send_message(embed=embed, view=SelfRoleConfigView(), ephemeral=True)

        elif choice == "stickyimage":
            embed = discord.Embed(
                title="🖼️ Configuration de l'Image Fixe",
                description="Sélectionnez le salon dans lequel une image doit toujours rester tout en bas.\n\n"
                            "Dès qu'un membre enverra un nouveau message dans ce salon, le bot supprimera "
                            "automatiquement son précédent message-image puis le renverra, pour que l'image "
                            "soit toujours le dernier message du salon.",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, view=StickyImageView(), ephemeral=True)

        elif choice == "stickyimage_reset":
            config = load_config()
            guild_id = str(interaction.guild.id)
            sticky_images = config.get(guild_id, {}).get("sticky_images", {})

            if sticky_images:
                lines = []
                for channel_id in sticky_images:
                    channel = interaction.guild.get_channel(int(channel_id))
                    lines.append(channel.mention if channel else f"❌ Salon introuvable (`{channel_id}`)")
                channels_txt = "\n".join(lines)
            else:
                channels_txt = "Aucun salon n'a actuellement d'image fixe configurée."

            embed = discord.Embed(
                title="🗑️ Réinitialisation de l'Image Fixe",
                description="Sélectionnez le salon pour lequel vous souhaitez **désactiver** le système d'image fixe.\n\n"
                            "Cela supprime la configuration ainsi que le dernier message-image encore présent dans ce salon.",
                color=discord.Color.red()
            )
            embed.add_field(name="📋 Salons actuellement configurés", value=channels_txt, inline=False)
            await interaction.response.send_message(embed=embed, view=StickyImageResetView(), ephemeral=True)


class SetupDashboardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SetupDashboardSelect())


# ==================== SYSTÈME DE GIVEAWAYS ====================
# Un giveaway est défini par : un prix, une durée (en jours), un nombre de
# gagnants, et une condition de participation basée sur le système de suivi
# des invitations déjà présent dans le bot (invite_counts). Les membres
# rejoignent via un bouton persistant ; le tirage au sort est automatique
# une fois la durée écoulée (vérifié périodiquement par une tâche de fond).

def get_giveaways(guild_id: str) -> list:
    config = load_config()
    return config.get(guild_id, {}).get("giveaways", [])


def get_giveaway(guild_id: str, giveaway_id: int):
    for gw in get_giveaways(guild_id):
        if gw.get("id") == giveaway_id:
            return gw
    return None


def get_next_giveaway_id(guild_id: str) -> int:
    giveaways = get_giveaways(guild_id)
    return max((g.get("id", 0) for g in giveaways), default=0) + 1


def build_giveaway_embed(prize, winners_count, required_invites, end_timestamp, host,
                          participants_count=0, color=None, ended=False, winners_mentions=None):
    embed = discord.Embed(
        title="🎉 GIVEAWAY 🎉" if not ended else "🎉 GIVEAWAY TERMINÉ 🎉",
        description=(
            f"**Prix :** {prize}\n\n"
            + ("Cliquez sur le bouton **Participer 🎉** ci-dessous pour tenter votre chance !\n\n"
               if not ended else "Ce giveaway est maintenant terminé.\n\n")
            + f"⏳ **Fin :** <t:{int(end_timestamp)}:R> (<t:{int(end_timestamp)}:F>)"
        ),
        color=color or discord.Color.gold()
    )
    embed.add_field(name="🏆 Nombre de gagnants", value=str(winners_count), inline=True)
    condition_text = f"{required_invites} invitation(s) minimum" if required_invites > 0 else "Aucune condition"
    embed.add_field(name="📋 Condition", value=condition_text, inline=True)
    embed.add_field(name="👥 Participants", value=str(participants_count), inline=True)
    if ended:
        embed.add_field(
            name="🏆 Gagnant(s)",
            value=winners_mentions if winners_mentions else "Aucun participant éligible.",
            inline=False
        )
    embed.set_footer(
        text=f"Giveaway organisé par {host.display_name}",
        icon_url=host.display_avatar.url if host.display_avatar else None
    )
    return embed


class GiveawayJoinButton(discord.ui.Button):
    def __init__(self, guild_id: int, giveaway_id: int):
        super().__init__(
            label="Participer 🎉",
            style=discord.ButtonStyle.success,
            custom_id=f"giveaway_join_{guild_id}_{giveaway_id}"
        )
        self.guild_id = guild_id
        self.giveaway_id = giveaway_id

    async def callback(self, interaction: discord.Interaction):
        guild_id = str(self.guild_id)
        config = load_config()
        gw = get_giveaway(guild_id, self.giveaway_id)

        if not gw:
            await interaction.response.send_message("❌ Ce giveaway n'existe plus.", ephemeral=True)
            return

        if gw.get("ended"):
            await interaction.response.send_message("❌ Ce giveaway est déjà terminé.", ephemeral=True)
            return

        required = gw.get("required_invites", 0)
        if required > 0:
            invite_data = get_invite_data(config, guild_id)
            user_invites = invite_data["invite_counts"].get(str(interaction.user.id), 0)
            if user_invites < required:
                await interaction.response.send_message(
                    f"❌ Vous devez avoir invité au moins **{required}** membre(s) pour participer à ce giveaway.\n"
                    f"Vous avez actuellement **{user_invites}** invitation(s) validée(s).",
                    ephemeral=True
                )
                return

        participants = gw.get("participants", [])
        user_id = interaction.user.id

        if user_id in participants:
            participants.remove(user_id)
            action_text = "❌ Vous avez retiré votre participation à ce giveaway."
        else:
            participants.append(user_id)
            action_text = "🎉 Votre participation a été enregistrée !"

        gw["participants"] = participants
        giveaways = config.get(guild_id, {}).get("giveaways", [])
        giveaways = [gw if g.get("id") == self.giveaway_id else g for g in giveaways]
        if guild_id not in config:
            config[guild_id] = {}
        config[guild_id]["giveaways"] = giveaways
        save_config(config)

        await interaction.response.send_message(action_text, ephemeral=True)

        # Mise à jour du nombre de participants affiché dans l'embed public
        try:
            embed = interaction.message.embeds[0]
            for i, field in enumerate(embed.fields):
                if field.name == "👥 Participants":
                    embed.set_field_at(i, name="👥 Participants", value=str(len(participants)), inline=True)
                    break
            await interaction.message.edit(embed=embed)
        except (IndexError, discord.HTTPException):
            pass


class GiveawayView(discord.ui.View):
    def __init__(self, guild_id: int, giveaway_id: int):
        super().__init__(timeout=None)
        self.add_item(GiveawayJoinButton(guild_id, giveaway_id))


async def end_giveaway(guild_id: int, giveaway_id: int, forced_winners: list = None):
    """Tire au sort (ou applique le(s) gagnant(s) prédéfini(s)) pour un giveaway
    terminé, met à jour le message public et annonce le(s) gagnant(s) dans le salon.

    - Si `forced_winners` est explicitement fourni (liste d'IDs), ces membres sont
      utilisés directement.
    - Sinon, si le giveaway possède des gagnants prédéfinis via /setwinnerg
      (clé "forced_winners" enregistrée dans sa configuration), ce sont ceux-là
      qui sont utilisés automatiquement à la fin du giveaway.
    - Sinon, un tirage au sort classique est effectué parmi les participants
      éligibles (la condition d'invitations est revérifiée à ce moment-là, au
      cas où un participant aurait perdu des invitations entre-temps)."""
    guild_key = str(guild_id)
    config = load_config()
    giveaways = config.get(guild_key, {}).get("giveaways", [])
    gw = next((g for g in giveaways if g.get("id") == giveaway_id), None)
    if not gw or gw.get("ended"):
        return

    if forced_winners is None:
        forced_winners = gw.get("forced_winners")

    if forced_winners:
        winners = forced_winners
    else:
        invite_data = get_invite_data(config, guild_key)
        required = gw.get("required_invites", 0)

        eligible = []
        for user_id in gw.get("participants", []):
            if required > 0 and invite_data["invite_counts"].get(str(user_id), 0) < required:
                continue
            eligible.append(user_id)

        winners_count = gw.get("winners_count", 1)
        winners = random.sample(eligible, min(winners_count, len(eligible))) if eligible else []

    gw["ended"] = True
    gw["winners"] = winners
    giveaways = [gw if g.get("id") == giveaway_id else g for g in giveaways]
    config[guild_key]["giveaways"] = giveaways
    save_config(config)

    guild = bot.get_guild(guild_id)
    if not guild:
        return

    channel = guild.get_channel(gw.get("channel_id"))
    winners_mentions = " ".join(f"<@{uid}>" for uid in winners) if winners else None
    host = guild.get_member(gw.get("host_id")) or guild.me

    embed = build_giveaway_embed(
        prize=gw["prize"],
        winners_count=gw["winners_count"],
        required_invites=gw.get("required_invites", 0),
        end_timestamp=gw["end_timestamp"],
        host=host,
        participants_count=len(gw.get("participants", [])),
        color=COLOR_MAP.get(gw.get("color", "or"), discord.Color.gold()),
        ended=True,
        winners_mentions=winners_mentions
    )

    if channel:
        try:
            message = await channel.fetch_message(gw["message_id"])
            disabled_view = discord.ui.View()
            disabled_view.add_item(
                discord.ui.Button(label="Giveaway terminé", style=discord.ButtonStyle.secondary, disabled=True)
            )
            await message.edit(embed=embed, view=disabled_view)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass

        try:
            if winners:
                await channel.send(f"🎉 Félicitations {winners_mentions} ! Vous avez remporté **{gw['prize']}** !")
            else:
                await channel.send(
                    f"😢 Aucun participant éligible n'a été trouvé pour le giveaway **{gw['prize']}**. "
                    "Aucun gagnant n'a été tiré au sort."
                )
        except discord.HTTPException:
            pass


# --- Composants UI pour la commande /setwinnerg (définir manuellement le(s) gagnant(s)) ---
class SetWinnerGiveawaySelect(discord.ui.Select):
    def __init__(self, guild_id: int, giveaways: list):
        self.guild_id = guild_id
        options = [
            discord.SelectOption(
                label=f"#{gw['id']} - {gw['prize']}"[:100],
                value=str(gw["id"]),
                description=f"{len(gw.get('participants', []))} participant(s) - {gw.get('winners_count', 1)} gagnant(s) à définir"[:100],
                emoji="🎉"
            )
            for gw in giveaways
        ]
        super().__init__(
            placeholder="Choisissez le giveaway en cours...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        giveaway_id = int(self.values[0])
        gw = get_giveaway(str(self.guild_id), giveaway_id)

        if not gw or gw.get("ended"):
            await interaction.response.edit_message(
                content="❌ Ce giveaway n'existe plus ou est déjà terminé.",
                embed=None,
                view=None
            )
            return

        winners_count = gw.get("winners_count", 1)
        existing_forced = gw.get("forced_winners") or []
        current_txt = (
            "\n\n📌 **Gagnant(s) actuellement prévu(s) :** " + " ".join(f"<@{uid}>" for uid in existing_forced)
            if existing_forced else ""
        )
        embed = discord.Embed(
            title=f"🏆 Définir le(s) gagnant(s) - Giveaway #{giveaway_id}",
            description=(
                f"**Prix :** {gw['prize']}\n\n"
                f"Sélectionnez ci-dessous jusqu'à **{winners_count}** membre(s) qui remporteront ce giveaway.\n\n"
                "⚠️ Le giveaway **ne sera pas clôturé maintenant**. Les membres sélectionnés seront simplement "
                "prévus comme gagnants et seront automatiquement déclarés vainqueurs (sans vérification de la "
                "condition d'invitations) au moment où le giveaway se terminera normalement."
                + current_txt
            ),
            color=discord.Color.gold()
        )
        await interaction.response.edit_message(
            content=None,
            embed=embed,
            view=SetWinnerUserSelectView(self.guild_id, giveaway_id, winners_count)
        )


class SetWinnerGiveawaySelectView(discord.ui.View):
    def __init__(self, guild_id: int, giveaways: list):
        super().__init__(timeout=300)
        self.add_item(SetWinnerGiveawaySelect(guild_id, giveaways))


class SetWinnerUserSelect(discord.ui.UserSelect):
    def __init__(self, guild_id: int, giveaway_id: int, winners_count: int):
        self.guild_id = guild_id
        self.giveaway_id = giveaway_id
        super().__init__(
            placeholder="Sélectionnez le(s) gagnant(s)...",
            min_values=1,
            max_values=max(1, min(winners_count, 25))
        )

    async def callback(self, interaction: discord.Interaction):
        winners = [user.id for user in self.values]

        await interaction.response.defer(ephemeral=True)

        config = load_config()
        guild_key = str(self.guild_id)
        gw = get_giveaway(guild_key, self.giveaway_id)
        if not gw or gw.get("ended"):
            await interaction.followup.send("❌ Ce giveaway n'existe plus ou est déjà terminé.", ephemeral=True)
            return

        # On enregistre simplement les gagnants prévus : le giveaway continue de
        # tourner normalement (les membres peuvent toujours participer/se retirer)
        # et sera clôturé automatiquement à la date de fin prévue par la tâche de
        # fond, en utilisant ce(s) gagnant(s) prédéfini(s) au lieu d'un tirage au sort.
        gw["forced_winners"] = winners
        giveaways = config.get(guild_key, {}).get("giveaways", [])
        giveaways = [gw if g.get("id") == self.giveaway_id else g for g in giveaways]
        config[guild_key]["giveaways"] = giveaways
        save_config(config)

        winners_mentions = " ".join(f"<@{uid}>" for uid in winners)
        await interaction.followup.send(
            f"✅ Le(s) gagnant(s) du giveaway **{gw['prize']}** ont été prévus : {winners_mentions}\n"
            "Le giveaway continue normalement et sera automatiquement clôturé à sa date de fin, "
            "avec ce(s) gagnant(s) prédéfini(s) (sans tirage au sort ni vérification de la condition d'invitations).",
            ephemeral=True
        )


class SetWinnerUserSelectView(discord.ui.View):
    def __init__(self, guild_id: int, giveaway_id: int, winners_count: int):
        super().__init__(timeout=300)
        self.add_item(SetWinnerUserSelect(guild_id, giveaway_id, winners_count))


@tasks.loop(seconds=30)
async def giveaway_checker():
    config = load_config()
    now = datetime.datetime.now(datetime.timezone.utc).timestamp()
    for guild_id, guild_config in config.items():
        for gw in guild_config.get("giveaways", []):
            if not gw.get("ended") and gw.get("end_timestamp", 0) <= now:
                try:
                    await end_giveaway(int(guild_id), gw["id"])
                except Exception as e:
                    print(f"⚠️ Giveaway : erreur lors de la fin du giveaway {gw.get('id')} sur {guild_id} : {e}")


@giveaway_checker.before_loop
async def before_giveaway_checker():
    await bot.wait_until_ready()


# --- Classe principale du Bot ---
class RulesBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.invites = True  # Nécessaire pour les événements on_invite_create / on_invite_delete (invite tracker)
        super().__init__(command_prefix="!", intents=intents)
        # Cache des invitations par serveur : {guild_id: {code: uses}}
        self.invite_cache = {}

    async def setup_hook(self):
        # Ré-enregistrement des vues persistantes pour éviter de les perdre aux reboots
        self.add_view(RulesView())
        self.add_view(AutoroleView())
        self.add_view(SetupDashboardView())
        self.add_view(SelfRoleConfigView())
        self.add_view(StickyImageView())
        self.add_view(StickyImageResetView())

        # Ré-enregistrement de tous les boutons de rôle déjà configurés
        config = load_config()
        for guild_id, guild_config in config.items():
            for entry in guild_config.get("selfroles", []):
                self.add_view(SelfRoleView(entry["role_id"], entry["label"], entry.get("emoji")))

        # Ré-enregistrement des giveaways encore actifs (non terminés)
        for guild_id, guild_config in config.items():
            for gw in guild_config.get("giveaways", []):
                if not gw.get("ended"):
                    self.add_view(GiveawayView(int(guild_id), gw["id"]))

        # Système de tickets : vue générique de fermeture + panels déjà publiés

        # Migration : les anciennes configs stockaient un seul panel sous
        # "ticket_panel". On les convertit en liste "ticket_panels" (avec un id).
        migrated = False
        for guild_id, guild_config in config.items():
            if "ticket_panel" in guild_config and "ticket_panels" not in guild_config:
                old_panel = guild_config.pop("ticket_panel")
                old_panel["id"] = 1
                old_panel.setdefault("support_role_ids", [])
                if "support_role_id" in old_panel:
                    role_id = old_panel.pop("support_role_id")
                    if role_id:
                        old_panel["support_role_ids"] = [role_id]
                old_panel.setdefault("panel_message_id", None)
                guild_config["ticket_panels"] = [old_panel]
                migrated = True
        if migrated:
            save_config(config)

        self.add_view(TicketActionView())
        for guild_id, guild_config in config.items():
            for panel in guild_config.get("ticket_panels", []):
                self.add_view(TicketPanelView(int(guild_id), panel["id"]))

        # Ré-enregistrement des panels regroupés (un seul message avec plusieurs boutons)
        for guild_id, guild_config in config.items():
            for group in guild_config.get("ticket_group_panels", []):
                self.add_view(GroupTicketPanelView(int(guild_id), group["id"]))

        # Synchronisation globale des commandes slash
        await self.tree.sync()

bot = RulesBot()


# --- Événements du Bot ---
@bot.event
async def on_ready():
    print(f"✅ Bot connecté avec succès en tant que {bot.user.name}")

    # Mise en cache des invitations existantes pour chaque serveur (invite tracker)
    for guild in bot.guilds:
        try:
            invites = await guild.invites()
            bot.invite_cache[guild.id] = {invite.code: invite.uses for invite in invites}
        except discord.Forbidden:
            bot.invite_cache[guild.id] = {}
            print(f"⚠️ Invite tracker : permissions insuffisantes pour lire les invitations sur {guild.name}.")

    # Démarrage de la tâche de fond qui termine automatiquement les giveaways expirés
    if not giveaway_checker.is_running():
        giveaway_checker.start()

    print("Prêt et synchronisé !")

@bot.event
async def on_member_join(member: discord.Member):
    # Rôle automatique
    config = load_config()
    guild_id = str(member.guild.id)
    if guild_id in config and "autorole" in config[guild_id]:
        role_id = config[guild_id]["autorole"]
        role = member.guild.get_role(role_id)
        if role:
            try:
                await member.add_roles(role)
                print(f"✅ Autorole : Rôle {role.name} attribué à {member.name} à l'arrivée.")
            except discord.Forbidden:
                print(f"❌ Autorole : Impossible d'attribuer le rôle {role.name} à {member.name} (permissions insuffisantes).")

    # --- Invite tracker : détection de l'invitation utilisée ---
    try:
        await track_invite_on_join(member)
    except Exception as e:
        print(f"⚠️ Invite tracker : erreur lors du suivi de l'invitation pour {member.name} : {e}")

@bot.event
async def on_invite_create(invite: discord.Invite):
    # Nouvelle invitation créée : on l'ajoute au cache avec 0 utilisation
    guild_cache = bot.invite_cache.setdefault(invite.guild.id, {})
    guild_cache[invite.code] = invite.uses

@bot.event
async def on_invite_delete(invite: discord.Invite):
    # Invitation supprimée : on la retire du cache pour éviter les erreurs de calcul
    guild_cache = bot.invite_cache.get(invite.guild.id)
    if guild_cache and invite.code in guild_cache:
        del guild_cache[invite.code]


# --- Système d'Image Fixe (Sticky Image) ---
async def handle_sticky_image(message: discord.Message):
    """Si le salon du message est configuré comme salon d'image fixe, supprime
    l'ancien message-image du bot puis renvoie l'image, pour qu'elle reste
    toujours tout en bas du salon."""
    if not message.guild:
        return

    config = load_config()
    guild_id = str(message.guild.id)
    sticky_images = config.get(guild_id, {}).get("sticky_images", {})
    channel_key = str(message.channel.id)

    if channel_key not in sticky_images:
        return

    entry = sticky_images[channel_key]
    image_url = entry.get("image_url")
    if not image_url:
        return

    # Suppression de l'ancien message-image, s'il existe encore
    old_message_id = entry.get("last_message_id")
    if old_message_id:
        try:
            old_message = await message.channel.fetch_message(old_message_id)
            await old_message.delete()
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass

    # Envoi de la nouvelle image en bas du salon
    # (fichier joint téléchargé puis réuploadé => s'affiche en GRAND format,
    # sans bordure colorée, contrairement à un lien ou à un embed)
    try:
        image_file = await get_sticky_image_file(image_url)
        if not image_file:
            return
        new_message = await message.channel.send(file=image_file)
    except discord.Forbidden:
        return

    entry["last_message_id"] = new_message.id
    sticky_images[channel_key] = entry
    config[guild_id]["sticky_images"] = sticky_images
    save_config(config)


@bot.event
async def on_message(message: discord.Message):
    # Ignorer les messages de bots pour éviter les boucles infinies
    # (cela inclut les propres messages-image renvoyés par le bot lui-même)
    if message.author.bot:
        return

    # Image Fixe : on gère ceci avant les commandes pour que ça s'applique
    # à tout message envoyé dans un salon configuré
    try:
        await handle_sticky_image(message)
    except Exception as e:
        print(f"⚠️ Image Fixe : erreur lors du traitement du message dans #{message.channel} : {e}")

    # Important : permet aux commandes slash et classiques de fonctionner
    await bot.process_commands(message)


# ==================== SYSTÈME DE SUIVI DES INVITATIONS (INVITE TRACKER) ====================

def get_invite_data(config: dict, guild_id: str) -> dict:
    """Retourne (et initialise si besoin) le dictionnaire de suivi des invitations d'un serveur."""
    if guild_id not in config:
        config[guild_id] = {}
    config[guild_id].setdefault("invite_counts", {})   # {user_id: nombre_d_invitations}
    config[guild_id].setdefault("invited_by", {})      # {new_member_id: inviter_id}
    return config[guild_id]


async def track_invite_on_join(member: discord.Member):
    """Compare le cache d'invitations avant/après l'arrivée du membre pour déterminer
    qui l'a invité, puis met à jour le compteur d'invitations de l'inviteur."""
    guild = member.guild

    try:
        new_invites = await guild.invites()
    except discord.Forbidden:
        return

    old_cache = bot.invite_cache.get(guild.id, {})
    new_cache = {invite.code: invite.uses for invite in new_invites}

    used_invite = None
    for invite in new_invites:
        old_uses = old_cache.get(invite.code, 0)
        if invite.uses > old_uses:
            used_invite = invite
            break

    # Mise à jour du cache dans tous les cas, même si on n'a pas pu déterminer l'invitation utilisée
    # (par exemple : invitation à usage unique déjà consommée puis supprimée par Discord)
    bot.invite_cache[guild.id] = new_cache

    if used_invite is None or used_invite.inviter is None:
        return

    config = load_config()
    guild_id = str(guild.id)
    data = get_invite_data(config, guild_id)

    inviter_id = str(used_invite.inviter.id)
    data["invite_counts"][inviter_id] = data["invite_counts"].get(inviter_id, 0) + 1
    data["invited_by"][str(member.id)] = inviter_id
    save_config(config)


@bot.tree.command(name="invituser", description="Affiche le nombre d'invitations d'un membre.")
@app_commands.describe(membre="Le membre dont vous souhaitez voir les invitations (vous-même par défaut)")
async def invituser(interaction: discord.Interaction, membre: discord.Member = None):
    membre = membre or interaction.user

    config = load_config()
    guild_id = str(interaction.guild.id)
    data = get_invite_data(config, guild_id)
    save_config(config)

    count = data["invite_counts"].get(str(membre.id), 0)

    embed = discord.Embed(
        title="📨 Suivi des invitations",
        description=f"{membre.mention} a invité **{count}** membre(s) sur ce serveur.",
        color=discord.Color.blurple()
    )
    embed.set_thumbnail(url=membre.display_avatar.url)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="invitesleaderboard", description="Affiche le classement des membres ayant le plus invité sur le serveur.")
async def invitesleaderboard(interaction: discord.Interaction):
    config = load_config()
    guild_id = str(interaction.guild.id)
    data = get_invite_data(config, guild_id)
    save_config(config)

    counts = data["invite_counts"]
    if not counts:
        await interaction.response.send_message("❌ Aucune invitation n'a encore été enregistrée sur ce serveur.", ephemeral=True)
        return

    sorted_counts = sorted(counts.items(), key=lambda item: item[1], reverse=True)[:10]
    medals = ["🥇", "🥈", "🥉"]
    lines = []
    for i, (user_id, count) in enumerate(sorted_counts):
        prefix = medals[i] if i < len(medals) else f"**#{i + 1}**"
        lines.append(f"{prefix} <@{user_id}> — **{count}** invitation(s)")

    embed = discord.Embed(
        title="🏆 Classement des invitations",
        description="\n".join(lines),
        color=discord.Color.gold()
    )
    await interaction.response.send_message(embed=embed)


# --- Commandes d'Administration & Configuration ---
@bot.tree.command(name="setuprules", description="Affiche le panneau de sélection de langue pour les règles.")
@app_commands.describe(
    titre="Le titre de l'embed des règles (ex: Conditions d'utilisation)",
    description="La description ou message d'accueil de l'embed",
    couleur="Couleur de l'embed (options : bleu, vert, rouge, violet, or, gris)"
)
@app_commands.choices(couleur=COLOR_CHOICES)
async def setuprules(
    interaction: discord.Interaction,
    titre: str = "MVP Terms of Service / Server Rules",
    description: str = "Please select your preferred language below to read the MVP server rules.\n\nVeuillez sélectionner votre langue ci-dessous pour lire les règles du serveur MVP.",
    couleur: str = "bleu"
):
    embed_color = COLOR_MAP.get(couleur, discord.Color.blue())

    embed = discord.Embed(
        title=titre,
        description=description,
        color=embed_color
    )

    await interaction.response.send_message("✅ Le panneau des règles a été généré avec succès !", ephemeral=True)
    await interaction.channel.send(embed=embed, view=RulesView())

@bot.tree.command(name="setup", description="Ouvre le panneau général de configuration du serveur MVP.")
@app_commands.default_permissions(administrator=True)
async def setup(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚙️ MVP Server - Configuration Dashboard",
        description="Choisissez la configuration que vous souhaitez ajuster ou activer sur votre serveur : \n\n"
                    "👤 **Rôle Automatique (Autorole)** : Attribuer un rôle par défaut aux arrivants.\n"
                    "🎭 **Rôle par Bouton (Self-Role)** : Créer un embed avec un bouton entièrement personnalisable (titre, description, couleur, texte et emoji du bouton) permettant aux membres d'obtenir un rôle.\n"
                    "🖼️ **Image Fixe (Bas de salon)** : Garder une image toujours affichée tout en bas d'un salon choisi.\n"
                    "🗑️ **Réinitialiser Image Fixe** : Désactiver le système d'image fixe sur un salon.",
        color=discord.Color.orange()
    )
    await interaction.response.send_message(embed=embed, view=SetupDashboardView(), ephemeral=True)


# --- Commandes de Contenu (Sondage / Annonce / Embed / Giveaway) ---
@bot.tree.command(name="poll", description="Créer un sondage avec plusieurs options.")
@app_commands.describe(
    question="La question du sondage",
    option1="Option 1",
    option2="Option 2",
    option3="Option 3 (facultatif)",
    option4="Option 4 (facultatif)",
    option5="Option 5 (facultatif)",
    couleur="Couleur de l'embed du sondage"
)
@app_commands.choices(couleur=COLOR_CHOICES)
async def poll(
    interaction: discord.Interaction,
    question: str,
    option1: str,
    option2: str,
    option3: str = None,
    option4: str = None,
    option5: str = None,
    couleur: str = "bleu"
):
    options = [option1, option2]
    for opt in (option3, option4, option5):
        if opt:
            options.append(opt)

    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
    description_lines = [f"{emojis[i]}  {opt}" for i, opt in enumerate(options)]

    embed = discord.Embed(
        title=f"📊 {question}",
        description="\n\n".join(description_lines),
        color=COLOR_MAP.get(couleur, discord.Color.blue())
    )
    embed.set_footer(text=f"Sondage lancé par {interaction.user.display_name}")
    embed.timestamp = datetime.datetime.now()

    await interaction.response.send_message("✅ Sondage créé !", ephemeral=True)
    poll_msg = await interaction.channel.send(embed=embed)
    for i in range(len(options)):
        await poll_msg.add_reaction(emojis[i])


@bot.tree.command(name="giveaway", description="Créer un giveaway avec une durée, un nombre de gagnants et une condition de participation.")
@app_commands.describe(
    prix="Le prix à gagner",
    duree_jours="Durée du giveaway en jours (ex: 1, 0.5 pour 12h, 7 pour une semaine)",
    gagnants="Nombre de gagnants à tirer au sort",
    invites_requises="Nombre d'invitations minimum requis pour participer (0 = aucune condition)",
    couleur="Couleur de l'embed"
)
@app_commands.choices(couleur=COLOR_CHOICES)
@app_commands.default_permissions(manage_guild=True)
async def giveaway(
    interaction: discord.Interaction,
    prix: str,
    duree_jours: float,
    gagnants: app_commands.Range[int, 1, 50] = 1,
    invites_requises: app_commands.Range[int, 0, 1000] = 0,
    couleur: str = "or"
):
    if duree_jours <= 0:
        await interaction.response.send_message("❌ La durée doit être supérieure à 0 jour.", ephemeral=True)
        return

    guild_id = str(interaction.guild.id)
    giveaway_id = get_next_giveaway_id(guild_id)

    end_dt = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=duree_jours)
    end_timestamp = end_dt.timestamp()

    embed_color = COLOR_MAP.get(couleur, discord.Color.gold())

    embed = build_giveaway_embed(
        prize=prix,
        winners_count=gagnants,
        required_invites=invites_requises,
        end_timestamp=end_timestamp,
        host=interaction.user,
        participants_count=0,
        color=embed_color
    )

    view = GiveawayView(interaction.guild.id, giveaway_id)

    await interaction.response.send_message("✅ Le giveaway a été lancé avec succès !", ephemeral=True)
    gw_message = await interaction.channel.send(embed=embed, view=view)

    config = load_config()
    if guild_id not in config:
        config[guild_id] = {}
    giveaways = config[guild_id].get("giveaways", [])
    giveaways.append({
        "id": giveaway_id,
        "prize": prix,
        "winners_count": gagnants,
        "required_invites": invites_requises,
        "channel_id": interaction.channel.id,
        "message_id": gw_message.id,
        "end_timestamp": end_timestamp,
        "participants": [],
        "ended": False,
        "host_id": interaction.user.id,
        "color": couleur
    })
    config[guild_id]["giveaways"] = giveaways
    save_config(config)


@bot.tree.command(name="setwinnerg", description="Prévoir manuellement le(s) gagnant(s) d'un giveaway en cours, sans le clôturer.")
@app_commands.default_permissions(manage_guild=True)
async def setwinnerg(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    giveaways = [gw for gw in get_giveaways(guild_id) if not gw.get("ended")]

    if not giveaways:
        await interaction.response.send_message(
            "❌ Aucun giveaway en cours sur ce serveur. Utilisez `/giveaway` pour en créer un.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="🏆 Prévoir le(s) gagnant(s) d'un giveaway",
        description="Sélectionnez ci-dessous le giveaway en cours pour lequel vous souhaitez prévoir "
                    "manuellement le(s) gagnant(s).\n\n"
                    "⚠️ Le giveaway **ne sera pas terminé maintenant** : il continue de tourner normalement "
                    "jusqu'à sa date de fin. Le(s) membre(s) choisi(s) seront simplement déclarés vainqueurs "
                    "automatiquement lorsque le giveaway se terminera, à la place d'un tirage au sort.",
        color=discord.Color.gold()
    )
    await interaction.response.send_message(
        embed=embed,
        view=SetWinnerGiveawaySelectView(interaction.guild.id, giveaways),
        ephemeral=True
    )


@bot.tree.command(name="announce", description="Créer une annonce sous forme d'embed, avec ou sans mention.")
@app_commands.describe(
    titre="Titre de l'annonce",
    description="Contenu de l'annonce",
    couleur="Couleur de l'embed",
    mention="Type de mention à ajouter au-dessus de l'annonce",
    role="Rôle à mentionner si l'option 'Rôle spécifique' est sélectionnée",
    image_url="URL d'une image à afficher (facultatif)"
)
@app_commands.choices(
    couleur=COLOR_CHOICES,
    mention=[
        app_commands.Choice(name="Aucune mention", value="none"),
        app_commands.Choice(name="@everyone", value="everyone"),
        app_commands.Choice(name="Rôle spécifique", value="role"),
    ]
)
@app_commands.default_permissions(administrator=True)
async def announce(
    interaction: discord.Interaction,
    titre: str,
    description: str,
    couleur: str = "bleu",
    mention: str = "none",
    role: discord.Role = None,
    image_url: str = None
):
    if mention == "role" and role is None:
        await interaction.response.send_message(
            "❌ Vous devez sélectionner un rôle si vous choisissez l'option 'Rôle spécifique'.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title=titre,
        description=description,
        color=COLOR_MAP.get(couleur, discord.Color.blue())
    )
    embed.set_footer(text=f"Annonce par {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
    embed.timestamp = datetime.datetime.now()
    if image_url:
        embed.set_image(url=image_url)

    content = None
    allowed_mentions = discord.AllowedMentions.none()
    if mention == "everyone":
        content = "@everyone"
        allowed_mentions = discord.AllowedMentions(everyone=True)
    elif mention == "role":
        content = role.mention
        allowed_mentions = discord.AllowedMentions(roles=True)

    await interaction.response.send_message("✅ Annonce publiée !", ephemeral=True)
    await interaction.channel.send(content=content, embed=embed, allowed_mentions=allowed_mentions)


@bot.tree.command(name="embed", description="Créer et envoyer un embed personnalisé.")
@app_commands.describe(
    description="Texte principal de l'embed",
    titre="Titre de l'embed (facultatif)",
    couleur="Couleur de l'embed",
    image_url="URL d'une grande image à afficher (facultatif)",
    thumbnail_url="URL d'une miniature à afficher (facultatif)",
    footer="Texte du pied de page (facultatif)"
)
@app_commands.choices(couleur=COLOR_CHOICES)
@app_commands.default_permissions(manage_messages=True)
async def embed_command(
    interaction: discord.Interaction,
    description: str,
    titre: str = None,
    couleur: str = "bleu",
    image_url: str = None,
    thumbnail_url: str = None,
    footer: str = None
):
    custom_embed = discord.Embed(
        description=description,
        color=COLOR_MAP.get(couleur, discord.Color.blue())
    )
    if titre:
        custom_embed.title = titre
    if image_url:
        custom_embed.set_image(url=image_url)
    if thumbnail_url:
        custom_embed.set_thumbnail(url=thumbnail_url)
    if footer:
        custom_embed.set_footer(text=footer)

    await interaction.response.send_message("✅ Embed envoyé !", ephemeral=True)
    await interaction.channel.send(embed=custom_embed)


# --- Vue de confirmation avant l'envoi massif de messages privés ---
class GlobalAnnounceConfirmView(discord.ui.View):
    def __init__(self, requester_id: int):
        super().__init__(timeout=60)
        self.requester_id = requester_id
        self.confirmed = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.requester_id:
            await interaction.response.send_message(
                "❌ Seule la personne ayant lancé cette annonce peut la confirmer.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="✅ Confirmer et envoyer", style=discord.ButtonStyle.danger, custom_id="global_announce_confirm")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = True
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="📨 Envoi en cours, veuillez patienter...", view=self)
        self.stop()

    @discord.ui.button(label="❌ Annuler", style=discord.ButtonStyle.secondary, custom_id="global_announce_cancel")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = False
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="❌ Annonce globale annulée.", embed=None, view=self)
        self.stop()


@bot.tree.command(name="globalannounce", description="Envoie un embed en message privé à tous les membres du serveur.")
@app_commands.describe(
    titre="Titre de l'annonce",
    description="Contenu de l'annonce",
    couleur="Couleur de l'embed",
    image_url="URL d'une image à afficher (facultatif)",
    inclure_bots="Envoyer également aux comptes bots (non, par défaut)"
)
@app_commands.choices(couleur=COLOR_CHOICES)
@app_commands.default_permissions(administrator=True)
async def globalannounce(
    interaction: discord.Interaction,
    titre: str,
    description: str,
    couleur: str = "bleu",
    image_url: str = None,
    inclure_bots: bool = False
):
    embed = discord.Embed(
        title=titre,
        description=description,
        color=COLOR_MAP.get(couleur, discord.Color.blue())
    )
    embed.set_footer(
        text=f"Annonce de {interaction.guild.name}",
        icon_url=interaction.guild.icon.url if interaction.guild.icon else None
    )
    embed.timestamp = datetime.datetime.now()
    if image_url:
        embed.set_image(url=image_url)

    members = [m for m in interaction.guild.members if inclure_bots or not m.bot]
    count = len(members)

    if count == 0:
        await interaction.response.send_message("❌ Aucun membre à qui envoyer cette annonce.", ephemeral=True)
        return

    estimated_seconds = count  # ~1 message/seconde pour rester sous les limites de Discord
    estimated_minutes = max(1, round(estimated_seconds / 60))

    confirm_embed = discord.Embed(
        title="⚠️ Confirmation requise",
        description=(
            f"Vous êtes sur le point d'envoyer cette annonce **en message privé** à **{count}** membre(s) "
            f"de **{interaction.guild.name}**.\n\n"
            f"⏱️ Durée estimée : environ **{estimated_minutes}** minute(s).\n\n"
            "Aperçu de l'embed qui sera envoyé ci-dessous :"
        ),
        color=discord.Color.orange()
    )

    view = GlobalAnnounceConfirmView(interaction.user.id)
    await interaction.response.send_message(embeds=[confirm_embed, embed], view=view, ephemeral=True)
    await view.wait()

    if not view.confirmed:
        return

    sent = 0
    failed = 0
    for member in members:
        try:
            await member.send(embed=embed)
            sent += 1
        except (discord.Forbidden, discord.HTTPException):
            failed += 1
        # Petite pause pour éviter de se faire rate-limit par Discord sur les DMs en masse
        await asyncio.sleep(1)

    result_embed = discord.Embed(
        title="📨 Annonce globale terminée",
        description=(
            f"✅ Envoyée avec succès à **{sent}** membre(s).\n"
            f"❌ Échec pour **{failed}** membre(s) (messages privés fermés ou erreur)."
        ),
        color=discord.Color.green() if failed == 0 else discord.Color.gold()
    )
    await interaction.followup.send(embed=result_embed, ephemeral=True)


# --- Commandes de Modération ---
@bot.tree.command(name="ban", description="Bannir définitivement un membre du serveur.")
@app_commands.describe(membre="Le membre à bannir", raison="La raison du bannissement")
@app_commands.default_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison fournie"):
    try:
        await membre.ban(reason=raison)
        await interaction.response.send_message(f"🔨 **{membre.mention}** a été banni.\n**Raison :** {raison}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ Permissions insuffisantes pour bannir ce membre.", ephemeral=True)

@bot.tree.command(name="kick", description="Expulser temporairement un membre du serveur.")
@app_commands.describe(membre="Le membre à expulser", raison="La raison de l'expulsion")
@app_commands.default_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison fournie"):
    try:
        await membre.kick(reason=raison)
        await interaction.response.send_message(f"👞 **{membre.mention}** a été expulsé.\n**Raison :** {raison}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ Permissions insuffisantes pour expulser ce membre.", ephemeral=True)

@bot.tree.command(name="mute", description="Mettre un membre en sourdine temporaire (Timeout).")
@app_commands.describe(membre="Le membre à muter", duree_minutes="Durée de la mise en sourdine en minutes", raison="La raison")
@app_commands.default_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, membre: discord.Member, duree_minutes: int, raison: str = "Aucune raison fournie"):
    try:
        duration = datetime.timedelta(minutes=duree_minutes)
        await membre.timeout(duration, reason=raison)
        await interaction.response.send_message(f"🔇 **{membre.mention}** a été mis en sourdine pour **{duree_minutes}** minute(s).\n**Raison :** {raison}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ Permissions insuffisantes pour appliquer la mise en sourdine.", ephemeral=True)

@bot.tree.command(name="unmute", description="Enlever la sourdine (Timeout) d'un membre.")
@app_commands.describe(membre="Le membre à démuter", raison="La raison de la fin de sourdine")
@app_commands.default_permissions(moderate_members=True)
async def unmute(interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison fournie"):
    try:
        await membre.timeout(None, reason=raison)
        await interaction.response.send_message(f"🔊 **{membre.mention}** n'est plus en sourdine.\n**Raison :** {raison}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ Permissions insuffisantes pour démuter ce membre.", ephemeral=True)

@bot.tree.command(name="clear", description="Supprime un nombre défini de messages dans le salon actuel.")
@app_commands.describe(nombre="Nombre de messages à supprimer")
@app_commands.default_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, nombre: int):
    if nombre < 1:
        await interaction.response.send_message("❌ Veuillez choisir un nombre supérieur à 0.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=nombre)
    await interaction.followup.send(f"🧹 **{len(deleted)}** messages ont été supprimés avec succès.")


# ==================== SYSTÈME DE TICKETS ====================

def get_ticket_panels(guild_id: str) -> list:
    config = load_config()
    return config.get(guild_id, {}).get("ticket_panels", [])


def get_ticket_panel(guild_id: str, panel_id: int):
    for panel in get_ticket_panels(guild_id):
        if panel.get("id") == panel_id:
            return panel
    return None


def get_next_ticket_number(guild_id: str) -> int:
    config = load_config()
    if guild_id not in config:
        config[guild_id] = {}
    current = config[guild_id].get("ticket_counter", 0) + 1
    config[guild_id]["ticket_counter"] = current
    save_config(config)
    return current


def slugify_username(name: str) -> str:
    """Nettoie un pseudo Discord pour en faire un nom de salon valide."""
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9]+", "-", name)
    name = name.strip("-")
    if not name:
        name = "user"
    return name[:80]


# --- Modale de personnalisation de l'embed du panel de ticket ---
class TicketEmbedModal(discord.ui.Modal):
    def __init__(self, setup_view: "TicketSetupView"):
        super().__init__(title="Personnalisation du Panel de Ticket")
        self.setup_view = setup_view

        self.titre = discord.ui.TextInput(
            label="Titre de l'embed",
            default=setup_view.data["embed_title"],
            required=True,
            max_length=100
        )
        self.description = discord.ui.TextInput(
            label="Description de l'embed",
            style=discord.TextStyle.paragraph,
            default=setup_view.data["embed_description"],
            required=True,
            max_length=1000
        )
        self.couleur = discord.ui.TextInput(
            label="Couleur (nom ou hex, ex: bleu / #5865F2)",
            default=setup_view.data["embed_color"],
            required=False,
            max_length=20
        )
        self.bouton_texte = discord.ui.TextInput(
            label="Texte du bouton",
            default=setup_view.data["button_label"],
            required=True,
            max_length=80
        )
        self.bouton_emoji = discord.ui.TextInput(
            label="Emoji du bouton (facultatif)",
            default=setup_view.data["button_emoji"] or "",
            required=False,
            max_length=50
        )
        self.add_item(self.titre)
        self.add_item(self.description)
        self.add_item(self.couleur)
        self.add_item(self.bouton_texte)
        self.add_item(self.bouton_emoji)

    async def on_submit(self, interaction: discord.Interaction):
        self.setup_view.data["embed_title"] = self.titre.value
        self.setup_view.data["embed_description"] = self.description.value
        self.setup_view.data["embed_color"] = self.couleur.value or "bleu"
        self.setup_view.data["button_label"] = self.bouton_texte.value
        self.setup_view.data["button_emoji"] = parse_emoji(self.bouton_emoji.value)

        await interaction.response.edit_message(
            embed=self.setup_view.build_preview_embed(),
            view=self.setup_view
        )


# --- Modale de saisie des questions préalables (jusqu'à 5) ---
class TicketQuestionsModal(discord.ui.Modal):
    def __init__(self, setup_view: "TicketSetupView"):
        super().__init__(title="Questions avant ouverture de ticket")
        self.setup_view = setup_view

        existing = setup_view.data.get("questions", [])
        defaults = [q["text"] for q in existing]
        while len(defaults) < 5:
            defaults.append("")

        self.q1 = discord.ui.TextInput(label="Question 1", default=defaults[0], required=True, max_length=200)
        self.q2 = discord.ui.TextInput(label="Question 2 (facultative)", default=defaults[1], required=False, max_length=200)
        self.q3 = discord.ui.TextInput(label="Question 3 (facultative)", default=defaults[2], required=False, max_length=200)
        self.q4 = discord.ui.TextInput(label="Question 4 (facultative)", default=defaults[3], required=False, max_length=200)
        self.q5 = discord.ui.TextInput(label="Question 5 (facultative)", default=defaults[4], required=False, max_length=200)
        for item in (self.q1, self.q2, self.q3, self.q4, self.q5):
            self.add_item(item)

    async def on_submit(self, interaction: discord.Interaction):
        old_required = {q["text"]: q["required"] for q in self.setup_view.data.get("questions", [])}
        new_questions = []
        for field in (self.q1, self.q2, self.q3, self.q4, self.q5):
            text = field.value.strip()
            if text:
                new_questions.append({
                    "text": text,
                    "required": old_required.get(text, False)
                })

        self.setup_view.data["questions"] = new_questions
        self.setup_view.data["questions_enabled"] = bool(new_questions)
        self.setup_view.refresh_buttons()

        await interaction.response.edit_message(
            embed=self.setup_view.build_preview_embed(),
            view=self.setup_view
        )

        if new_questions:
            await interaction.followup.send(
                "Sélectionnez maintenant les questions auxquelles il est **obligatoire** de répondre "
                "(les autres resteront facultatives) :",
                view=TicketRequiredQuestionsView(self.setup_view),
                ephemeral=True
            )


# --- Sélection multiple des questions obligatoires ---
class TicketRequiredQuestionsSelect(discord.ui.Select):
    def __init__(self, setup_view: "TicketSetupView"):
        self.setup_view = setup_view
        options = [
            discord.SelectOption(
                label=q["text"][:100],
                value=str(i),
                default=q["required"]
            )
            for i, q in enumerate(setup_view.data["questions"])
        ]
        super().__init__(
            placeholder="Questions obligatoires (aucune = tout facultatif)...",
            min_values=0,
            max_values=len(options),
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selected_indexes = set(int(v) for v in self.values)
        for i, question in enumerate(self.setup_view.data["questions"]):
            question["required"] = i in selected_indexes
        await interaction.response.edit_message(
            content="✅ Questions obligatoires mises à jour ! Retournez au message de configuration pour publier le panel.",
            view=None
        )


class TicketRequiredQuestionsView(discord.ui.View):
    def __init__(self, setup_view: "TicketSetupView"):
        super().__init__(timeout=300)
        self.add_item(TicketRequiredQuestionsSelect(setup_view))


# --- Sélecteurs de salon / catégorie / rôles support pour le wizard ---
class TicketPanelChannelSelect(discord.ui.ChannelSelect):
    def __init__(self, setup_view: "TicketSetupView"):
        self.setup_view = setup_view
        super().__init__(
            placeholder="📍 Salon où poster le panel de ticket...",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
            row=0
        )

    async def callback(self, interaction: discord.Interaction):
        self.setup_view.data["panel_channel_id"] = self.values[0].id
        await interaction.response.edit_message(embed=self.setup_view.build_preview_embed(), view=self.setup_view)


class TicketCategorySelect(discord.ui.ChannelSelect):
    def __init__(self, setup_view: "TicketSetupView"):
        self.setup_view = setup_view
        super().__init__(
            placeholder="📁 Catégorie où créer les salons de tickets...",
            channel_types=[discord.ChannelType.category],
            min_values=1,
            max_values=1,
            row=1
        )

    async def callback(self, interaction: discord.Interaction):
        self.setup_view.data["category_id"] = self.values[0].id
        await interaction.response.edit_message(embed=self.setup_view.build_preview_embed(), view=self.setup_view)


class TicketSupportRoleSelect(discord.ui.RoleSelect):
    """Sélection MULTIPLE : on peut désormais choisir plusieurs rôles support
    qui verront tous les tickets créés depuis ce panel."""
    def __init__(self, setup_view: "TicketSetupView"):
        self.setup_view = setup_view
        super().__init__(
            placeholder="👮 Rôle(s) support (facultatif, voient tous les tickets)...",
            min_values=0,
            max_values=10,
            row=2
        )

    async def callback(self, interaction: discord.Interaction):
        self.setup_view.data["support_role_ids"] = [role.id for role in self.values]
        await interaction.response.edit_message(embed=self.setup_view.build_preview_embed(), view=self.setup_view)


# --- Vue principale de configuration (/setupticket) ---
class TicketSetupView(discord.ui.View):
    def __init__(self, guild_id: int, panel_data: dict = None, panel_id: int = None):
        super().__init__(timeout=900)
        self.guild_id = guild_id
        # panel_id renseigné => on modifie un panel existant plutôt que d'en créer un nouveau
        self.editing_panel_id = panel_id

        if panel_data:
            self.data = json.loads(json.dumps(panel_data))  # copie profonde simple
            self.data.setdefault("support_role_ids", [])
        else:
            self.data = {
                "embed_title": "🎫 Support",
                "embed_description": "Cliquez sur le bouton ci-dessous pour ouvrir un ticket.",
                "embed_color": "bleu",
                "button_label": "Ouvrir un ticket",
                "button_emoji": "🎫",
                "panel_channel_id": None,
                "category_id": None,
                "support_role_ids": [],
                "questions_enabled": False,
                "questions": []
            }

        self.add_item(TicketPanelChannelSelect(self))
        self.add_item(TicketCategorySelect(self))
        self.add_item(TicketSupportRoleSelect(self))
        self.refresh_buttons()

    def build_preview_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=self.data["embed_title"],
            description=self.data["embed_description"],
            color=parse_color(self.data["embed_color"])
        )

        support_role_ids = self.data.get("support_role_ids", [])
        if support_role_ids:
            roles_txt = ", ".join(f"<@&{rid}>" for rid in support_role_ids)
            support_line = f"**Rôles support :** {roles_txt}"
        else:
            support_line = "**Rôles support :** Aucun (staff par défaut)"

        status_lines = [
            f"**Salon du panel :** <#{self.data['panel_channel_id']}>" if self.data["panel_channel_id"] else "**Salon du panel :** ❌ non défini",
            f"**Catégorie tickets :** <#{self.data['category_id']}>" if self.data["category_id"] else "**Catégorie tickets :** ❌ non définie",
            support_line,
            f"**Questions préalables :** {'✅ Activées (' + str(len(self.data['questions'])) + ')' if (self.data['questions_enabled'] and self.data['questions']) else '❌ Désactivées'}"
        ]
        embed.add_field(name="⚙️ Configuration actuelle", value="\n".join(status_lines), inline=False)
        if self.editing_panel_id is not None:
            embed.set_footer(text=f"✏️ Modification du panel #{self.editing_panel_id}")
        return embed

    def refresh_buttons(self):
        for item in self.children:
            if isinstance(item, discord.ui.Button) and item.custom_id == "ticket_setup_configure_questions":
                item.disabled = not self.data["questions_enabled"]
            if isinstance(item, discord.ui.Button) and item.custom_id == "ticket_setup_toggle_questions":
                item.label = "❓ Questions : Activées" if self.data["questions_enabled"] else "❓ Questions : Désactivées"
                item.style = discord.ButtonStyle.success if self.data["questions_enabled"] else discord.ButtonStyle.secondary
            if isinstance(item, discord.ui.Button) and item.custom_id == "ticket_setup_publish":
                item.label = "✅ Enregistrer les modifications" if self.editing_panel_id is not None else "✅ Publier le panel"

    @discord.ui.button(label="✏️ Personnaliser l'embed", style=discord.ButtonStyle.primary, row=3, custom_id="ticket_setup_edit_embed")
    async def edit_embed(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketEmbedModal(self))

    @discord.ui.button(label="❓ Questions : Désactivées", style=discord.ButtonStyle.secondary, row=3, custom_id="ticket_setup_toggle_questions")
    async def toggle_questions(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.data["questions_enabled"] = not self.data["questions_enabled"]
        self.refresh_buttons()

        if self.data["questions_enabled"] and not self.data["questions"]:
            await interaction.response.edit_message(embed=self.build_preview_embed(), view=self)
            await interaction.followup.send(
                "Cliquez sur **📝 Configurer les questions** pour ajouter vos questions.",
                ephemeral=True
            )
            return

        await interaction.response.edit_message(embed=self.build_preview_embed(), view=self)

    @discord.ui.button(label="📝 Configurer les questions", style=discord.ButtonStyle.secondary, row=3, custom_id="ticket_setup_configure_questions", disabled=True)
    async def configure_questions(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketQuestionsModal(self))

    @discord.ui.button(label="✅ Publier le panel", style=discord.ButtonStyle.success, row=4, custom_id="ticket_setup_publish")
    async def publish(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.data["panel_channel_id"] or not self.data["category_id"]:
            await interaction.response.send_message(
                "❌ Vous devez sélectionner un **salon** pour le panel et une **catégorie** pour les tickets avant de publier.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        config = load_config()
        guild_id = str(self.guild_id)
        if guild_id not in config:
            config[guild_id] = {}
        panels = config[guild_id].get("ticket_panels", [])

        embed = discord.Embed(
            title=self.data["embed_title"],
            description=self.data["embed_description"],
            color=parse_color(self.data["embed_color"])
        )

        if self.editing_panel_id is not None:
            panel_id = self.editing_panel_id
            existing = next((p for p in panels if p.get("id") == panel_id), None)
            self.data["id"] = panel_id

            # On enregistre la config avant l'envoi/édition du message pour que
            # TicketPanelView retrouve bien le bon libellé/emoji de bouton.
            self.data["panel_message_id"] = existing.get("panel_message_id") if existing else None
            panels = [self.data if p.get("id") == panel_id else p for p in panels]
            config[guild_id]["ticket_panels"] = panels
            save_config(config)

            panel_view = TicketPanelView(self.guild_id, panel_id)
            edited = False
            if existing and existing.get("panel_message_id") and existing.get("panel_channel_id"):
                old_channel = interaction.guild.get_channel(existing["panel_channel_id"])
                if old_channel:
                    try:
                        old_message = await old_channel.fetch_message(existing["panel_message_id"])
                        await old_message.edit(embed=embed, view=panel_view)
                        self.data["panel_message_id"] = old_message.id
                        self.data["panel_channel_id"] = old_channel.id
                        edited = True
                    except (discord.NotFound, discord.Forbidden):
                        edited = False

            if not edited:
                channel = interaction.guild.get_channel(self.data["panel_channel_id"])
                new_message = await channel.send(embed=embed, view=panel_view)
                self.data["panel_message_id"] = new_message.id

            panels = [self.data if p.get("id") == panel_id else p for p in panels]
            config[guild_id]["ticket_panels"] = panels
            save_config(config)

            result_channel = interaction.guild.get_channel(self.data["panel_channel_id"])
            confirmation = f"✅ Le panel #{panel_id} a été mis à jour dans {result_channel.mention} !"
        else:
            panel_id = max((p.get("id", 0) for p in panels), default=0) + 1
            self.data["id"] = panel_id
            self.data["panel_message_id"] = None
            panels.append(self.data)
            config[guild_id]["ticket_panels"] = panels
            save_config(config)

            channel = interaction.guild.get_channel(self.data["panel_channel_id"])
            panel_view = TicketPanelView(self.guild_id, panel_id)
            new_message = await channel.send(embed=embed, view=panel_view)
            self.data["panel_message_id"] = new_message.id
            panels = [self.data if p.get("id") == panel_id else p for p in panels]
            config[guild_id]["ticket_panels"] = panels
            save_config(config)

            confirmation = f"✅ Le panel de ticket a été publié dans {channel.mention} ! Il est désormais géré via `/manageticket`."

        for item in self.children:
            item.disabled = True
        await interaction.edit_original_response(
            content=confirmation,
            embed=None,
            view=self
        )

    @discord.ui.button(label="❌ Annuler", style=discord.ButtonStyle.danger, row=4, custom_id="ticket_setup_cancel")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="❌ Configuration annulée.", embed=None, view=self)


# --- Sélecteur affiché par /setupticket pour choisir un panel existant ou en créer un nouveau ---
class TicketPanelChooserSelect(discord.ui.Select):
    def __init__(self, guild: discord.Guild, panels: list):
        self.guild = guild
        self.panels = panels
        options = [
            discord.SelectOption(
                label="➕ Créer un nouveau panel",
                value="new",
                description="Configurer et publier un nouveau panel de tickets",
                emoji="✨"
            )
        ]
        for p in panels:
            channel = guild.get_channel(p.get("panel_channel_id")) if p.get("panel_channel_id") else None
            channel_desc = f"#{channel.name}" if channel else "salon introuvable"
            options.append(
                discord.SelectOption(
                    label=f"Panel #{p.get('id')} - {p.get('embed_title', 'Sans titre')}"[:100],
                    value=str(p.get("id")),
                    description=channel_desc[:100],
                    emoji="🎫"
                )
            )
        super().__init__(
            placeholder="Choisissez un panel existant à modifier, ou créez-en un nouveau...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "new":
            view = TicketSetupView(self.guild.id)
        else:
            panel_id = int(self.values[0])
            panel_data = next((p for p in self.panels if p.get("id") == panel_id), None)
            view = TicketSetupView(self.guild.id, panel_data=panel_data, panel_id=panel_id)

        await interaction.response.edit_message(
            content=(
                "**🎫 Configuration du système de tickets**\n"
                "1️⃣ Personnalisez l'embed, 2️⃣ choisissez le salon et la catégorie, "
                "3️⃣ activez les questions préalables si besoin, puis publiez."
            ),
            embed=view.build_preview_embed(),
            view=view
        )


class TicketPanelChooserView(discord.ui.View):
    def __init__(self, guild: discord.Guild, panels: list):
        super().__init__(timeout=300)
        self.add_item(TicketPanelChooserSelect(guild, panels))


# ==================== PANELS REGROUPÉS (plusieurs boutons dans un même message) ====================
# Permet de regrouper plusieurs panels de tickets déjà créés avec /setupticket
# dans un seul message avec une bannière et un bouton par panel (comme la capture d'écran fournie).

def get_ticket_group_panels(guild_id: str) -> list:
    config = load_config()
    return config.get(guild_id, {}).get("ticket_group_panels", [])


def get_ticket_group_panel(guild_id: str, group_id: int):
    for group in get_ticket_group_panels(guild_id):
        if group.get("id") == group_id:
            return group
    return None


class GroupTicketPanelView(discord.ui.View):
    """Un seul message avec un bouton par panel de ticket regroupé.
    Réutilise TicketPanelButton : chaque bouton ouvre exactement le même flux
    (catégorie, questions, rôles support) que le panel individuel correspondant."""
    def __init__(self, guild_id: int, group_id: int):
        super().__init__(timeout=None)
        cfg = get_ticket_group_panel(str(guild_id), group_id) or {}
        for panel_id in cfg.get("panel_ids", []):
            panel_cfg = get_ticket_panel(str(guild_id), panel_id)
            if not panel_cfg:
                continue
            label = panel_cfg.get("button_label", f"Panel {panel_id}")
            emoji = panel_cfg.get("button_emoji", "🎫")
            self.add_item(TicketPanelButton(guild_id, panel_id, label, emoji))


class GroupEmbedModal(discord.ui.Modal):
    def __init__(self, setup_view: "GroupSetupView"):
        super().__init__(title="Personnalisation du Panel Regroupé")
        self.setup_view = setup_view

        self.titre = discord.ui.TextInput(
            label="Titre de l'embed",
            default=setup_view.data["embed_title"],
            required=True,
            max_length=100
        )
        self.description = discord.ui.TextInput(
            label="Description de l'embed",
            style=discord.TextStyle.paragraph,
            default=setup_view.data["embed_description"],
            required=False,
            max_length=1000
        )
        self.couleur = discord.ui.TextInput(
            label="Couleur (nom ou hex, ex: bleu / #5865F2)",
            default=setup_view.data["embed_color"],
            required=False,
            max_length=20
        )
        self.image_url = discord.ui.TextInput(
            label="URL de la bannière (image, facultatif)",
            default=setup_view.data.get("image_url") or "",
            required=False,
            max_length=300
        )
        self.add_item(self.titre)
        self.add_item(self.description)
        self.add_item(self.couleur)
        self.add_item(self.image_url)

    async def on_submit(self, interaction: discord.Interaction):
        self.setup_view.data["embed_title"] = self.titre.value
        self.setup_view.data["embed_description"] = self.description.value
        self.setup_view.data["embed_color"] = self.couleur.value or "bleu"
        self.setup_view.data["image_url"] = self.image_url.value.strip() or None

        await interaction.response.edit_message(
            embed=self.setup_view.build_preview_embed(),
            view=self.setup_view
        )


class GroupPanelChannelSelect(discord.ui.ChannelSelect):
    def __init__(self, setup_view: "GroupSetupView"):
        self.setup_view = setup_view
        super().__init__(
            placeholder="📍 Salon où poster le panel regroupé...",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
            row=0
        )

    async def callback(self, interaction: discord.Interaction):
        self.setup_view.data["panel_channel_id"] = self.values[0].id
        await interaction.response.edit_message(embed=self.setup_view.build_preview_embed(), view=self.setup_view)


class GroupPanelsMultiSelect(discord.ui.Select):
    """Sélection des panels de tickets existants à inclure comme boutons dans le message regroupé."""
    def __init__(self, setup_view: "GroupSetupView", panels: list):
        self.setup_view = setup_view
        options = [
            discord.SelectOption(
                label=f"Panel #{p.get('id')} - {p.get('embed_title', 'Sans titre')}"[:100],
                value=str(p.get("id")),
                emoji=p.get("button_emoji") or "🎫",
                default=p.get("id") in setup_view.data.get("panel_ids", [])
            )
            for p in panels
        ]
        super().__init__(
            placeholder="Choisissez les panels à regrouper dans ce message...",
            min_values=0,
            max_values=len(options),
            options=options,
            row=1
        )

    async def callback(self, interaction: discord.Interaction):
        self.setup_view.data["panel_ids"] = [int(v) for v in self.values]
        self.setup_view._refresh_field_select()
        await interaction.response.edit_message(embed=self.setup_view.build_preview_embed(), view=self.setup_view)


# --- Modale de personnalisation du texte affiché pour UN panel donné dans le message regroupé ---
class GroupFieldModal(discord.ui.Modal):
    def __init__(self, setup_view: "GroupSetupView", panel_id: int, panel_cfg: dict):
        super().__init__(title=f"Texte affiché - Panel #{panel_id}")
        self.setup_view = setup_view
        self.panel_id = panel_id

        existing = setup_view.data.get("panel_fields", {}).get(str(panel_id), {})
        default_label = panel_cfg.get("button_label", "Ouvrir un ticket")
        default_title = existing.get("title") or panel_cfg.get("embed_title") or default_label
        # Par défaut, on préremplit avec la description déjà configurée sur le panel
        # individuel (via /setupticket), plutôt qu'une phrase générique.
        default_desc = (
            existing.get("description")
            or panel_cfg.get("embed_description")
            or f"Appuyez sur **{default_label}** pour ouvrir le ticket correspondant."
        )

        self.titre = discord.ui.TextInput(
            label="Titre affiché (ex : une question en gras)",
            default=default_title,
            required=True,
            max_length=256
        )
        self.description = discord.ui.TextInput(
            label="Texte affiché sous le titre",
            style=discord.TextStyle.paragraph,
            default=default_desc,
            required=True,
            max_length=1024
        )
        self.add_item(self.titre)
        self.add_item(self.description)

    async def on_submit(self, interaction: discord.Interaction):
        panel_fields = self.setup_view.data.setdefault("panel_fields", {})
        panel_fields[str(self.panel_id)] = {
            "title": self.titre.value,
            "description": self.description.value
        }
        await interaction.response.edit_message(
            embed=self.setup_view.build_preview_embed(),
            view=self.setup_view
        )


# --- Sélecteur permettant de choisir POUR QUEL panel personnaliser le texte affiché ---
class GroupFieldEditSelect(discord.ui.Select):
    def __init__(self, setup_view: "GroupSetupView", panels: list, panel_ids: list):
        self.setup_view = setup_view
        self.panels = panels

        options = []
        for pid in panel_ids:
            p = next((x for x in panels if x.get("id") == pid), None)
            if not p:
                continue
            options.append(
                discord.SelectOption(
                    label=f"Panel #{pid} - {p.get('button_label', 'Ouvrir un ticket')}"[:100],
                    value=str(pid),
                    emoji=p.get("button_emoji") or "🎫"
                )
            )

        disabled = not options
        if not options:
            options = [discord.SelectOption(label="Sélectionnez d'abord des panels ci-dessus", value="none")]

        super().__init__(
            placeholder="✏️ Personnaliser le texte affiché d'un panel...",
            min_values=1,
            max_values=1,
            options=options,
            disabled=disabled,
            row=4
        )

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            await interaction.response.defer()
            return
        panel_id = int(self.values[0])
        panel_cfg = next((p for p in self.panels if p.get("id") == panel_id), None)
        if not panel_cfg:
            await interaction.response.send_message("❌ Ce panel n'existe plus.", ephemeral=True)
            return
        await interaction.response.send_modal(GroupFieldModal(self.setup_view, panel_id, panel_cfg))


class GroupSetupView(discord.ui.View):
    def __init__(self, guild_id: int, panels: list, group_data: dict = None, group_id: int = None):
        super().__init__(timeout=900)
        self.guild_id = guild_id
        self.editing_group_id = group_id
        self.panels = panels
        self.field_select = None

        if group_data:
            self.data = json.loads(json.dumps(group_data))
            self.data.setdefault("panel_ids", [])
            self.data.setdefault("panel_fields", {})
        else:
            self.data = {
                "embed_title": "🎫 Support, 24/7",
                "embed_description": "Cliquez sur un bouton ci-dessous pour ouvrir le ticket correspondant.",
                "embed_color": "bleu",
                "image_url": None,
                "panel_channel_id": None,
                "panel_ids": [],
                "panel_fields": {}
            }

        self.add_item(GroupPanelChannelSelect(self))
        if panels:
            self.add_item(GroupPanelsMultiSelect(self, panels))
        self._refresh_field_select()
        self.refresh_buttons()

    def _refresh_field_select(self):
        """Recrée le sélecteur de personnalisation de texte pour qu'il reflète
        toujours la liste actuelle des panels inclus dans le groupe."""
        if self.field_select is not None and self.field_select in self.children:
            self.remove_item(self.field_select)
        self.field_select = GroupFieldEditSelect(self, self.panels, self.data.get("panel_ids", []))
        self.add_item(self.field_select)

    def build_public_embed(self) -> discord.Embed:
        """Construit l'embed exactement tel qu'il sera publié publiquement :
        bannière/couleur/titre + un champ (titre en gras + texte) par panel inclus."""
        embed = discord.Embed(
            title=self.data["embed_title"],
            description=self.data["embed_description"],
            color=parse_color(self.data["embed_color"])
        )
        if self.data.get("image_url"):
            embed.set_image(url=self.data["image_url"])

        panel_fields = self.data.get("panel_fields", {})
        for pid in self.data.get("panel_ids", []):
            p = next((x for x in self.panels if x.get("id") == pid), None)
            if not p:
                continue
            label = p.get("button_label", "Ouvrir un ticket")
            field_data = panel_fields.get(str(pid), {})
            title = field_data.get("title") or p.get("embed_title") or label
            # Par défaut, le texte affiché avant le bouton est la description du panel
            # telle que configurée dans /setupticket (et non une phrase générique).
            default_description = p.get("embed_description") or f"Appuyez sur **{label}** pour ouvrir le ticket correspondant."
            description = field_data.get("description") or default_description
            embed.add_field(name=title, value=description, inline=False)

        return embed

    def build_preview_embed(self) -> discord.Embed:
        embed = self.build_public_embed()

        status_lines = [
            f"**Salon du panel :** <#{self.data['panel_channel_id']}>" if self.data["panel_channel_id"] else "**Salon du panel :** ❌ non défini",
            f"**Panels sélectionnés :** {len(self.data.get('panel_ids', []))}" if self.data.get("panel_ids") else "**Panels sélectionnés :** ❌ aucun",
        ]
        embed.add_field(name="⚙️ Configuration actuelle", value="\n".join(status_lines), inline=False)
        if self.editing_group_id is not None:
            embed.set_footer(text=f"✏️ Modification du panel regroupé #{self.editing_group_id}")
        return embed

    def refresh_buttons(self):
        for item in self.children:
            if isinstance(item, discord.ui.Button) and item.custom_id == "group_setup_publish":
                item.label = "✅ Enregistrer les modifications" if self.editing_group_id is not None else "✅ Publier le panel"

    @discord.ui.button(label="✏️ Personnaliser l'embed", style=discord.ButtonStyle.primary, row=2, custom_id="group_setup_edit_embed")
    async def edit_embed(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(GroupEmbedModal(self))

    @discord.ui.button(label="✅ Publier le panel", style=discord.ButtonStyle.success, row=3, custom_id="group_setup_publish")
    async def publish(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.data["panel_channel_id"] or not self.data.get("panel_ids"):
            await interaction.response.send_message(
                "❌ Vous devez sélectionner un **salon** et au moins **un panel** avant de publier.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        config = load_config()
        guild_id = str(self.guild_id)
        if guild_id not in config:
            config[guild_id] = {}
        groups = config[guild_id].get("ticket_group_panels", [])

        # On publie exactement le rendu final (bannière + un champ par panel), sans le
        # champ de statut qui n'est utile que pendant la configuration.
        embed = self.build_public_embed()

        if self.editing_group_id is not None:
            group_id = self.editing_group_id
            existing = next((g for g in groups if g.get("id") == group_id), None)
            self.data["id"] = group_id
            self.data["panel_message_id"] = existing.get("panel_message_id") if existing else None
            groups = [self.data if g.get("id") == group_id else g for g in groups]
            config[guild_id]["ticket_group_panels"] = groups
            save_config(config)

            group_view = GroupTicketPanelView(self.guild_id, group_id)
            edited = False
            if existing and existing.get("panel_message_id") and existing.get("panel_channel_id"):
                old_channel = interaction.guild.get_channel(existing["panel_channel_id"])
                if old_channel:
                    try:
                        old_message = await old_channel.fetch_message(existing["panel_message_id"])
                        await old_message.edit(embed=embed, view=group_view)
                        self.data["panel_message_id"] = old_message.id
                        self.data["panel_channel_id"] = old_channel.id
                        edited = True
                    except (discord.NotFound, discord.Forbidden):
                        edited = False

            if not edited:
                channel = interaction.guild.get_channel(self.data["panel_channel_id"])
                new_message = await channel.send(embed=embed, view=group_view)
                self.data["panel_message_id"] = new_message.id

            groups = [self.data if g.get("id") == group_id else g for g in groups]
            config[guild_id]["ticket_group_panels"] = groups
            save_config(config)

            result_channel = interaction.guild.get_channel(self.data["panel_channel_id"])
            confirmation = f"✅ Le panel regroupé #{group_id} a été mis à jour dans {result_channel.mention} !"
        else:
            group_id = max((g.get("id", 0) for g in groups), default=0) + 1
            self.data["id"] = group_id
            self.data["panel_message_id"] = None
            groups.append(self.data)
            config[guild_id]["ticket_group_panels"] = groups
            save_config(config)

            channel = interaction.guild.get_channel(self.data["panel_channel_id"])
            group_view = GroupTicketPanelView(self.guild_id, group_id)
            new_message = await channel.send(embed=embed, view=group_view)
            self.data["panel_message_id"] = new_message.id
            groups = [self.data if g.get("id") == group_id else g for g in groups]
            config[guild_id]["ticket_group_panels"] = groups
            save_config(config)

            confirmation = f"✅ Le panel regroupé a été publié dans {channel.mention} ! Il est désormais géré via `/manageticket`."

        for item in self.children:
            item.disabled = True
        await interaction.edit_original_response(content=confirmation, embed=None, view=self)

    @discord.ui.button(label="❌ Annuler", style=discord.ButtonStyle.danger, row=3, custom_id="group_setup_cancel")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="❌ Configuration annulée.", embed=None, view=self)


class GroupPanelChooserSelect(discord.ui.Select):
    def __init__(self, guild: discord.Guild, panels: list, groups: list):
        self.guild = guild
        self.panels = panels
        self.groups = groups
        options = [
            discord.SelectOption(
                label="➕ Créer un nouveau panel regroupé",
                value="new",
                description="Configurer et publier un nouveau message multi-boutons",
                emoji="✨"
            )
        ]
        for g in groups:
            channel = guild.get_channel(g.get("panel_channel_id")) if g.get("panel_channel_id") else None
            channel_desc = f"#{channel.name}" if channel else "salon introuvable"
            options.append(
                discord.SelectOption(
                    label=f"Groupe #{g.get('id')} - {g.get('embed_title', 'Sans titre')}"[:100],
                    value=str(g.get("id")),
                    description=channel_desc[:100],
                    emoji="🗂️"
                )
            )
        super().__init__(
            placeholder="Choisissez un panel regroupé existant à modifier, ou créez-en un nouveau...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "new":
            view = GroupSetupView(self.guild.id, self.panels)
        else:
            group_id = int(self.values[0])
            group_data = next((g for g in self.groups if g.get("id") == group_id), None)
            view = GroupSetupView(self.guild.id, self.panels, group_data=group_data, group_id=group_id)

        await interaction.response.edit_message(
            content=(
                "**🗂️ Configuration d'un panel regroupé**\n"
                "1️⃣ Personnalisez l'embed (titre, description, couleur, bannière), "
                "2️⃣ choisissez le salon, 3️⃣ sélectionnez les panels de tickets à regrouper, "
                "4️⃣ personnalisez le texte affiché pour chaque panel, puis publiez."
            ),
            embed=view.build_preview_embed(),
            view=view
        )


class GroupPanelChooserView(discord.ui.View):
    def __init__(self, guild: discord.Guild, panels: list, groups: list):
        super().__init__(timeout=300)
        self.add_item(GroupPanelChooserSelect(guild, panels, groups))


# --- Modale affichée à l'utilisateur qui ouvre un ticket avec questions ---
class TicketAnswerModal(discord.ui.Modal):
    def __init__(self, guild_id: int, panel_id: int, questions: list):
        super().__init__(title="Ouverture de ticket")
        self.guild_id = guild_id
        self.panel_id = panel_id
        self.inputs = []
        for q in questions[:5]:
            text_input = discord.ui.TextInput(
                label=q["text"][:45],
                style=discord.TextStyle.paragraph,
                required=q["required"],
                max_length=500
            )
            self.add_item(text_input)
            self.inputs.append((q["text"], text_input))

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        answers = [(label, field.value) for label, field in self.inputs if field.value]
        await create_ticket_channel(interaction, self.guild_id, self.panel_id, answers)


# --- Bouton persistant du panel public ("Ouvrir un ticket") ---
class TicketPanelButton(discord.ui.Button):
    def __init__(self, guild_id: int, panel_id: int, label: str, emoji: str = None):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.primary,
            emoji=emoji if emoji else "🎫",
            custom_id=f"ticket_create_{guild_id}_{panel_id}"
        )
        self.guild_id = guild_id
        self.panel_id = panel_id

    async def callback(self, interaction: discord.Interaction):
        cfg = get_ticket_panel(str(self.guild_id), self.panel_id)
        if not cfg:
            await interaction.response.send_message("❌ Le système de tickets n'est plus configuré.", ephemeral=True)
            return

        if cfg.get("questions_enabled") and cfg.get("questions"):
            await interaction.response.send_modal(TicketAnswerModal(self.guild_id, self.panel_id, cfg["questions"]))
        else:
            await interaction.response.defer(ephemeral=True)
            await create_ticket_channel(interaction, self.guild_id, self.panel_id, [])


class TicketPanelView(discord.ui.View):
    def __init__(self, guild_id: int, panel_id: int):
        super().__init__(timeout=None)
        cfg = get_ticket_panel(str(guild_id), panel_id) or {}
        label = cfg.get("button_label", "Ouvrir un ticket")
        emoji = cfg.get("button_emoji", "🎫")
        self.add_item(TicketPanelButton(guild_id, panel_id, label, emoji))


# --- Création effective du salon de ticket ---
async def create_ticket_channel(interaction: discord.Interaction, guild_id: int, panel_id: int, answers: list):
    cfg = get_ticket_panel(str(guild_id), panel_id)
    if not cfg:
        await interaction.followup.send("❌ Le système de tickets n'est plus configuré.", ephemeral=True)
        return

    guild = interaction.guild
    category = guild.get_channel(cfg["category_id"])
    ticket_number = get_next_ticket_number(str(guild_id))

    # Nom du salon basé sur le pseudo de l'utilisateur : "{user}-delivery"
    base_name = f"{slugify_username(interaction.user.name)}-delivery"
    existing_names = {c.name for c in guild.text_channels}
    channel_name = base_name
    suffix = 2
    while channel_name in existing_names:
        channel_name = f"{base_name}-{suffix}"
        suffix += 1

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
    }

    # Plusieurs rôles support peuvent désormais voir le ticket
    support_roles = []
    for role_id in cfg.get("support_role_ids", []):
        role = guild.get_role(role_id)
        if role:
            support_roles.append(role)
            overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

    try:
        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            reason=f"Ticket ouvert par {interaction.user}"
        )
    except discord.Forbidden:
        await interaction.followup.send("❌ Permissions insuffisantes pour créer le salon de ticket.", ephemeral=True)
        return

    description = f"Bonjour {interaction.user.mention}, un membre du support va vous répondre sous peu."
    if support_roles:
        description += "\n" + " ".join(role.mention for role in support_roles)

    embed = discord.Embed(
        title=f"🎫 Ticket #{ticket_number:04d}",
        description=description,
        color=discord.Color.blurple()
    )
    for question_text, answer in answers:
        embed.add_field(name=question_text, value=answer[:1024], inline=False)
    embed.set_footer(text=f"Ouvert par {interaction.user.display_name}")
    embed.timestamp = datetime.datetime.now()

    await ticket_channel.send(embed=embed, view=TicketActionView())
    await interaction.followup.send(f"✅ Votre ticket a été créé : {ticket_channel.mention}", ephemeral=True)


# --- Bouton persistant de fermeture, présent dans chaque salon de ticket ---
class TicketActionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Fermer le ticket", style=discord.ButtonStyle.danger, custom_id="ticket_close_button")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"🔒 Ticket fermé par {interaction.user.mention}. Suppression dans 5 secondes...")

        channel = interaction.channel
        try:
            for target, ow in list(channel.overwrites.items()):
                if isinstance(target, discord.Member):
                    ow.send_messages = False
                    await channel.set_permissions(target, overwrite=ow)
        except discord.Forbidden:
            pass

        await asyncio.sleep(5)
        try:
            await channel.delete(reason=f"Ticket fermé par {interaction.user}")
        except discord.Forbidden:
            await channel.send("❌ Permissions insuffisantes pour supprimer ce salon.")


# --- Commande /setupticket : ouverture du wizard de configuration ---
# Si des panels existent déjà sur le serveur, on propose de les modifier
# avant de pouvoir en créer un nouveau.
@bot.tree.command(name="setupticket", description="Configurer, modifier ou publier un panel de création de tickets.")
@app_commands.default_permissions(administrator=True)
async def setupticket(interaction: discord.Interaction):
    panels = get_ticket_panels(str(interaction.guild.id))

    if panels:
        lines = []
        for p in panels:
            channel = interaction.guild.get_channel(p.get("panel_channel_id")) if p.get("panel_channel_id") else None
            channel_txt = channel.mention if channel else "❌ salon supprimé"
            lines.append(f"**Panel #{p.get('id')}** — {p.get('embed_title', 'Sans titre')} ({channel_txt})")

        embed = discord.Embed(
            title="🎫 Gestion des panels de tickets",
            description="Ce serveur possède déjà des panels de tickets. Choisissez-en un ci-dessous pour le "
                        "modifier, ou créez-en un nouveau.",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Panels existants", value="\n".join(lines), inline=False)

        view = TicketPanelChooserView(interaction.guild, panels)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    else:
        view = TicketSetupView(interaction.guild.id)
        await interaction.response.send_message(
            content=(
                "**🎫 Configuration du système de tickets**\n"
                "1️⃣ Personnalisez l'embed, 2️⃣ choisissez le salon et la catégorie, "
                "3️⃣ activez les questions préalables si besoin, puis publiez."
            ),
            embed=view.build_preview_embed(),
            view=view,
            ephemeral=True
        )


# --- Commande /setupticketgroup : regrouper plusieurs panels existants dans un même message ---
@bot.tree.command(name="setupticketgroup", description="Regrouper plusieurs panels de tickets dans un seul message avec un bouton par panel.")
@app_commands.default_permissions(administrator=True)
async def setupticketgroup(interaction: discord.Interaction):
    panels = get_ticket_panels(str(interaction.guild.id))
    if not panels:
        await interaction.response.send_message(
            "❌ Vous devez d'abord créer au moins un panel de ticket avec `/setupticket` avant de pouvoir les regrouper.",
            ephemeral=True
        )
        return

    groups = get_ticket_group_panels(str(interaction.guild.id))

    if groups:
        lines = []
        for g in groups:
            channel = interaction.guild.get_channel(g.get("panel_channel_id")) if g.get("panel_channel_id") else None
            channel_txt = channel.mention if channel else "❌ salon supprimé"
            lines.append(f"**Groupe #{g.get('id')}** — {g.get('embed_title', 'Sans titre')} ({channel_txt})")

        embed = discord.Embed(
            title="🗂️ Gestion des panels regroupés",
            description="Ce serveur possède déjà des panels regroupés. Choisissez-en un ci-dessous pour le "
                        "modifier, ou créez-en un nouveau.",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Groupes existants", value="\n".join(lines), inline=False)

        view = GroupPanelChooserView(interaction.guild, panels, groups)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    else:
        view = GroupSetupView(interaction.guild.id, panels)
        await interaction.response.send_message(
            content=(
                "**🗂️ Configuration d'un panel regroupé**\n"
                "1️⃣ Personnalisez l'embed (titre, description, couleur, bannière), "
                "2️⃣ choisissez le salon, 3️⃣ sélectionnez les panels de tickets à regrouper, "
                "4️⃣ personnalisez le texte affiché pour chaque panel, puis publiez."
            ),
            embed=view.build_preview_embed(),
            view=view,
            ephemeral=True
        )


# ==================== GESTION DES TICKETS EXISTANTS (/manageticket) ====================
# Permet de modifier ou supprimer un panel de ticket déjà publié, directement
# depuis une liste déroulante, sans devoir tout reconfigurer manuellement.
#
# Dès qu'un panel (individuel via /setupticket ou regroupé via /setupticketgroup)
# est créé, il est automatiquement enregistré dans config.json (ticket_panels /
# ticket_group_panels). /manageticket relit systématiquement cette configuration
# à chaque appel : tout panel nouvellement créé apparaît donc immédiatement dans
# la liste, sans redémarrage ni action supplémentaire.

def build_manage_ticket_embed(guild: discord.Guild, panels: list, groups: list) -> discord.Embed:
    embed = discord.Embed(
        title="🎫 Gestion des panels de tickets",
        description="Choisissez un panel ci-dessous pour le modifier ou le supprimer.",
        color=discord.Color.blurple()
    )
    if panels:
        lines = []
        for p in panels:
            channel = guild.get_channel(p.get("panel_channel_id")) if p.get("panel_channel_id") else None
            channel_txt = channel.mention if channel else "❌ salon supprimé"
            lines.append(f"**Panel #{p.get('id')}** — {p.get('embed_title', 'Sans titre')} ({channel_txt})")
        embed.add_field(name="🎫 Panels individuels", value="\n".join(lines), inline=False)
    if groups:
        lines = []
        for g in groups:
            channel = guild.get_channel(g.get("panel_channel_id")) if g.get("panel_channel_id") else None
            channel_txt = channel.mention if channel else "❌ salon supprimé"
            lines.append(f"**Groupe #{g.get('id')}** — {g.get('embed_title', 'Sans titre')} ({channel_txt})")
        embed.add_field(name="🗂️ Panels regroupés", value="\n".join(lines), inline=False)
    return embed


class ManageTicketSelect(discord.ui.Select):
    def __init__(self, guild: discord.Guild, panels: list, groups: list):
        self.guild = guild
        self.panels = panels
        self.groups = groups
        options = []
        for p in panels:
            channel = guild.get_channel(p.get("panel_channel_id")) if p.get("panel_channel_id") else None
            channel_desc = f"#{channel.name}" if channel else "salon introuvable"
            options.append(
                discord.SelectOption(
                    label=f"Panel #{p.get('id')} - {p.get('embed_title', 'Sans titre')}"[:100],
                    value=f"panel:{p.get('id')}",
                    description=channel_desc[:100],
                    emoji="🎫"
                )
            )
        for g in groups:
            channel = guild.get_channel(g.get("panel_channel_id")) if g.get("panel_channel_id") else None
            channel_desc = f"#{channel.name}" if channel else "salon introuvable"
            options.append(
                discord.SelectOption(
                    label=f"Groupe #{g.get('id')} - {g.get('embed_title', 'Sans titre')}"[:100],
                    value=f"group:{g.get('id')}",
                    description=channel_desc[:100],
                    emoji="🗂️"
                )
            )
        super().__init__(
            placeholder="Choisissez le panel (ou groupe) de ticket à gérer...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        kind, raw_id = self.values[0].split(":")
        item_id = int(raw_id)

        if kind == "panel":
            item_data = next((p for p in self.panels if p.get("id") == item_id), None)
            title_prefix = "panel"
        else:
            item_data = next((g for g in self.groups if g.get("id") == item_id), None)
            title_prefix = "groupe"

        if not item_data:
            await interaction.response.edit_message(content="❌ Cet élément n'existe plus.", embed=None, view=None)
            return

        channel = self.guild.get_channel(item_data.get("panel_channel_id")) if item_data.get("panel_channel_id") else None
        embed = discord.Embed(
            title=f"🎫 Gestion du {title_prefix} #{item_id}",
            description=f"**Titre :** {item_data.get('embed_title', 'Sans titre')}\n"
                        f"**Salon :** {channel.mention if channel else '❌ salon introuvable'}\n\n"
                        "Que souhaitez-vous faire ?",
            color=discord.Color.blurple()
        )
        await interaction.response.edit_message(
            content=None,
            embed=embed,
            view=ManageTicketActionsView(self.guild, kind, item_id)
        )


class ManageTicketSelectView(discord.ui.View):
    def __init__(self, guild: discord.Guild, panels: list, groups: list):
        super().__init__(timeout=300)
        self.add_item(ManageTicketSelect(guild, panels, groups))


class ManageTicketActionsView(discord.ui.View):
    def __init__(self, guild: discord.Guild, kind: str, item_id: int):
        super().__init__(timeout=300)
        self.guild = guild
        self.kind = kind  # "panel" ou "group"
        self.item_id = item_id

    @discord.ui.button(label="✏️ Modifier", style=discord.ButtonStyle.primary, emoji="✏️", custom_id="manage_ticket_edit")
    async def edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.kind == "panel":
            panel_data = get_ticket_panel(str(self.guild.id), self.item_id)
            if not panel_data:
                await interaction.response.edit_message(content="❌ Ce panel n'existe plus.", embed=None, view=None)
                return
            view = TicketSetupView(self.guild.id, panel_data=panel_data, panel_id=self.item_id)
            await interaction.response.edit_message(
                content=(
                    "**🎫 Modification du panel de ticket**\n"
                    "Ajustez les paramètres ci-dessous puis enregistrez les modifications."
                ),
                embed=view.build_preview_embed(),
                view=view
            )
        else:
            group_data = get_ticket_group_panel(str(self.guild.id), self.item_id)
            if not group_data:
                await interaction.response.edit_message(content="❌ Ce groupe n'existe plus.", embed=None, view=None)
                return
            panels = get_ticket_panels(str(self.guild.id))
            view = GroupSetupView(self.guild.id, panels, group_data=group_data, group_id=self.item_id)
            await interaction.response.edit_message(
                content=(
                    "**🗂️ Modification du panel regroupé**\n"
                    "Ajustez les paramètres ci-dessous puis enregistrez les modifications."
                ),
                embed=view.build_preview_embed(),
                view=view
            )

    @discord.ui.button(label="🗑️ Supprimer", style=discord.ButtonStyle.danger, emoji="🗑️", custom_id="manage_ticket_delete")
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        label = "panel" if self.kind == "panel" else "groupe"
        embed = discord.Embed(
            title="⚠️ Confirmation de suppression",
            description=f"Êtes-vous sûr de vouloir supprimer le {label} #{self.item_id} ? "
                        "Le message correspondant sera supprimé et les membres ne pourront plus ouvrir de ticket depuis celui-ci. "
                        "Cette action est irréversible.",
            color=discord.Color.red()
        )
        await interaction.response.edit_message(embed=embed, view=ManageTicketDeleteConfirmView(self.guild, self.kind, self.item_id))

    @discord.ui.button(label="⬅️ Retour", style=discord.ButtonStyle.secondary, custom_id="manage_ticket_back")
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        panels = get_ticket_panels(str(self.guild.id))
        groups = get_ticket_group_panels(str(self.guild.id))
        if not panels and not groups:
            await interaction.response.edit_message(
                content="❌ Il n'y a plus aucun panel de ticket sur ce serveur.",
                embed=None,
                view=None
            )
            return

        embed = build_manage_ticket_embed(self.guild, panels, groups)
        await interaction.response.edit_message(
            content=None,
            embed=embed,
            view=ManageTicketSelectView(self.guild, panels, groups)
        )


class ManageTicketDeleteConfirmView(discord.ui.View):
    def __init__(self, guild: discord.Guild, kind: str, item_id: int):
        super().__init__(timeout=300)
        self.guild = guild
        self.kind = kind
        self.item_id = item_id

    @discord.ui.button(label="✅ Confirmer la suppression", style=discord.ButtonStyle.danger, custom_id="manage_ticket_confirm_delete")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        config = load_config()
        guild_id = str(self.guild.id)

        if self.kind == "panel":
            panels = config.get(guild_id, {}).get("ticket_panels", [])
            item_data = next((p for p in panels if p.get("id") == self.item_id), None)

            if not item_data:
                await interaction.edit_original_response(content="❌ Ce panel n'existe plus.", embed=None, view=None)
                return

            # Suppression du message publié du panel, si celui-ci existe encore
            if item_data.get("panel_message_id") and item_data.get("panel_channel_id"):
                channel = self.guild.get_channel(item_data["panel_channel_id"])
                if channel:
                    try:
                        message = await channel.fetch_message(item_data["panel_message_id"])
                        await message.delete()
                    except (discord.NotFound, discord.Forbidden):
                        pass

            # Retrait du panel de la config, ainsi que de tout panel regroupé qui le référence
            panels = [p for p in panels if p.get("id") != self.item_id]
            config[guild_id]["ticket_panels"] = panels

            groups = config.get(guild_id, {}).get("ticket_group_panels", [])
            for group in groups:
                if self.item_id in group.get("panel_ids", []):
                    group["panel_ids"] = [pid for pid in group["panel_ids"] if pid != self.item_id]
            config[guild_id]["ticket_group_panels"] = groups
            save_config(config)

            confirmation = f"🗑️ Le panel #{self.item_id} a été supprimé avec succès."
        else:
            groups = config.get(guild_id, {}).get("ticket_group_panels", [])
            item_data = next((g for g in groups if g.get("id") == self.item_id), None)

            if not item_data:
                await interaction.edit_original_response(content="❌ Ce groupe n'existe plus.", embed=None, view=None)
                return

            # Suppression du message publié du groupe, si celui-ci existe encore
            if item_data.get("panel_message_id") and item_data.get("panel_channel_id"):
                channel = self.guild.get_channel(item_data["panel_channel_id"])
                if channel:
                    try:
                        message = await channel.fetch_message(item_data["panel_message_id"])
                        await message.delete()
                    except (discord.NotFound, discord.Forbidden):
                        pass

            groups = [g for g in groups if g.get("id") != self.item_id]
            config[guild_id]["ticket_group_panels"] = groups
            save_config(config)

            confirmation = f"🗑️ Le panel regroupé #{self.item_id} a été supprimé avec succès."

        await interaction.edit_original_response(
            content=confirmation,
            embed=None,
            view=None
        )

    @discord.ui.button(label="❌ Annuler", style=discord.ButtonStyle.secondary, custom_id="manage_ticket_cancel_delete")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        label = "panel" if self.kind == "panel" else "groupe"
        embed = discord.Embed(
            title=f"🎫 Gestion du {label} #{self.item_id}",
            description="Suppression annulée. Que souhaitez-vous faire ?",
            color=discord.Color.blurple()
        )
        await interaction.response.edit_message(embed=embed, view=ManageTicketActionsView(self.guild, self.kind, self.item_id))


@bot.tree.command(name="manageticket", description="Modifier ou supprimer un panel de ticket (ou un panel regroupé) existant.")
@app_commands.default_permissions(administrator=True)
async def manageticket(interaction: discord.Interaction):
    panels = get_ticket_panels(str(interaction.guild.id))
    groups = get_ticket_group_panels(str(interaction.guild.id))

    if not panels and not groups:
        await interaction.response.send_message(
            "❌ Aucun panel de ticket n'a encore été créé sur ce serveur. Utilisez `/setupticket` pour en créer un.",
            ephemeral=True
        )
        return

    embed = build_manage_ticket_embed(interaction.guild, panels, groups)
    await interaction.response.send_message(
        embed=embed,
        view=ManageTicketSelectView(interaction.guild, panels, groups),
        ephemeral=True
    )


# --- Serveur HTTP minimal pour garder le bot actif sur Render (Web Service) ---
class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot Discord actif !")

    def log_message(self, format, *args):
        # Empeche de spammer les logs Render à chaque ping
        pass

def run_keep_alive_server():
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), KeepAliveHandler)
    print(f"🌐 Serveur keep-alive lancé sur le port {port}")
    server.serve_forever()

def start_keep_alive():
    thread = threading.Thread(target=run_keep_alive_server, daemon=True)
    thread.start()


# --- Démarrage du bot ---
if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        raise RuntimeError("La variable d'environnement DISCORD_TOKEN n'est pas définie.")

    start_keep_alive()  # Lance le petit serveur HTTP en parallèle pour rester actif sur Render
    bot.run(TOKEN)
