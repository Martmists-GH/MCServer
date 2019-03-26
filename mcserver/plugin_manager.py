from copy import deepcopy
from importlib._bootstrap import module_from_spec
from importlib._bootstrap_external import spec_from_file_location
from os import listdir
from traceback import print_exc

from quarry.net.protocol import Protocol

from mcserver.utils import read_config


def plugin(cls):
    PluginManager.plugins.append(cls())
    return cls


class PluginManager:
    plugins = []

    @classmethod
    def handle_event(cls, player: Protocol, buff, name):
        for _plugin in cls.plugins:
            new_buff = deepcopy(buff)
            func = getattr(_plugin, f"event_{name}", lambda *_: None)
            func(player, new_buff)

    @classmethod
    def load_mods(cls):
        mod_folders = listdir("mods")
        for mod in mod_folders:
            if "mod.mcmeta" in listdir(f"mods/{mod}"):
                with open(f"mods/{mod}/mod.mcmeta") as fp:
                    data = read_config(fp)
                print(f"Attempting to load {data['mod_name']} ({data['version']})")
                main_file_path = f"mods/{mod}/{data['main_file']}"
                try:
                    spec = spec_from_file_location("mc.server.mod", main_file_path)
                    mod = module_from_spec(spec)
                    spec.loader.exec_module(mod)
                except Exception:  # pylint: disable=broad-except
                    print(f"Failed to load mod {data['mod_name']}:")
                    print_exc()
                else:
                    print("Loaded successfully.")
