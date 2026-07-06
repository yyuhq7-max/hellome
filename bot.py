import discord
from discord.ext import commands
from discord import app_commands
import os
import json
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
    "gris": discord.Color.light_grey()
}

COLOR_CHOICES = [
    app_commands.Choice(name="Bleu", value="bleu"),
    app_commands.Choice(name="Vert", value="vert"),
    app_commands.Choice(name="Rouge", value="rouge"),
    app_commands.Choice(name="Violet", value="violet"),
    app_commands.Choice(name="Or", value="or"),
    app_commands.Choice(name="Gris", value="gris")
]

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


# --- Modal et Composants pour la réponse automatique dans un salon ---
class AutoresponderModal(discord.ui.Modal):
    def __init__(self, channel_id: int):
        super().__init__(title="Message de Réponse Automatique")
        self.channel_id = channel_id

        # Champ de saisie pour le message facultatif à renvoyer automatiquement
        self.response_text = discord.ui.TextInput(
            label="Message textuel facultatif (laisser vide pour l'image seule) :",
            style=discord.TextStyle.paragraph,
            placeholder="Ex : Merci pour votre vouch ! La team MVP vous remercie.",
            required=False,
            max_length=1500
        )
        self.add_item(self.response_text)

    async def on_submit(self, interaction: discord.Interaction):
        config = load_config()
        guild_id = str(interaction.guild.id)
        if guild_id not in config:
            config[guild_id] = {}
        
        config[guild_id]["autoresponder_channel"] = self.channel_id
        config[guild_id]["autoresponder_message"] = self.response_text.value
        save_config(config)

        channel = interaction.guild.get_channel(self.channel_id)
        channel_mention = channel.mention if channel else f"Salon ID: {self.channel_id}"

        msg_val = self.response_text.value if self.response_text.value else "(Seulement l'image)"
        await interaction.response.send_message(
            f"✅ **Répondeur automatique activé** avec l'image `vouch.png` !\n"
            f"• **Salon ciblé :** {channel_mention}\n"
            f"• **Texte configuré :** {msg_val}",
            ephemeral=True
        )

class ChannelSelect(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(
            placeholder="Sélectionnez le salon textuel ciblé...",
            min_values=1,
            max_values=1,
            channel_types=[discord.ChannelType.text],
            custom_id="persistent_autoresponder_channel_select"
        )

    async def callback(self, interaction: discord.Interaction):
        channel = self.values[0]
        # Ouvrir la boîte modale de saisie de texte à la sélection du salon
        await interaction.response.send_modal(AutoresponderModal(channel.id))

class AutoresponderChannelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ChannelSelect())


# --- Composants UI pour la configuration du Rôle par Bouton (Self-Role) ---
class SelfRoleModal(discord.ui.Modal):
    def __init__(self, role_id: int):
        super().__init__(title="Configuration du Rôle par Bouton")
        self.role_id = role_id

        self.embed_titre = discord.ui.TextInput(
            label="Titre de l'embed (facultatif)",
            placeholder="Ex : Obtenir le rôle Notifications",
            required=False,
            max_length=100
        )
        self.embed_texte = discord.ui.TextInput(
            label="Texte de l'embed (facultatif)",
            style=discord.TextStyle.paragraph,
            placeholder="Ex : Cliquez sur le bouton ci-dessous pour obtenir ce rôle.",
            required=False,
            max_length=1000
        )
        self.bouton_texte = discord.ui.TextInput(
            label="Texte du bouton",
            placeholder="Ex : Obtenir le rôle",
            required=True,
            max_length=80
        )
        self.add_item(self.embed_titre)
        self.add_item(self.embed_texte)
        self.add_item(self.bouton_texte)

    async def on_submit(self, interaction: discord.Interaction):
        role = interaction.guild.get_role(self.role_id)
        if not role:
            await interaction.response.send_message("❌ Rôle introuvable.", ephemeral=True)
            return

        embed = discord.Embed(
            title=self.embed_titre.value if self.embed_titre.value else f"🎭 Rôle : {role.name}",
            description=self.embed_texte.value if self.embed_texte.value else "Cliquez sur le bouton ci-dessous pour obtenir ou retirer ce rôle.",
            color=discord.Color.blurple()
        )

        view = SelfRoleView(role.id, self.bouton_texte.value)

        # Sauvegarde de la configuration pour pouvoir ré-enregistrer le bouton après un redémarrage
        config = load_config()
        guild_id = str(interaction.guild.id)
        if guild_id not in config:
            config[guild_id] = {}
        selfroles = config[guild_id].get("selfroles", [])
        # On évite les doublons pour un même rôle
        selfroles = [entry for entry in selfroles if entry.get("role_id") != role.id]
        selfroles.append({"role_id": role.id, "label": self.bouton_texte.value})
        config[guild_id]["selfroles"] = selfroles
        save_config(config)

        await interaction.response.send_message("✅ Le bouton de rôle automatique a été créé !", ephemeral=True)
        await interaction.channel.send(embed=embed, view=view)


class SelfRoleButton(discord.ui.Button):
    def __init__(self, role_id: int, label: str):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.primary,
            emoji="🎭",
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
    def __init__(self, role_id: int, label: str):
        super().__init__(timeout=None)
        self.add_item(SelfRoleButton(role_id, label))


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
        # Ouvrir la modale pour personnaliser le texte de l'embed et du bouton
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

    @discord.ui.button(label="Répondeur de Salon (Auto-Response)", style=discord.ButtonStyle.success, emoji="💬", custom_id="dashboard_autoresponder")
    async def configure_autoresponder(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="💬 Configuration du Répondeur automatique",
            description="Sélectionnez le salon ci-dessous. Dès qu'un message y sera envoyé, le bot supprimera l'ancienne image et enverra la nouvelle image `vouch.png`.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, view=AutoresponderChannelView(), ephemeral=True)

    @discord.ui.button(label="Rôle par Bouton (Self-Role)", style=discord.ButtonStyle.secondary, emoji="🎭", custom_id="dashboard_selfrole")
    async def configure_selfrole(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🎭 Configuration du Rôle par Bouton",
            description="Sélectionnez le rôle que les membres pourront obtenir (ou retirer) en cliquant sur un bouton. Vous pourrez ensuite personnaliser le titre, le texte de l'embed et le texte du bouton.",
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
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Ré-enregistrement des vues persistantes pour éviter de les perdre aux reboots
        self.add_view(RulesView())
        self.add_view(AutoroleView())
        self.add_view(AutoresponderChannelView())
        self.add_view(SetupDashboardView())
        self.add_view(SelfRoleConfigView())

        # Ré-enregistrement de tous les boutons de rôle automatique déjà configurés
        config = load_config()
        for guild_id, guild_config in config.items():
            for entry in guild_config.get("selfroles", []):
                self.add_view(SelfRoleView(entry["role_id"], entry["label"]))
        
        # Synchronisation globale des commandes slash
        await self.tree.sync()

bot = RulesBot()


# --- Événements du Bot ---
@bot.event
async def on_ready():
    print(f"✅ Bot connecté avec succès en tant que {bot.user.name}")
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

@bot.event
async def on_message(message: discord.Message):
    # Ignorer les messages de bots pour éviter les boucles infinies
    if message.author.bot:
        return

    # Vérification du répondeur automatique de salon
    config = load_config()
    guild_id = str(message.guild.id) if message.guild else None

    if guild_id and guild_id in config:
        target_channel_id = config[guild_id].get("autoresponder_channel")
        response_msg = config[guild_id].get("autoresponder_message")

        # Si le message est dans le salon ciblé
        if target_channel_id and message.channel.id == target_channel_id:
            # 1. Tenter de supprimer la dernière image envoyée par le bot
            last_msg_id = config[guild_id].get("autoresponder_last_msg")
            if last_msg_id:
                try:
                    old_msg = await message.channel.fetch_message(last_msg_id)
                    await old_msg.delete()
                except Exception:
                    pass # Le message a pu être supprimé manuellement ou n'existe plus

            # 2. Envoyer la nouvelle image vouch.png (et le texte si configuré)
            try:
                file = None
                if os.path.exists("vouch.png"):
                    file = discord.File("vouch.png")

                # Envoi du message
                new_msg = await message.channel.send(
                    content=response_msg if response_msg else None,
                    file=file
                )

                # 3. Enregistrer l'ID de ce nouveau message
                config[guild_id]["autoresponder_last_msg"] = new_msg.id
                save_config(config)
            except discord.Forbidden:
                print(f"❌ Répondeur : Droits d'écriture ou d'envoi de fichiers manquants dans #{message.channel.name}.")

    # Important : permet aux commandes slash et classiques de fonctionner
    await bot.process_commands(message)


# --- Commandes d'Administration & Configuration ---
@bot.tree.command(name="setuprules", description="Affiche le panneau de sélection de langue pour les règles.")
@app_commands.describe(
    titre="Le titre de l'embed des règles (ex: Conditions d'utilisation)",
    description="La description ou message d'accueil de l'embed",
    couleur="Couleur de l'embed (options : bleu, vert, rouge, violet, or, gris)"
)
@app_commands.choices(couleur=COLOR_CHOICES)
@app_commands.default_permissions(administrator=True)
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
                    "💬 **Répondeur de Salon** : Envoyer une image automatique et supprimer la précédente à chaque envoi.\n"
                    "🎭 **Rôle par Bouton (Self-Role)** : Créer un message avec un bouton permettant aux membres de s'attribuer un rôle.",
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


# --- Démarrage du bot ---
# NOTE : le fichier original fourni était tronqué à ce stade (fin de /clear).
# Complétez ci-dessous avec vos éventuelles commandes additionnelles, puis lancez le bot
# avec le token stocké dans une variable d'environnement (ne jamais coder le token en dur).
if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        raise RuntimeError("La variable d'environnement DISCORD_TOKEN n'est pas définie.")
    bot.run(TOKEN)
