# Stdlib
from typing import List

# External Libraries
from anyio import run, create_task_group, create_tcp_server
from quarry.data import packets

# MCServer
from mcserver.utils.cryptography import export_public_key, make_keypair
from mcserver.utils.misc import DEFAULT_SERVER_PROPERTIES, read_config


class ServerCore:
    # TODO:
    # Refactor auth in a different object
    auth_timeout = 30
    options = DEFAULT_SERVER_PROPERTIES
    with open("server.properties") as fp:
        override = read_config(fp)
    options.update(override)

    keypair = make_keypair()
    pubkey = export_public_key(keypair)
    minecraft_versions = [
        "1.7",
        "1.8",
        "1.9",
        "1.10",
        "1.11",
        "1.12",
        "1.13"
    ]

    @classmethod
    def supported_protocols(cls) -> List[int]:
        return [k for k, v in packets.minecraft_versions.items() if any(v.startswith(ver) for ver in cls.minecraft_versions)]

    @classmethod
    async def start(cls):
        from mcserver.classes.client_connection import ClientConnection
        async with create_task_group() as tg:
            async with await create_tcp_server(cls.options["server-port"], "0.0.0.0") as server:
                async for client in server.accept_connections():
                    # await client.start_tls()
                    conn = ClientConnection(client)
                    await tg.spawn(conn.serve)

    @classmethod
    def run(cls):
        try:
            run(cls.start, backend="curio")
        except KeyboardInterrupt:
            pass
