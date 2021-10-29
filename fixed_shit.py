# FIX DISCORD_SLASH
from discord import HTTPException, Forbidden, Client
from discord.ext.commands import Bot, AutoShardedBot, Cog
from re import findall
from discord_slash import SlashCommand as OldSlashCommand
from discord_slash import model, error, http
from contextlib import suppress
import typing
import logging

# subclasses to fix shit
class OptionData2( model.OptionData ):
    def __init__(self, name, description, required=False, choices=None, options=None, **kwargs):
        self.name = name
        self.description = description
        self.type = kwargs.get("type")
        if self.type is None:
            raise error.IncorrectCommandData("type is required for options")
        self.required = required
        self.choices = []
        if choices is not None:
            for choice in choices:
                self.choices.append(model.ChoiceData(**choice))

        if self.type in (1, 2):
            self.options = []
            if options is not None:
                for option in options:
                    self.options.append(OptionData2(**option))
            elif self.type == 2:
                raise error.IncorrectCommandData(
                    "Options are required for subcommands / subcommand groups"
                )
                
    def __eq__(self, other):
        return isinstance(other, OptionData2) and self.__dict__ == other.__dict__

class CommandData2( model.CommandData ):
    def __init__(
        self,
        name,
        description='',
        options=None,
        default_permission=True,
        id=None,
        application_id=None,
        version=None,
        **kwargs,
    ):
        self.name = name
        self.description = description or ''
        self.default_permission = True if default_permission == None else default_permission
        self.id = id
        self.application_id = application_id
        self.version = version
        self.options = []
        if options is not None:
            for option in options:
                self.options.append(OptionData2(**option))
                
    def __eq__(self, other):
        if isinstance(other, CommandData2):
            return (
                self.name == other.name
                and self.description == other.description
                and self.options == other.options
                and self.default_permission == other.default_permission
            )
        else:
            return False

# sub class to change sync_all_commands to just sync global commands to all guilds and to add ext_commands
class SlashCommand( OldSlashCommand ):
    def __init__(
        self,
        client: typing.Union[Client, Bot],
        sync_commands: bool = False,
        debug_guild: typing.Optional[int] = None,
        delete_from_unused_guilds: bool = False,
        sync_on_cog_reload: bool = False,
        override_type: bool = False,
        application_id: typing.Optional[int] = None,
        ext_commands: typing.Optional[list] = []
    ):
        self._discord = client
        self.commands = {"context": {}}
        self.subcommands = {}
        self.components = {}
        self.logger = logging.getLogger("discord_slash")
        self.req = http.SlashCommandRequest(self.logger, self._discord, application_id)
        self.sync_commands = sync_commands
        self.debug_guild = debug_guild
        self.sync_on_cog_reload = sync_on_cog_reload
        self.ext_commands = ext_commands

        if self.sync_commands:
            self._discord.loop.create_task(self.sync_all_commands(delete_from_unused_guilds))

        if (
            not isinstance(client, Bot)
            and not isinstance(client, AutoShardedBot)
            and not override_type
        ):
            self.logger.warning(
                "Detected discord.Client! It is highly recommended to use `commands.Bot`. Do not add any `on_socket_response` event."
            )

            self._discord.on_socket_response = self.on_socket_response
            self.has_listener = False
        else:
            if not hasattr(self._discord, "slash"):
                self._discord.slash = self
            else:
                raise error.DuplicateSlashClient("You can't have duplicate SlashCommand instances!")

            self._discord.add_listener(self.on_socket_response)
            self.has_listener = True
            default_add_function = self._discord.add_cog

            def override_add_cog(cog: Cog):
                default_add_function(cog)
                self.get_cog_commands(cog)

            self._discord.add_cog = override_add_cog
            default_remove_function = self._discord.remove_cog

            def override_remove_cog(name: str):
                cog = self._discord.get_cog(name)
                if cog is None:
                    return
                self.remove_cog_commands(cog)
                default_remove_function(name)

            self._discord.remove_cog = override_remove_cog

            if self.sync_on_cog_reload:
                orig_reload = self._discord.reload_extension

                def override_reload_extension(*args):
                    orig_reload(*args)
                    self._discord.loop.create_task(
                        self.sync_all_commands(delete_from_unused_guilds)
                    )

                self._discord.reload_extension = override_reload_extension

    async def sync_all_commands(
        self, delete_from_unused_guilds=False, delete_perms_from_unused_guilds=False
    ):
        """
        Matches commands registered on Discord to commands registered here.
        Deletes any commands on Discord but not here, and registers any not on Discord.
        This is done with a `put` request.
        A PUT request will only be made if there are changes detected.
        If ``sync_commands`` is ``True``, then this will be automatically called.
        :param delete_from_unused_guilds: If the bot should make a request to set no commands for guilds that haven't got any commands registered in :class:``SlashCommand``
        :param delete_perms_from_unused_guilds: If the bot should make a request to clear permissions for guilds that haven't got any permissions registered in :class:``SlashCommand``
        """
        permissions_map = {}
        cmds = await self.to_dict()
        self.logger.info("Syncing commands...")
        # if debug_guild is set, global commands get re-routed to the guild to update quickly
        cmds["global"] += self.ext_commands
        cmds_formatted = {self.debug_guild: cmds["global"]}
        #for guild in cmds["guild"]:
            #cmds_formatted[guild] = cmds["guild"][guild]
        
        #for scope in cmds_formatted:
        for bth in self._discord.guilds:
            scope = bth.id
            permissions = {}
            new_cmds = cmds_formatted[None]
            existing_cmds = await self.req.get_all_commands(guild_id=scope)
            existing_by_name = {}
            to_send = []
            changed = False
            for cmd in existing_cmds:
                #existing_by_name[cmd["name"]] = model.CommandData(**cmd)
                existing_by_name[cmd["name"]] = CommandData2(**cmd)

            if len(new_cmds) != len(existing_cmds):
                changed = True
                print("1 changed")
            
            for command in new_cmds:
                cmd_name = command["name"]
                permissions[cmd_name] = command.get("permissions")
                if cmd_name in existing_by_name:
                    #cmd_data = model.CommandData(**command)
                    cmd_data = CommandData2(**command)
                    existing_cmd = existing_by_name[cmd_name]
                        
                    if cmd_data != existing_cmd:
                        changed = True
                        print("2 changed")
                        #print(vars(cmd_data),vars(existing_cmd))
                        print(cmd_data.__dict__)
                        print(existing_cmd.__dict__)
                        print()
                        #print(cmd_data.options.__dict__,existing_cmd.options.__dict__)
                        to_send.append(command)
                    else:
                        command_with_id = command.copy()
                        command_with_id["id"] = existing_cmd.id
                        to_send.append(command_with_id)
                else:
                    changed = True
                    print("3 changed")
                    to_send.append(command)

            if changed:
                self.logger.debug(
                    f"Detected changes on {scope if scope is not None else 'global'}, updating them"
                )
                try:
                    #print("sync: ", scope, to_send)
                    print("sync: ", scope)
                    existing_cmds = await self.req.put_slash_commands(
                        slash_commands=to_send, guild_id=scope
                    )
                except HTTPException as ex:
                    if ex.status == 400:
                        # catch bad requests
                        cmd_nums = set(
                            findall(r"^[\w-]{1,32}$", ex.args[0])
                        )  # find all discords references to commands
                        error_string = ex.args[0]

                        for num in cmd_nums:
                            error_command = to_send[int(num)]
                            error_string = error_string.replace(
                                f"In {num}",
                                f"'{error_command.get('name')}'",
                            )

                        ex.args = (error_string,)

                    raise ex
            else:
                self.logger.debug(
                    f"Detected no changes on {scope if scope is not None else 'global'}, skipping"
                )

            id_name_map = {}
            for cmd in existing_cmds:
                id_name_map[cmd["name"]] = cmd["id"]

            for cmd_name in permissions:
                cmd_permissions = permissions[cmd_name]
                cmd_id = id_name_map[cmd_name]
                for applicable_guild in cmd_permissions:
                    if applicable_guild not in permissions_map:
                        permissions_map[applicable_guild] = []
                    permission = {
                        "id": cmd_id,
                        "guild_id": applicable_guild,
                        "permissions": cmd_permissions[applicable_guild],
                    }
                    permissions_map[applicable_guild].append(permission)

        self.logger.info("Syncing permissions...")
        self.logger.debug(f"Commands permission data are {permissions_map}")
        for scope in permissions_map:
            existing_perms = await self.req.get_all_guild_commands_permissions(scope)
            new_perms = permissions_map[scope]

            changed = False
            if len(existing_perms) != len(new_perms):
                changed = True
            else:
                existing_perms_model = {}
                for existing_perm in existing_perms:
                    existing_perms_model[existing_perm["id"]] = model.GuildPermissionsData(
                        **existing_perm
                    )
                for new_perm in new_perms:
                    if new_perm["id"] not in existing_perms_model:
                        changed = True
                        break
                    if existing_perms_model[new_perm["id"]] != model.GuildPermissionsData(
                        **new_perm
                    ):
                        changed = True
                        break

            if changed:
                self.logger.debug(f"Detected permissions changes on {scope}, updating them")
                await self.req.update_guild_commands_permissions(scope, new_perms)
            else:
                self.logger.debug(f"Detected no permissions changes on {scope}, skipping")

        if delete_from_unused_guilds:
            self.logger.info("Deleting unused guild commands...")
            other_guilds = [
                guild.id for guild in self._discord.guilds if guild.id not in cmds["guild"]
            ]
            # This is an extremly bad way to do this, because slash cmds can be in guilds the bot isn't in
            # But it's the only way until discord makes an endpoint to request all the guild with cmds registered.

            for guild in other_guilds:
                with suppress(Forbidden):
                    existing = await self.req.get_all_commands(guild_id=guild)
                    if len(existing) != 0:
                        self.logger.debug(f"Deleting commands from {guild}")
                        await self.req.put_slash_commands(slash_commands=[], guild_id=guild)

        if delete_perms_from_unused_guilds:
            self.logger.info("Deleting unused guild permissions...")
            other_guilds = [
                guild.id for guild in self._discord.guilds if guild.id not in permissions_map.keys()
            ]
            for guild in other_guilds:
                with suppress(Forbidden):
                    self.logger.debug(f"Deleting permissions from {guild}")
                    existing_perms = await self.req.get_all_guild_commands_permissions(guild)
                    if len(existing_perms) != 0:
                        await self.req.update_guild_commands_permissions(guild, [])

        self.logger.info("Completed syncing all commands!")
        

# FIX PYTUBE

from pytube import Stream as OldStream
from pytube import YouTube as OldYouTube
from pytube import request
from pytube.extract import apply_descrambler
from pytube.extract import apply_signature
from urllib.error import HTTPError, URLError
from pytube.exceptions import RegexMatchError, MaxRetriesExceeded, PytubeError
from async_property import async_property

# overwrite .download to debug stuff
class Stream( OldStream ):
    async def download(
        self,
        output_path: typing.Optional[str] = None,
        filename: typing.Optional[str] = None,
        filename_prefix: typing.Optional[str] = None,
        skip_existing: bool = True,
        timeout: typing.Optional[int] = None,
        max_retries: typing.Optional[int] = 0
    ) -> str:
        
        file_path = self.get_file_path(
            filename=filename,
            output_path=output_path,
            filename_prefix=filename_prefix,
        )

        if skip_existing and await self.exists_at_path(file_path):
            #logger.debug(f'file {file_path} already exists, skipping')
            print(f'Stream.download: file {file_path} already exists, skipping')
            self.on_complete(file_path)
            return file_path

        bytes_remaining = (await self.filesize)
        #logger.debug(f'downloading ({(await self.filesize)} total bytes) file to {file_path}')
        print(f'Stream.download: downloading ({bytes_remaining} total bytes) file to {file_path}')

        with open(file_path, "wb") as fh:
            try:
                async for chunk in request_stream(
                    self.url,
                    self._session,
                    timeout=timeout,
                    max_retries=max_retries
                ):
                    # reduce the (bytes) remainder by the length of the chunk.
                    bytes_remaining -= len(chunk)
                    # send to the on_progress callback.
                    self.on_progress(chunk, fh, bytes_remaining)
            except HTTPError as e:
                if e.code != 404:
                    raise
                # Some adaptive streams need to be requested with sequence numbers
                async for chunk in request.seq_stream(
                    self.url,
                    self._session,
                    timeout=timeout,
                    max_retries=max_retries
                ):
                    # reduce the (bytes) remainder by the length of the chunk.
                    bytes_remaining -= len(chunk)
                    # send to the on_progress callback.
                    self.on_progress(chunk, fh, bytes_remaining)
        self.on_complete(file_path)
        return file_path

default_range_size = 9437184  # 9MB
default_chunk_size = 4096  # 4kb

# try to find that console spam bug
async def request_stream(
    url,
    session,
    timeout=900,
    max_retries=0
):
    file_size: int = default_range_size  # fake filesize to start
    downloaded = 0
    while downloaded < file_size:
        stop_pos = min(downloaded + default_range_size, file_size) - 1
        range_header = f"bytes={downloaded}-{stop_pos}"
        tries = 0

        # Attempt to make the request multiple times as necessary.
        while True:
            # If the max retries is exceeded, raise an exception
            if tries >= 1 + max_retries:
                raise MaxRetriesExceeded()

            # Try to execute the request, ignoring socket timeouts
            try:
                response = await request._execute_request(
                    url,
                    session,
                    method="GET",
                    headers={"Range": range_header},
                    timeout=timeout
                )
            except Exception as e:
                # We only want to skip over timeout errors, and
                # raise any other URLError exceptions
                if isinstance( e, socket.timeout ):
                    pass
                else:
                    raise
            else:
                # On a successful request, break from loop
                break
            tries += 1

        if file_size == default_range_size:
            try:
                content_range = response.headers["Content-Range"]
                file_size = int(content_range.split("/")[1])
            except (KeyError, IndexError, ValueError) as e:
                #logger.error(e)
                print("request_stream: ", e, response )
                raise e
                return
        while True:
            chunk = await response.content.read(default_chunk_size)
            if not chunk:
                break
            downloaded += len(chunk)
            yield chunk
    return  # pylint: disable=R1711

# use the new Stream
class YouTube( OldYouTube ):
    @async_property
    async def fmt_streams(self):
        await self.check_availability()
        if self._fmt_streams:
            return self._fmt_streams

        self._fmt_streams = []
        # https://github.com/pytube/pytube/issues/165
        stream_maps = ["url_encoded_fmt_stream_map"]
        if "adaptive_fmts" in (await self.player_config_args):
            stream_maps.append("adaptive_fmts")

        # unscramble the progressive and adaptive stream manifests.
        for fmt in stream_maps:
            if not (await self.age_restricted) and fmt in (await self.vid_info):
                apply_descrambler((await self.vid_info), fmt)
            apply_descrambler((await self.player_config_args), fmt)

            apply_signature((await self.player_config_args), fmt, (await self.js))

            # build instances of :class:`Stream <Stream>`
            # Initialize stream objects
            stream_manifest = (await self.player_config_args)[fmt]
            for stream in stream_manifest:
                video = Stream(
                    stream=stream,
                    player_config_args=(await self.player_config_args),
                    monostate=self.stream_monostate,
                    session=self._client_session,
                )
                self._fmt_streams.append(video)

        self.stream_monostate.title = await self.title
        self.stream_monostate.duration = await self.length

        return self._fmt_streams
    