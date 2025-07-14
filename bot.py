import discord
import requests
import asyncio
import logging
import os

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY")
GUILD_ID = int(os.getenv("GUILD_ID") or '1392171241586298880')
TOKEN_ADDRESS = 'So11111111111111111111111111111111111111112'
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
            url = f"https://public-api.birdeye.so/defi/price?address={TOKEN_ADDRESS}&ui_amount_mode=raw"
            headers = {
                "accept": "application/json",
                "x-chain": "solana",
                "X-API-KEY": BIRDEYE_API_KEY
            }

            response = requests.get(url, headers=headers)

            # 🔍 Log the status code and response body
            logging.info(f"Birdeye response: {response.status_code} - {response.text}")

            data = response.json()

            price = data.get('data', {}).get('value')
            if price is None:
                logging.error(f"Price not found in API response: {data}")
                await asyncio.sleep(UPDATE_INTERVAL)
                continue

            formatted_price = f"${price:.6f}"

            # Get 24h change from the same API response
            change_24h = data.get('data', {}).get('priceChange24h')
            if change_24h is not None:
                change_str = f"{change_24h:+.2f}%"
                arrow = "📈" if change_24h > 0 else "📉"
                activity = discord.Activity(type=discord.ActivityType.watching, name=f"24h: {change_str} {arrow}")
                await client.change_presence(activity=activity)
                logging.info(f"Updated presence: Watching 24h: {change_str}")
            else:
                logging.warning("24h change not found in API response.")

            guild = discord.utils.get(client.guilds, id=GUILD_ID)
            if guild is None:
                logging.error("Guild not found. Check GUILD_ID.")
                await asyncio.sleep(UPDATE_INTERVAL)
                continue
            member = guild.get_member(client.user.id)
            if member is None:
                logging.error("Bot member not found in guild.")
                await asyncio.sleep(UPDATE_INTERVAL)
                continue
            await member.edit(nick=formatted_price)
            logging.info("Nickname updated.")
            role_name = "PriceBotSolColor"  # Name of the role you want to recolor

            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                if change_24h > 0:
                    await role.edit(color=discord.Color.green())
                    logging.info("Set role color to green 📈")
                else:
                    await role.edit(color=discord.Color.red())
                    logging.info("Set role color to red 📉")
            else:
                logging.warning(f"Role '{role_name}' not found in guild.")

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
