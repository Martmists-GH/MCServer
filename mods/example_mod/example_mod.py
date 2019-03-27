from quarry.net.protocol import Protocol

from mcserver.plugin_manager import plugin
from rewrite.utils import open_local, read_config


@plugin
class ExampleMod:
    def event_client_settings(self, player: Protocol, buffer):
        with open_local("settings.cfg") as fp:
            config = read_config(fp)
            if config["do_log_client_info"]:
                print(player.display_name, buffer.read())


if __name__ == "__main__":
    ExampleMod().event_client_settings(None, None)
