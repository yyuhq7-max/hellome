import discord
from discord.ext import commands
from discord import app_commands
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

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
                description="Leer las reglas del serveur de revente MVP en Español", 
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

class RulesBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(RulesView())
        await self.tree.sync()

bot = RulesBot()

@bot.event
async def on_ready():
    print(f"✅ Bot connecté avec succès en tant que {bot.user.name}")
    print("Prêt à afficher les règles de revente via le menu déroulant !")

@bot.tree.command(name="setuprules", description="Configure et affiche le panneau de sélection de langue pour les règles.")
@app_commands.describe(
    titre="Le titre de l'embed des règles (ex: Conditions d'utilisation)",
    description="La description ou message d'accueil de l'embed",
    couleur="Couleur de l'embed (options : bleu, vert, rouge, violet, or, gris)"
)
@app_commands.choices(couleur=[
    app_commands.Choice(name="Bleu", value="bleu"),
    app_commands.Choice(name="Vert", value="vert"),
    app_commands.Choice(name="Rouge", value="rouge"),
    app_commands.Choice(name="Violet", value="violet"),
    app_commands.Choice(name="Or", value="or"),
    app_commands.Choice(name="Gris", value="gris")
])
@app_commands.default_permissions(administrator=True)
async def setuprules(
    interaction: discord.Interaction,
    titre: str = "MVP Terms of Service / Server Rules",
    description: str = "Please select your preferred language below to read the MVP server rules.\n\nVeuillez sélectionner votre langue ci-dessous pour lire les règles du serveur MVP.",
    couleur: str = "bleu"
):
    color_map = {
        "bleu": discord.Color.blue(),
        "vert": discord.Color.green(),
        "rouge": discord.Color.red(),
        "violet": discord.Color.purple(),
        "or": discord.Color.gold(),
        "gris": discord.Color.light_grey()
    }
    embed_color = color_map.get(couleur, discord.Color.blue())

    embed = discord.Embed(
        title=titre,
        description=description,
        color=embed_color
    )

    await interaction.response.send_message("✅ Le panneau des règles a été généré avec succès !", ephemeral=True)
    await interaction.channel.send(embed=embed, view=RulesView())

class SimpleWebServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleWebServer)
    print(f"ℹ️ Serveur web démarré sur le port {port} pour le maintien en ligne.")
    server.serve_forever()

if __name__ == "__main__":
    TOKEN = os.environ.get("DISCORD_TOKEN", "VOTRE_TOKEN_ICI")
    
    if TOKEN == "VOTRE_TOKEN_ICI":
        print("❌ Veuillez configurer le TOKEN de votre bot Discord dans bot.py ou via la variable d'environnement DISCORD_TOKEN.")
    else:
        threading.Thread(target=run_web_server, daemon=True).start()
        bot.run(TOKEN)
