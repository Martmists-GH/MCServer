import logging
from configparser import ConfigParser

from quarry.data import packets
from quarry.net.server import ServerFactory

from mcserver.plugin_manager import PluginManager
from mcserver.utils import DEFAULT_SERVER_PROPERTIES, read_config


class MCServerFactory(ServerFactory):
    def __init__(self):
        super().__init__()
        self.log_level = logging.INFO
        self.buff_type = self.get_buff_type(packets.default_protocol_version)

    def start(self):
        settings = DEFAULT_SERVER_PROPERTIES
        with open("server.properties") as fp:
            override = read_config(fp)
        settings.update(override)
        PluginManager.load_mods()
        self.listen("0.0.0.0", int(settings['server-port']))

    def listen(self, host, port=25565):
        from mcserver.server_protocol import MCServerProtocol
        self.protocol = MCServerProtocol
        super().listen(host, port)


MCServer = MCServerFactory()
