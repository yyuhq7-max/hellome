import discord
from discord.ext import commands
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# Resell server rules in French, English, Spanish, and German for MVP
RULES = {
    "fr": (
        "📜 **RÈGLES DE REVENTE MVP (RESELL)** 📜\n\n"
        "1. **Respect & Civilité** : Soyez courtois et respectueux envers tous les membres. Les insultes, les menaces et les comportements toxiques sont interdits.\n"
        "2. **Légitimité des transactions** : Les arnaques (scams), la vente de contrefaçons non déclarées et le recel d'objets volés sont strictement interdits sous peine de ban définitif.\n"
        "3. **Format des annonces** : Utilisez obligatoirement les salons dédiés (`#wts` pour vendre, `#wtb` pour acheter, `#wtt` pour échanger) et respectez le format d'annonce demandé.\n"
        "4. **Pas de vol de vente (Sniping)** : Il est interdit de contacter en privé un acheteur/vendeur qui est déjà en cours de négociation publique avec un autre membre.\n"
        "5. **Avertissement (Disclaimer)** : L'équipe de modération décline toute responsabilité en cas de litige lors d'une transaction. Utilisez un intermédiaire de confiance (Middleman) si nécessaire."
    ),
    "en": (
        "📜 **MVP RESELL SERVER RULES** 📜\n\n"
        "1. **Respect & Civility**: Be polite and respectful to all members. Insults, threats, and toxicity are strictly prohibited.\n"
        "2. **Legitimate Deals**: Scams, undeclared counterfeits, and selling stolen items are strictly forbidden and will result in a permanent ban.\n"
        "3. **Format of Listings**: You must use the dedicated channels (`#wts` to sell, `#wtb` to buy, `#wtt` to trade) and follow the required listing template.\n"
        "4. **No Sniping**: Do not privately message a buyer or seller who is already publicly negotiating with another member.\n"
        "5. **Disclaimer**: The moderation team is not responsible for any issues or disputes during transactions. Use a trusted Middleman if necessary."
    ),
    "es": (
        "📜 **REGLAS DE REVENTA MVP** 📜\n\n"
        "1. **Respeto y Civilidad**: Sé cortés y respetuoso con todos. No se tolerarán insultos, amenazas ni comportamientos tóxicos.\n"
        "2. **Tratos Legítimos**: Las estafas (scams), la venta de réplicas no declaradas y el comercio de artículos robados están prohibidos y resultarán en un baneo permanente.\n"
        "3. **Formato de Anuncios**: Debes usar los canales correctos (`#wts` para vender, `#wtb` para comprar, `#wtt` para intercambiar) y seguir la plantilla establecida.\n"
        "4. **No Interferir (Sniping)**: Está prohibido contactar en privado a un miembro que ya esté negociando públicamente con otro vendedor/comprador.\n"
        "5. **Descargo de Responsabilidad**: El equipo de moderación no se hace responsable de ningún inconveniente en las transacciones. Usa un intermediario (Middleman) de confianza si es necesario."
    ),
    "de": (
        "📜 **MVP RESELL-SERVER REGELN** 📜\n\n"
        "1. **Respekt & Höflichkeit**: Gehen Sie höflich und respektvoll mit allen Mitgliedern um. Beleidigungen, Drohungen und Toxizität sind strengstens verboten.\n"
        "2. **Legitime Geschäfte**: Betrug (Scams), der Verkauf nicht deklarierierter Fälschungen sowie Diebesgut sind verboten und führen zu einem dauerhaften Bann.\n"
        "3. **Format der Angebote**: Nutzen Sie zwingend die dafür vorgesehenen Kanäle (`#wts` für Verkauf, `#wtb` für Kauf, `#wtt` für Tausch) und halten Sie sich an die Vorlage.\n"
        "4. **Kein Sniping**: Es ist verboten, Käufer oder Verkäufer privat anzuschreiben, wenn diese bereits öffentlich mit einem anderen Mitglied verhandeln.\n"
        "5. **Haftungsausschluss**: Das Moderationsteam übernimmt keine Haftung für Transaktionen oder Streitigkeiten. Nutzen Sie bei Bedarf einen vertrauenswürdigen Mittelsmann (Middleman)."
    )
}

class LanguageSelect(discord.ui.Select):
    def __init__(self):
        # Dropdown options with flags for each language/country
        options = [
            discord.SelectOption(
                label="English", 
                description="Read the MVP resell server rules in English", 
                emoji="🇬🇧", 
                value="en"
            ),
            discord.SelectOption(
                label="Français", 
                description="Lire les règles du serveur de revente MVP en Français", 
                emoji="🇫🇷", 
                value="fr"
            ),
            discord.SelectOption(
                label="Español", 
                description="Leer las reglas del servidor de reventa MVP en Español", 
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
        # Persistent custom ID
        super().__init__(
            placeholder="Choose a language / Choisissez une langue...", 
            min_values=1, 
            max_values=1, 
            options=options, 
            custom_id="persistent_rules_select"
        )

    async def callback(self, interaction: discord.Interaction):
        # Retrieve selected language key
        selected_lang = self.values[0]
        rules_text = RULES.get(selected_lang, "Rules not found.")
        
        # ephemeral=True makes the rules visible ONLY to the user who clicked
        await interaction.response.send_message(rules_text, ephemeral=True)

class RulesView(discord.ui.View):
    def __init__(self):
        # timeout=None allows the view to stay active forever
        super().__init__(timeout=None)
        self.add_item(LanguageSelect())

class RulesBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Re-register the persistent view upon bot start
        self.add_view(RulesView())

bot = RulesBot()

@bot.event
async def on_ready():
    print(f"✅ Bot successfully connected as {bot.user.name}")
    print("Ready to display resell rules via the dropdown menu!")

@bot.command(name="setup_rules")
@commands.has_permissions(administrator=True)
async def setup_rules(ctx: commands.Context):
    """Administrator command to send the language selection embed"""
    embed = discord.Embed(
        title="MVP Terms of Service / Server Rules",
        description="Please select your preferred language below to read the MVP server rules.\n\n"
                    "Veuillez sélectionner votre langue ci-dessous pour lire les règles du serveur MVP.",
        color=discord.Color.blue()
    )
    # Send the embed message with the select menu view
    await ctx.send(embed=embed, view=RulesView())
    await ctx.message.delete() # Cleans up the chat by deleting the !setup_rules command trigger

class SimpleWebServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_web_server():
    # Hosting platforms (like Render) specify a PORT environment variable
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleWebServer)
    print(f"ℹ️ Web server started on port {port} for hosting keep-alive.")
    server.serve_forever()

# Replace 'YOUR_TOKEN_HERE' with your actual bot token from the Discord Developer Portal
if __name__ == "__main__":
    TOKEN = "YOUR_TOKEN_HERE"
    if TOKEN == "YOUR_TOKEN_HERE":
        print("❌ Please configure your Discord TOKEN in bot.py before running the bot.")
    else:
        # Start a lightweight web server in a background thread for hosting platforms (Render, Koyeb, etc.)
        threading.Thread(target=run_web_server, daemon=True).start()
        bot.run(TOKEN)
