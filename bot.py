#!/usr/bin/env python

from asyncio import TimeoutError
import discord
import sys
import re
from concurrent.futures import ThreadPoolExecutor
import threading
import logging
import datetime
import aiohttp
import config
import random
import time
from timers import Timer

# noinspection PyArgumentList
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(config.LOG_FILE, 'a', 'utf-8'),
        logging.StreamHandler(sys.stdout)
    ])
    

TOKEN_AUTH = "" # get token from logged in browser session cache

MUDAE_ID =   # ID of Mudae bot
CHANNEL_ID =   # ID of claiming channel 934814167179874364
SERVER_ID =   # ID of Discord server
USER_ID =   # ID of main user

client = discord.Client()
main_user: discord.User
dm_channel: discord.DMChannel
roll_channel: discord.TextChannel
mudae: discord.Member
ready = False

async def rollit():
    global client
    count = 0
    while count < 10:
        channel = client.get_channel(CHANNEL_ID)
        time.sleep(2)
        await channel.send("$w")
        count += 1

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    
    global main_user, mudae, dm_channel, roll_channel, timer, timing_info, ready
    logging.info(f'Bot connected as {client.user.name} with ID {client.user.id}')
    main_user = await client.fetch_user(USER_ID)
    dm_channel = await main_user.create_dm()
    roll_channel = await client.fetch_channel(CHANNEL_ID)
    mudae = await client.fetch_user(MUDAE_ID)

    # Parse timers by sending $tu command
    # Only do so once by checking ready property
    if not ready:
        logging.info("Listener is ready")
        ready = True
            
@client.event
async def on_message(message):
    def parse_embed():
        embed = message.embeds[0]

        desc = embed.description
        name = embed.author.name
        series = None
        owner = None
        key = False
            
        # Get series and key value if present
        #match = re.search(r'^(.*?[^<]*)(?:<:(\w+key))?', desc, re.DOTALL)
        match = re.split(r'[\n\r]+', desc)

        kak = re.split(r'[**]+', match[2])

        if len(kak) > 2:
            kak = int(kak[1])
        else:
            kak = 0
            
        if match:
            series = match[0]

        # Check if valid parse
        if not series: return

        # Get owner if present
        if not embed.footer.text:
            is_claimed = False
        else:
            match = re.search(r'(?<=Belongs to )\w+', embed.footer.text, re.DOTALL)
            if match:
                is_claimed = True
                owner = match.group(0)
            else:
                is_claimed = False

        #logging.info(f'Parsed roll: {name} - {series} - Claimed: {is_claimed}')

        return {'name': name,
                'series': series,
                'is_claimed': is_claimed,
                'owner': owner,
                'kak': kak}

    ## BEGIN ON_MESSAGE BELOW ##
    global main_user, mudae, dm_channel, roll_channel, ready
    if not ready: return

    if message.content == '.ggez':
        await rollit()

    # Only parse messages from the bot in the right channel that contain a valid embed
    if message.channel != roll_channel or message.author != mudae or not len(message.embeds) == 1 or \
            message.embeds[0].image.url == message.embeds[0].Empty: return

    if not (waifu_r := parse_embed()): return  # Return if parsing failed

    reaction = None
    def check(reaction, user):
        return user == message.author

    # lets claim anyone with over 150 Kakera
    if waifu_r['kak'] > 150 and not waifu_r['is_claimed']:
        try:
            reaction, user = await client.wait_for('reaction_add', timeout=3.0, check=check)
        except TimeoutError:
            print("No emoji to click, adding emoji")
        else:
            print("**Attempting to snipe**")
            
        if reaction:
            # they set an emoji to click, what is it, click it
            emoji = reaction.emoji
        else:
            # no emoji set, place our own
            emoji = '🦊'
        await message.add_reaction(emoji)


if __name__ == '__main__':
    try:
        client.run(TOKEN_AUTH, bot=False)
    except KeyboardInterrupt:
        logging.critical("Keyboard interrupt, quitting")
        client.loop.run_until_complete(client.logout())
    except discord.LoginFailure or aiohttp.ClientConnectorError:
        logging.critical(f"Improper token has been passed or connection to Discord failed, quitting")
    finally:
        client.loop.stop()
        client.loop.close()
        exit()
