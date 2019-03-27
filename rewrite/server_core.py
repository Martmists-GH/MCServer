from anyio import create_task_group, create_tcp_server, run
from quarry.net.crypto import make_keypair, export_public_key

from rewrite.utils import DEFAULT_SERVER_PROPERTIES, read_config


class ServerCore:
    auth_timeout = 30
    options = DEFAULT_SERVER_PROPERTIES
    with open("server.properties") as fp:
        override = read_config(fp)
    options.update(override)

    keypair = make_keypair()
    pubkey = export_public_key(keypair)
    minecraft_versions = [
        "1.12.2"
    ]

    @classmethod
    async def start(cls):
        from rewrite.client_connection import ClientConnection
        async with create_task_group() as tg:
            async with await create_tcp_server(cls.options["server-port"], "0.0.0.0") as server:
                async for client in server.accept_connections():
                    # await client.start_tls()
                    conn = ClientConnection(client)
                    await tg.spawn(conn.serve)

    @classmethod
    def run(cls):
        run(cls.start, backend="asyncio")
