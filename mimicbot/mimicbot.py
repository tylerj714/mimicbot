# mimicbot.py
import os
import discord
from dotenv import load_dotenv
from discord import app_commands, Member, Guild
from typing import List, Optional, Literal
import mimicbot_dom
from mimicbot_dom import Game, Watcher
from logging_manager import logger
import time

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
VOTE_CHANNEL = int(os.getenv('VOTE_CHANNEL'))
BASE_PATH = os.getenv('BASE_PATH')


class MimicBotClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.synced = False

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync(guild=discord.Object(id=GUILD_ID))
            self.synced = True
        print(f"We have logged in as {self.user}.")


client = MimicBotClient()
tree = app_commands.CommandTree(client)


async def watcher_list_autocomplete(interaction: discord.Interaction,
                                    current: str,
                                    ) -> List[app_commands.Choice[str]]:
    game = await get_game(BASE_PATH)
    watchers = await get_watchers(current, game.watchers)
    return [
        app_commands.Choice(name=watcher.watcher_name,
                            value=str(watcher.watched_channel_id) + '_' + str(watcher.copy_to_channel_id))
        for watcher in watchers
    ]


async def get_watchers(substr: str, watchers: List[Watcher]) -> List[Watcher]:
    watcher_list = []
    for watcher in sorted(watchers, key=lambda e: e.watcher_name.lower()):
        if substr and substr.lower() not in watcher.watcher_name.lower():
            continue
        watcher_list.append(watcher)
    return watcher_list[:25]


@client.event
async def on_ready():
    logger.info(f'{client.user.name} has connected to Discord!')


@client.event
async def on_message(message):
    # Don't copy bot messages to create a loop
    if message.sender.id == client.user.id:
        return

    game = await get_game(BASE_PATH)

    # If the bot is disabled, stop copying
    if not game.is_active:
        return

    message_channel_id = message.channel.id

    for watcher in game.watchers:
        if message_channel_id == watcher.watched_channel_id:
            mimic_message = message.content

            if watcher.with_timestamps:
                mimic_message = "[" + message.created_at + "] " + mimic_message

            if watcher.with_users:
                mimic_message = "[" + message.sender.display_name + "] " + mimic_message

            await message.guild.get_channel(watcher.copy_to_channel_id).send(mimic_message)


@tree.command(name="toggle-activity",
              description="Enables/Disables bot commands for players",
              guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_guild=True)
async def toggle_activity(interaction: discord.Interaction,
                          active: Literal['True', 'False']):
    log_interaction_call(interaction)
    game = await get_game(BASE_PATH)

    game.is_active = True if active == 'True' else False

    await write_game(game, BASE_PATH)
    await interaction.response.send_message(f'Bot active state has been set to {active}!', ephemeral=True)


@tree.command(name="clear-messages",
              description="Clears up to 100 messages out of a discord channel",
              guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_guild=True)
async def clear_messages(interaction: discord.Interaction,
                         channel: discord.TextChannel,
                         channel_again: discord.TextChannel
                         ):
    log_interaction_call(interaction)

    if channel != channel_again:
        await interaction.response.send_message(f"Both channel arguments must be the same! This is a safety feature!")

    await interaction.response.send_message(f"Clearing messages from channel {channel.name}")
    await channel.purge(limit=100)


@tree.command(name="create-mimic",
              description="Creates a mimic that watches a channel and copies all text into another channel",
              guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_guild=True)
async def create_mimic(interaction: discord.Interaction,
                       watchedChannel: discord.TextChannel,
                       copyToChannel: discord.TextChannel,
                       withTimestamp: Optional[Literal['True', 'False']],
                       withUser: Optional[Literal['True', 'False']]
                       ):
    log_interaction_call(interaction)
    if not withTimestamp:
        withTimestamp = False
    if not withUser:
        withUser = False

    game = await get_game(BASE_PATH)

    watcher_name = watchedChannel.name + " => " + copyToChannel.name
    watcher = Watcher(watcher_name=watcher_name, watched_channel_id=watchedChannel.id, copy_to_channel_id=copyToChannel.id,
                      with_timestamps=withTimestamp, with_users=withUser)

    game.add_watcher(watcher)

    await write_game(game, BASE_PATH)
    await interaction.response.send_message(f'Created watcher for {watchedChannel.name} copying to {copyToChannel.name}', ephemeral=True)


@tree.command(name="remove-mimic",
              description="Creates a mimic that watches a channel and copies all text into another channel",
              guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_guild=True)
@app_commands.autocomplete(watcher=watcher_list_autocomplete)
async def delete_mimic(interaction: discord.Interaction,
                       watcher: str):
    log_interaction_call(interaction)

    game = await get_game(BASE_PATH)

    id_parts = watcher.split("_")
    watched_channel_id = id_parts[0]
    copy_to_channel_id = id_parts[1]

    watcher = game.get_watcher(int(watched_channel_id), int(copy_to_channel_id))

    if watcher is not None:
        game.remove_watcher(watcher)
        await write_game(game, BASE_PATH)
        await interaction.response.send_message("Successfully deleted watcher!", ephemeral=True)
    else:
        await interaction.response.send_message("Could not find a matching watcher!", ephemeral=True)


@tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"Cooldown is in force, please wait for {round(error.retry_after)} seconds", ephemeral=True)
    else:
        raise error


async def get_game(path: str) -> Game:
    json_file_path = f'{path}/game.json'
    logger.info(f'Grabbing game info from {json_file_path}')
    return mimicbot_dom.read_json_to_dom(json_file_path)


async def write_game(game: Game, path: str):
    json_file_path = f'{path}/game.json'
    logger.info(f'Wrote game data to {json_file_path}')
    mimicbot_dom.write_dom_to_json(game, json_file_path)


def log_interaction_call(interaction: discord.Interaction):
    logger.info(
        f'Received command {interaction.command.name} with parameters {interaction.data} initiated by user {interaction.user.name}')


client.run(TOKEN)
