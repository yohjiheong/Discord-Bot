import discord
import asyncio
from discord.ext import commands, tasks
from discord.voice_client import VoiceClient
import youtube_dl

from random import choice

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

def is_connected(ctx):
    voice_client = ctx.message.guild.voice_client
    return voice_client and voice_client.is_connected()

client = commands.Bot(command_prefix='/')

status = ['Jamming out to music!', 'Eating!','Sleeping!']
queue = []
loop = False

@client.event
async def on_ready():
    change_status.start()
    print('Bot is Here!')

@client.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.channels, name='general')
    await channel.send(f'Welcome {member.mention}!  Ready to jam out? See `?help` command for details!')

# change status every 20 secs
@tasks.loop(seconds=20)
async def change_status():
    await client.change_presence(activity=discord.Game(choice(status)))

@client.command(name='hello', help='This command returns a random welcome message')
async def hello(ctx):
    responses = ['(***grumbles***) Why did you wake me up!?','Top of the morning to you!']
    await ctx.send(choice(responses))

@client.command(name='bye', help='This command returns a random goodbye message')
async def bye(ctx):
    responses = ['Why would you want me to leave?',"I'm happy to say goodbye, haahahah!"]
    await ctx.send(choice(responses))

@client.command(name='credit', help='This command returns credit')
async def credit(ctx):
    await ctx.send('**Duh???**(the chef from liyue ofc!)')


@client.command(name='join', help='This command makes the bot join the voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("You are not connected to a voice channel")
        return

    else:
        channel = ctx.message.author.voice.channel

    await channel.connect()


@client.command(name='leave', help='This command stops the music and makes the bot leave the voice channel')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    await voice_client.disconnect()


@client.command(name='loop', help='This command toggles loop mode')
async def loop_(ctx):
    global loop

    if loop:
        await ctx.send('Loop mode is now `False!`')
        loop = False

    else:
        await ctx.send('Loop mode is now `True!`')
        loop = True


@client.command(name='play', help='This command plays music')
async def play(ctx):
    global queue

    if not ctx.message.author.voice:
        await ctx.send("You are not connected to a voice channel")
        return

    else:
        channel = ctx.message.author.voice.channel

    try:
        await channel.connect()
    except:
        pass

    server = ctx.message.guild
    voice_channel = server.voice_client

    try:
        async with ctx.typing():
            player = await YTDLSource.from_url(queue[0], loop=client.loop)
            voice_channel.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

            if loop:
                queue.append(queue[0])

            del (queue[0])

        await ctx.send('**Now playing:** {}'.format(player.title))

    except:
        await ctx.send('Nothing in your queue! Use `?queue` to add a song!')


@client.command(name='p', help='This command pauses the song')
async def pause():
    voice_channel = server.voice_client

    voice_channel.pause()


@client.command(name='r', help='This command resumes the song!')
async def resume():
    voice_channel = server.voice_client

    voice_channel.resume()


@client.command(name='stop', help='This command stops the song!')
async def stop(ctx):
    server = ctx.message.guild
    voice_channel = server.voice_client

    voice_channel.stop()


@client.command(name='q', help='This command queues the song!')
async def queue_(ctx, url):
    global queue

    queue.append(url)
    await ctx.send(f'`{url}` added to queue!')


@client.command(name='del', help='This command remove the song from queue!')
async def remove(ctx, number):
    global queue

    try:
        del (queue[int(number)])
        await ctx.send(f'Your queue is now `{queue}!`')

    except:
        await ctx.send('Your queue is either **empty** or the index is **out of range**')


@client.command(name='view', help='This command shows the queue')
async def view(ctx):
    await ctx.send(f'Your queue is now `{queue}!`')

client.run('ODQ3Mzg4MzE0OTI3MTA0MDIw.YK9V3Q.L8oYkIjrWGxEqZk48UNqV6yZdO4')