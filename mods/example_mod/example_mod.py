# TODO: Fix mods/plugins

from quarry.net.protocol import Protocol

from mcserver.plugin_manager import plugin
from mcserver.utils.misc import open_local, read_config


@plugin
class ExampleMod:
    def event_client_settings(self, player: Protocol, buffer):
        with open_local("settings.cfg") as fp:
            config = read_config(fp)
            if config["do_log_client_info"]:
                print(player.display_name, buffer.read())
