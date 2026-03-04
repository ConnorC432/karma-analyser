import asyncio
import logging

import discord
import yt_dlp
from discord.ext import commands

import utils


## TODO playlist playback
## TODO fix url in query option failing to play
class MusicPlayer:
    """
    Music Player class to allow for server independent voice clients/song queues
    """

    def __init__(self, bot: commands.Bot, guild: discord.Guild):
        self.bot = bot
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

        self.guild = guild
        self.queue = asyncio.Queue()
        self.current = None
        self.voice_client = None
        self.play_next_event = asyncio.Event()

        self.ffmpeg_opts = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options'       : '-vn'
        }

        self.loop_task = bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        while True:
            self.current = await self.queue.get()
            try:
                await self.start_next_song()
            except Exception as e:
                self.logger.error(f"ERROR IN PLAYBACK LOOP: {e}")

    async def start_next_song(self):
        ctx = self.current["ctx"]
        info = self.current["info"]

        try:
            await self.join_vc(ctx)

            source = discord.FFmpegPCMAudio(info["url"], **self.ffmpeg_opts)

            self.play_next_event.clear()
            self.voice_client.play(
                source,
                after=lambda e: self.bot.loop.call_soon_threadsafe(self.play_next_event.set),
            )

            ### Create Embed
            duration = info.get("duration", 0)
            minutes, seconds = divmod(duration, 60)
            duration_str = f"{minutes}:{seconds:02d}"

            embed = discord.Embed(
                title=f"NOW PLAYING: {info.get("title", "Unknown Title")}",
                url=info.get("webpage_url", "Unknown URL"),
                description=f"By **{info.get("uploader", "Unknown User")}**",
                colour=utils.REDDIT_RED
            )

            embed.add_field(name="Duration", value=duration_str)
            embed.add_field(name="Views", value=f"{info.get("view_count", 0):,}")

            if info.get("thumbnail"):
                embed.set_thumbnail(url=info["thumbnail"])

            embed.set_footer(text=f"Requested by {ctx.author.display_name}")

            await ctx.send(embed=embed)

            ### Wait for song to end and check VC still populated
            while self.voice_client.is_playing():
                users = [m for m in self.voice_client.channel.members if not m.bot]
                if not users:
                    self.logger.info("NO ONE LEFT IN VC. STOPPING PLAYBACK")
                    self.voice_client.stop()
                    break

                await asyncio.sleep(5)

            await self.play_next_event.wait()
            self.play_next_event.clear()

            if self.queue.empty():
                await self.voice_client.disconnect()
                self.voice_client = None

        except Exception as e:
            await ctx.reply("ERROR PLAYING SONG")
            self.logger.error(f"ERROR PLAYING SONG: {e}")

    async def join_vc(self, ctx):
        channel = ctx.author.voice.channel

        if self.voice_client and self.voice_client.is_connected():
            if self.voice_client.channel != channel:
                await self.voice_client.move_to(channel)

        else:
            self.voice_client = await channel.connect()


class Play(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

        self.players: dict[int, MusicPlayer] = {}

    def get_music_player(self, guild: discord.Guild) -> MusicPlayer:
        """
        return or create a new music player for the given guild
        :param guild:
        :return:
        """
        if guild.id not in self.players:
            self.players[guild.id] = MusicPlayer(self.bot, guild)

        return self.players[guild.id]

    async def search_youtube(self, query: str):
        ytdl_opts = {
            "format"        : "bestaudio/best[ext=m4a]/best",
            "noplaylist"    : True,
            "default_search": "ytsearch5",
            "quiet"         : True,
            "ignoreerrors"  : True,
            "logger"        : self.logger,
            "progress_hooks": [lambda d: self.logger.debug(d)],
        }

        loop = asyncio.get_running_loop()

        def extract():
            with yt_dlp.YoutubeDL(ytdl_opts) as ytdl:
                return ytdl.extract_info(query, download=False)

        try:
            info = await loop.run_in_executor(None, extract)

            if not info:
                self.logger.warning(f"YT search returned no results for query: {query}")
                return None

            # if search results, loop over entries
            if "entries" in info:
                for entry in info["entries"]:
                    if not entry:
                        continue

                    # log for debugging
                    self.logger.info(f"YT entry found: title={entry.get('title')} url={entry.get('webpage_url')}")

                    if entry.get("webpage_url") and entry.get("url"):
                        return entry  # first valid video

                # none valid
                self.logger.warning(f"No valid videos found for query: {query}")
                return None

            # single video case
            if info.get("webpage_url") and info.get("url"):
                self.logger.info(f"YT video found: title={info.get('title')} url={info.get('webpage_url')}")
                return info

            self.logger.warning(f"No valid fields in info: {info}")
            return None

        except Exception as e:
            self.logger.error(f"YouTube search failed for query {query}: {e}")
            return None

    @commands.command(name="play")
    async def play(self, ctx, *, query: str):
        """
        Play a YouTube video in a voice channel
        - `Query` (required): Video search query
        """
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.reply("YOU ARE NOT IN A VOICE CHANNEL")
            return

        if not query:
            await ctx.reply("PLEASE PROVIDE A SEARCH QUERY")
            return

        player = self.get_music_player(ctx.guild)

        info = await self.search_youtube(query)
        if not info:
            await ctx.reply("COULD NOT FIND A RELEVANT VIDEO")
            return

        await player.queue.put(
            {
                "ctx" : ctx,
                "info": info
            }
        )

        await ctx.reply(f"QUEUED: **{info['title']}**")

    @commands.command(name="skip")
    async def skip(self, ctx):
        """
        Skip the currently playing song
        """
        player = self.get_music_player(ctx.guild)

        if not player:
            await ctx.reply("NOTHING EVER HAPPENS")
            return

        if not player.voice_client or not player.voice_client.is_connected():
            await ctx.reply("NOTHING IS PLAYING")
            return

        if not ctx.author.voice or ctx.author.voice.channel != player.voice_client.channel:
            await ctx.reply("YOU MUST BE IN THE SAME VOICE CHANNEL TO SKIP")
            return

        player.voice_client.stop()
        await ctx.reply("SKIPPED")

    @commands.command(name="queue")
    async def queue(self, ctx):
        """
        Show the song queue
        """
        player = self.get_music_player(ctx.guild)

        if not player:
            await ctx.reply("QUEUE IS EMPTY")
            return

        if player.current is None and player.queue.empty():
            await ctx.reply("QUEUE IS EMPTY")

        embed = discord.Embed(
            title="QUEUE",
            color=utils.REDDIT_RED,
        )

        if player.current:
            current_info = player.current["info"]
            embed.add_field(
                name="Now Playing",
                value=f"[{current_info.get('title')}]({current_info.get('webpage_url')})",
                inline=False
            )

        upcoming = list(player.queue._queue)

        if upcoming:
            description = ""
            for index, song in enumerate(upcoming[:10], start=1):
                info = song["info"]
                description += f"**{index}.** [{info.get('title')}]({info.get('webpage_url')})\n"

            if len(upcoming) > 10:
                description += f"\n...and {len(upcoming) - 10} more"

            embed.add_field(
                name="UP NEXT",
                value=description,
                inline=False
            )

        else:
            embed.add_field(
                name="UP NEXT",
                value="NOTHING ELSE IN QUEUE",
                inline=False
            )

        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(Play(bot))
