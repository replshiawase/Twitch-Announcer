# -*- coding: utf-8 -*-

from disnake.ext import commands, tasks
from disnake import Intents, Embed
from random import randint
import requests
import time
import os

from yaml import safe_load, safe_dump

from logging import WARNING, INFO
from utils import get_logger, keep

ds = get_logger('disnake', WARNING)
tw = get_logger('twitch', INFO)

client = requests.Session()

intents = Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', help_command=None, intents=intents)

settings = {
  'tw_client_id': os.environ['tw_client_id'],
  'tw_secret_key': os.environ['tw_secret_key'],
  'tw_channel_name': os.environ['tw_channel_name'],
  'ds_token': os.environ['ds_token'],
  'ds_channel': int(os.environ['ds_channel'])
}

live_status = False

### TWITCH ###


def authorize():

  global twitch_token
  global headers

  token_params = {
    'client_id': settings['tw_client_id'],
    'client_secret': settings['tw_secret_key'],
    'grant_type': 'client_credentials',
  }

  api_token_request = client.post('https://id.twitch.tv/oauth2/token',
                                  params=token_params)
  twitch_token = api_token_request.json()

  if twitch_token.get('access_token'):
    tw.info(f'Token successfully received: {twitch_token["access_token"]}')
  else:
    tw.warning(f'Token not received: {twitch_token}')

  headers = {
    'Authorization': f"Bearer {twitch_token['access_token']}",
    'Client-Id': settings['tw_client_id']
  }


def getStream():
  global headers
  params = {'user_login': settings['tw_channel_name']}

  stream = client.get('https://api.twitch.tv/helix/streams',
                      params=params,
                      headers=headers)

  while stream.status_code != 200:
    if stream.status_code == 401:
      tw.info(
        f'(getStream) Token has expired. Try get new token, wait 10 seconds...'
      )
      authorize()

    else:
      tw.warning(
        f'Stream info not received: {stream.json()}\n\nTry to request, wait 10 seconds...'
      )

    time.sleep(10)
    stream = client.get('https://api.twitch.tv/helix/streams',
                        params=params,
                        headers=headers)

  return stream.json()['data']


def getGame(id):

  params = {'id': id}

  url = 'https://api.twitch.tv/helix/games?&id'

  game = client.get(url, params=params, headers=headers)
  return game.json()['data']


def user_ico():
  global headers
  params = {'login': settings['tw_channel_name']}

  res = client.get('https://api.twitch.tv/helix/users',
                   params=params,
                   headers=headers)

  while res.status_code != 200:
    if res.status_code == 401:
      tw.info(
        f'(user_ico) Token has expired. Try get new token, wait 10 seconds...')
      authorize()

    else:
      tw.warning(
        f'user_ico not received: {res.json()}\n\nTry to request, wait 10 seconds...'
      )

    time.sleep(10)
    res = client.get('https://api.twitch.tv/helix/users',
                     params=params,
                     headers=headers)

  return res.json()['data'][0]['profile_image_url']


### DISCORD ###


def live_status():
  with open('live.yml', encoding='utf-8') as file:
    item = safe_load(file)

  return item['status']


@tasks.loop(minutes=5, reconnect=True)
async def stream_live():

  if 'twitch_token' not in globals(): authorize()
  stream = getStream()

  if stream:
    if not live_status():

      with open('live.yml', 'w', encoding='utf-8') as outfile:
        safe_dump({'status': True}, outfile, allow_unicode=True)

      t = str(int(time.time()))

      tw.info('Stream is live!')

      user_name = stream[0]['user_name']
      game_name = stream[0]['game_name']
      title = stream[0]['title']
      img = stream[0]['thumbnail_url'].replace("{width}", "1280").replace(
        '{height}', '720') + '?rnd=' + t
      game_box_art = getGame(stream[0]['game_id'])[0]['box_art_url'].replace(
        "{width}", "144").replace('{height}', '192') + '?rnd=' + t
      icon = user_ico()

      embed = Embed(
        color=randint(0, 0xFFFFFF),
        title=title,
        url='https://www.twitch.tv/' + settings['tw_channel_name'],
        description=
        f"Начался Стрим Стримыч!\nhttps://www.twitch.tv/{settings['tw_channel_name']}"
      )
      embed.set_thumbnail(url=game_box_art)
      embed.set_author(
        name=user_name,
        icon_url=icon,
        url=f"https://www.twitch.tv/{settings['tw_channel_name']}")
      embed.set_image(url=img)
      embed.add_field('Играет в', game_name)

      channel = bot.get_channel(settings['ds_channel'])
      await channel.send('', embed=embed)

  else:
    if live_status():
      with open('live.yml', 'w', encoding='utf-8') as outfile:
        safe_dump({'status': False}, outfile, allow_unicode=True)

      tw.info('Stream is over!')


@bot.event
async def on_ready():
  ds.info(f'Logined as: {bot.user.name}')
  stream_live.start()


keep()
bot.run(settings['ds_token'])
