# TODO: Fix mods/plugins
from mcserver.objects.plugin_manager import mod, Dependency


@mod("example.dependent", "1.12.2", "0.0.1", [Dependency("example.mod", "0.0.0")])
class ExampleDependent:
    def __init__(self):
        print("This will run second")


@mod("example.mod", "1.12.2", "0.0.1")
class ExampleMod:
    def __init__(self):
        print("This will run first")
