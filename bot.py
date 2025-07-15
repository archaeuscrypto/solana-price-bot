import discord
import requests
import asyncio
import logging
import os
import json

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_IDS = json.loads(os.getenv("GUILD_IDS_JSON", "[]"))
COINGECKO_ID = "solana"
UPDATE_INTERVAL = 60  # seconds

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.presences = True

client = discord.Client(intents=intents)

async def update_price_nickname():
    await client.wait_until_ready()
    while not client.is_closed():
        try:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={COINGECKO_ID}&vs_currencies=usd&include_24hr_change=true"
            response = requests.get(url)
            logging.info(f"CoinGecko response: {response.status_code} - {response.text}")

            data = response.json()
            token_data = data.get(COINGECKO_ID)
            if not token_data:
                logging.error(f"Solana data not found in response: {data}")
                await asyncio.sleep(UPDATE_INTERVAL)
                continue

            price = token_data.get("usd")
            change_24h = token_data.get("usd_24h_change")

            if price is None:
                logging.error("Price missing from CoinGecko response.")
                await asyncio.sleep(UPDATE_INTERVAL)
                continue

            formatted_price = f"${price:.2f}"

            if change_24h is not None:
                change_str = f"{change_24h:+.2f}%"
                arrow = "📈" if change_24h > 0 else "📉"
                activity = discord.Activity(type=discord.ActivityType.watching, name=f"24h: {change_str} {arrow}")
                await client.change_presence(activity=activity)
                logging.info(f"Updated presence: Watching 24h: {change_str}")
            else:
                logging.warning("24h change not found in API response.")

            for guild_id in GUILD_IDS:
                guild = discord.utils.get(client.guilds, id=guild_id)
                if guild is None:
                    logging.error(f"Guild {guild_id} not found.")
                    continue

                member = guild.get_member(client.user.id)
                if member is None:
                    logging.error(f"Bot member not found in guild {guild_id}.")
                    continue

                await member.edit(nick=formatted_price)
                logging.info(f"Nickname updated in guild {guild.name}.")

                role_name = "PriceBotSolColor"
                role = discord.utils.get(guild.roles, name=role_name)
                if role:
                    color = discord.Color.green() if change_24h > 0 else discord.Color.red()
                    await role.edit(color=color)
                    logging.info(f"Updated role color in {guild.name}.")
                else:
                    logging.warning(f"Role '{role_name}' not found in {guild.name}.")

        except Exception as e:
            logging.error(f"Error updating nickname: {e}")
        await asyncio.sleep(UPDATE_INTERVAL)

@client.event
async def on_ready():
    logging.info(f"Logged in as {client.user}")
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Starting..."))
    client.loop.create_task(update_price_nickname())

def main():
    logging.basicConfig(level=logging.INFO)
    client.run(DISCORD_TOKEN)

if __name__ == "__main__":
    main()