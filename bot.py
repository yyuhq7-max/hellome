import discord
from discord.ext import commands
from discord import app_commands
import os
import json
import re
import datetime
import random
import asyncio
import threading
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


# --- Dashboard de configuration central (/setup) ---
class SetupDashboardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Rôle Automatique (Autorole)", style=discord.ButtonStyle.primary, emoji="👤", custom_id="dashboard_autorole")
    async def configure_autorole(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="👤 Configuration de l'Autorole",
            description="Choisissez dans le menu déroulant ci-dessous le rôle à attribuer automatiquement aux nouveaux membres dès leur arrivée.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=AutoroleView(), ephemeral=True)

    @discord.ui.button(label="Rôle par Bouton (Self-Role)", style=discord.ButtonStyle.secondary, emoji="🎭", custom_id="dashboard_selfrole")
    async def configure_selfrole(self, interaction: discord.Interaction, button: discord.ui.Button):
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


# --- Système de participation pour les Giveaways ---
class GiveawayView(discord.ui.View):
    def __init__(self, prize, winners_count):
        super().__init__(timeout=None)
        self.prize = prize
        self.winners_count = winners_count
        self.participants = set()

    @discord.ui.button(label="Rejoindre ! 🎉", style=discord.ButtonStyle.success, custom_id="giveaway_join")
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.participants:
            self.participants.remove(interaction.user.id)
            await interaction.response.send_message("❌ Vous avez retiré votre participation.", ephemeral=True)
        else:
            self.participants.add(interaction.user.id)
            await interaction.response.send_message("🎉 Votre participation a été enregistrée !", ephemeral=True)
        
        embed = interaction.message.embeds[0]
        embed.set_footer(text=f"Participants : {len(self.participants)}")
        await interaction.message.edit(embed=embed)


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

        # Ré-enregistrement de tous les boutons de rôle déjà configurés
        config = load_config()
        for guild_id, guild_config in config.items():
            for entry in guild_config.get("selfroles", []):
                self.add_view(SelfRoleView(entry["role_id"], entry["label"], entry.get("emoji")))

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

@bot.event
async def on_message(message: discord.Message):
    # Ignorer les messages de bots pour éviter les boucles infinies
    if message.author.bot:
        return

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
                    "🎭 **Rôle par Bouton (Self-Role)** : Créer un embed avec un bouton entièrement personnalisable (titre, description, couleur, texte et emoji du bouton) permettant aux membres d'obtenir un rôle.",
        color=discord.Color.orange()
    )
    await interaction.response.send_message(embed=embed, view=SetupDashboardView(), ephemeral=True)


# --- Commandes de Contenu (Sondage / Annonce / Embed) ---
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
        await interaction.response.edit_message(embed=self.setup_view.build_preview_embed(), view=self.setup_view)


class GroupSetupView(discord.ui.View):
    def __init__(self, guild_id: int, panels: list, group_data: dict = None, group_id: int = None):
        super().__init__(timeout=900)
        self.guild_id = guild_id
        self.editing_group_id = group_id
        self.panels = panels

        if group_data:
            self.data = json.loads(json.dumps(group_data))
            self.data.setdefault("panel_ids", [])
        else:
            self.data = {
                "embed_title": "🎫 Support, 24/7",
                "embed_description": "Cliquez sur un bouton ci-dessous pour ouvrir le ticket correspondant.",
                "embed_color": "bleu",
                "image_url": None,
                "panel_channel_id": None,
                "panel_ids": []
            }

        self.add_item(GroupPanelChannelSelect(self))
        if panels:
            self.add_item(GroupPanelsMultiSelect(self, panels))
        self.refresh_buttons()

    def build_preview_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=self.data["embed_title"],
            description=self.data["embed_description"],
            color=parse_color(self.data["embed_color"])
        )
        if self.data.get("image_url"):
            embed.set_image(url=self.data["image_url"])

        included = []
        for pid in self.data.get("panel_ids", []):
            p = next((x for x in self.panels if x.get("id") == pid), None)
            if p:
                included.append(f"• {p.get('button_emoji') or '🎫'} {p.get('button_label', 'Ouvrir un ticket')} (panel #{pid})")

        status_lines = [
            f"**Salon du panel :** <#{self.data['panel_channel_id']}>" if self.data["panel_channel_id"] else "**Salon du panel :** ❌ non défini",
            "**Panels inclus :**\n" + ("\n".join(included) if included else "❌ aucun panel sélectionné")
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

        embed = self.build_preview_embed()
        # On retire le champ de statut (uniquement utile dans l'aperçu de configuration)
        embed.clear_fields()

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
                "2️⃣ choisissez le salon, 3️⃣ sélectionnez les panels de tickets à regrouper, puis publiez."
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
                "2️⃣ choisissez le salon, 3️⃣ sélectionnez les panels de tickets à regrouper, puis publiez."
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
