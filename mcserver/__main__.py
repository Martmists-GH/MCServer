from twisted.internet import reactor

from mcserver.server_factory import MCServer

MCServer.start()
reactor.run()
