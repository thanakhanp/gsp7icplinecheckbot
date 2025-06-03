#main.py
'''This code is for running discord bot for save photo on construction line check 
  1.create folder YYMMDD for each day the photo was sent
  2.rename photo to YYmmddhhmm_caption and save for the folder in that day'''

######################################################################################################################
import discord
import os
import requests
from flask import Flask
from threading import Thread
from datetime import datetime
import pytz

### for get token and webhook from pipedream ###
TOKEN = os.environ.get("TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

### Listen for message in discord ###
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

### Set up flask for web server ###
app = Flask('')
@app.route('/')
def home():
    return "🤖 Discord bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

# Run Flask server in background
Thread(target=run).start()

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")

@client.event
async def on_message(message):
    print(f"[LOG] New message from {message.author}: {message.content}")

    if message.content.strip() == "!status":
        await message.channel.send(f"✅ I’m alive as {client.user}\n Please send me a photo to save it.")
        return

    if message.author.bot:
        print("[LOG] Ignored bot message")
        return

    # ⏰ Restrict to 08:00–22:00 Thai time
    tz = pytz.timezone("Asia/Bangkok")
    now = datetime.now(tz)
    if now.hour < 8 or now.hour >= 22:
        print("[LOG] Outside active hours. Ignoring message.")
        return

    ### Protect no attachement	###
    if not message.attachments:
        print("[LOG] Message received without attachment. Skipping.")
        return

    print(f"[LOG] {len(message.attachments)} attachment(s) found")
    caption = message.content.strip().replace("/", "_") or "no_caption"
    timestamp = now.strftime("%Y%m%d%H%M")
    folder_name = now.strftime("%Y%m%d")
    attachments = message.attachments

    ### If 1 filename	###
    if len(attachments) == 1:
        attachment = attachments[0]
        filename = f"{timestamp}_{caption}"
        print(f"[LOG] Sending file: {filename}")

        data = {
            "filename": attachment.filename,
            "url": attachment.url,
            "author": str(message.author),
            "channel": str(message.channel),
            "folder": folder_name,
            "renamed": filename
        }

        try:
            res = requests.post(WEBHOOK_URL, json=data)
            print(f"[LOG] Sent to Pipedream. Response: {res.status_code}")
            if res.status_code == 200:
                await message.channel.send(f"✅ File `{filename}` was already uploaded")
            else:
                await message.channel.send(f"❌ Failed to upload `{filename}`")
        except Exception as e:
            print(f"[ERROR] Failed to send to Pipedream: {e}")
            await message.channel.send(f"❌ Upload error: {e}")

    ### Else More than 1 files	###
    else:
        for i, attachment in enumerate(attachments, start=1):
            filename = f"{timestamp}_{caption}_{i}"
            print(f"[LOG] Sending file: {filename}")

            data = {
                "filename": attachment.filename,
                "url": attachment.url,
                "author": str(message.author),
                "channel": str(message.channel),
                "folder": folder_name,
                "renamed": filename
            }

            try:
                res = requests.post(WEBHOOK_URL, json=data)
                print(f"[LOG] Sent to Pipedream. Response: {res.status_code}")
                if res.status_code == 200:
                    await message.channel.send(f"✅ File `{filename}` was already uploaded")
                else:
                    await message.channel.send(f"❌ Failed to upload `{filename}`")
            except Exception as e:
                print(f"[ERROR] Failed to send to Pipedream: {e}")
                await message.channel.send(f"❌ Upload error: {e}")

client.run(TOKEN)
