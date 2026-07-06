# Guide d'hébergement gratuit 24h/24 🌐

Pour faire tourner votre bot Discord en continu (24h/24 et 7j/7) sans laisser votre propre ordinateur allumé, voici les meilleures solutions gratuites en 2026.

---

## Option 1 : Render.com (Recommandé & Facile) 🌟

Render est une plateforme cloud gratuite très populaire. Par défaut, les applications gratuites s'endorment s'il n'y a pas d'activité. C'est pourquoi nous avons ajouté un **serveur web minimaliste** dans le code de `bot.py` pour pouvoir le garder éveillé à l'aide d'un ping régulier.

### Étapes de mise en place :

1. **Créer un dépôt GitHub** :
   - Mettez vos fichiers (`bot.py` et `requirements.txt`) sur un dépôt GitHub privé ou public.
   - Ne mettez **PAS** votre token Discord en clair sur GitHub ! Utilisez une variable d'environnement (voir étape 3).

2. **Créer un compte sur Render** :
   - Allez sur [Render.com](https://render.com/) et connectez-vous avec votre compte GitHub.
   - Cliquez sur **New +** -> **Web Service**.
   - Connectez votre dépôt GitHub.

3. **Configurer le Web Service** :
   - **Name** : `mvp-rules-bot` (ou ce que vous voulez).
   - **Language** : `Python`.
   - **Build Command** : `pip install -r requirements.txt`.
   - **Start Command** : `python bot.py`.
   - **Instance Type** : `Free`.
   - Cliquez sur **Advanced** pour ajouter des variables d'environnement (Environment Variables) :
     - Ajoutez la clé `PORT` avec la valeur `8080`.
     - Ajoutez la clé `YOUR_TOKEN_HERE` (ou configurez le code pour lire `os.environ.get('DISCORD_TOKEN')` si vous le souhaitez) ou modifiez la ligne `TOKEN = "..."` de `bot.py` pour y placer directement le token (uniquement si votre dépôt GitHub est **strictement privé**).
     *Recommandation de sécurité : Modifiez la ligne `TOKEN = "YOUR_TOKEN_HERE"` par `TOKEN = os.environ.get("DISCORD_TOKEN")` dans `bot.py` et ajoutez `DISCORD_TOKEN` dans Render.*

4. **Garder le bot éveillé (Anti-veille)** :
   - Une fois déployé, Render va vous donner une URL publique (ex: `https://mvp-rules-bot.onrender.com`).
   - Rendez-vous sur un service de ping gratuit comme [UptimeRobot](https://uptimerobot.com/) ou [cron-job.org](https://cron-job.org/).
   - Créez un moniteur de type **HTTPS** pointant vers votre URL Render avec un intervalle de **5 à 10 minutes**.
   - Le ping régulier va empêcher Render d'endormir votre bot, assurant un fonctionnement 24h/24 !

---

## Option 2 : Koyeb ⚡

Koyeb est une excellente alternative à Render. Leur offre gratuite (Free Tier) inclut 1 service "Nano" qui **ne s'endort pas**. Cependant, Koyeb nécessite la validation d'une carte bancaire à l'inscription pour éviter les abus (aucun prélèvement n'est effectué).

### Étapes :
1. Créez un compte sur [Koyeb.com](https://www.koyeb.com/).
2. Connectez votre dépôt GitHub.
3. Créez un service en sélectionnant votre dépôt.
4. Spécifiez la commande de démarrage : `python bot.py`.
5. Ajoutez votre token dans les variables d'environnement.

---

## Option 3 : Hébergement Local (Vieux PC ou Raspberry Pi) 🏠

Si vous possédez un mini-ordinateur comme un **Raspberry Pi** ou un vieux PC portable/bureau inutilisé :
- Vous pouvez le laisser tourner chez vous.
- La consommation électrique d'un Raspberry Pi est minime (environ 3 à 5 Watts), ce qui en fait une solution d'hébergement physique gratuite, privée, sans limite de temps et sans dépendance à un fournisseur cloud externe.
