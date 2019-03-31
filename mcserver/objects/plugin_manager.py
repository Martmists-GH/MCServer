from dataclasses import dataclass
from importlib._bootstrap import module_from_spec
from importlib._bootstrap_external import spec_from_file_location
from os import listdir
from os.path import exists
from typing import List, Optional, Dict, Union, Tuple, Type

from anyio import Event, create_task_group

from mcserver.objects.server_core import ServerCore
from mcserver.utils.misc import map_version


@dataclass
class Dependency:
    dependency_id: str
    dependency_min_version: str
    dependency_max_version: Optional[str] = None


def plugin(plugin_id: str,
           minecraft_version: str,
           plugin_version: str,
           dependencies: List[Dependency] = None):
    dependencies = dependencies or []

    def decorator(cls: Type):
        if plugin_id in PluginManager.plugins:
            raise ValueError(f"Plugin with ID {plugin_id} has already been registered!")
        PluginManager.plugins[plugin_id] = {
            "mc_version": map_version(minecraft_version),
            "plugin_version": map_version(plugin_version),
            "dependencies": dependencies,
            "cls": cls,
            "instance": None,
            "locks": []
        }
        return cls
    return decorator


def mod(mod_id: str,
        minecraft_version: str,
        mod_version: str,
        dependencies: List[Dependency] = None):
    dependencies = dependencies or []

    def decorator(cls: type):
        if mod_id in PluginManager.plugins:
            raise ValueError(f"Mod with ID {mod_id} has already been registered!")
        PluginManager.mods[mod_id] = {
            "mc_version": map_version(minecraft_version),
            "mod_version": map_version(mod_version),
            "dependencies": dependencies,
            "cls": cls,
            "instance": None,
            "locks": []
        }
        return cls
    return decorator


class PluginManager:
    plugins: Dict[str, Dict[str, Union[Tuple, Type, None, List[Union[Event, Dependency]]]]] = {}
    mods: Dict[str, Dict[str, Union[Tuple, Type, None, List[Union[Event, Dependency]]]]] = {}

    @classmethod
    async def search_extensions(cls):
        if exists("mods"):
            for mod in listdir("mods"):
                if exists(f"mods/{mod}/{mod}.py"):
                    spec = spec_from_file_location("extension.module", f"mods/{mod}/{mod}.py")
                    modu = module_from_spec(spec)
                    spec.loader.exec_module(modu)
                    del modu

    @classmethod
    async def prepare(cls):
        with create_task_group() as tg:
            for plugin_id, plugin_obj in cls.plugins.items():
                await tg.spawn(cls.prepare_plugin, plugin_id, plugin_obj)
            for mod_id, mod_obj in cls.mods.items():
                await tg.spawn(cls.prepare_mod, mod_id, mod_obj)

    @classmethod
    async def prepare_plugin(cls, plugin_id: str, plugin_obj: dict):
        lowest_mc_version = min(map(map_version, ServerCore.minecraft_versions))

        if plugin_obj["mc_version"] > lowest_mc_version:
            raise Exception(f"Expected at least minecraft version {plugin_obj['mc_version']}, "
                            f"got {lowest_mc_version}")

        plugin_locks = []

        for dep in plugin_obj["dependencies"]:
            if dep.dependency_id not in cls.plugins:
                raise Exception(f"Missing dependency {dep.dependency_id} "
                                f"for plugin {plugin_id}")

            lock = Event()

            dep_obj = cls.plugins[dep.dependency_id]

            if dep_obj["instance"] is None:
                dep_obj["locks"].append(lock)
                plugin_locks.append(lock)

            dep_version = dep_obj["plugin_version"]

            if map_version(dep.dependecy_min_version) > dep_version:
                raise Exception(f"Dependency {dep.dependency_id} out of date! "
                                f"Expected at least version {dep.dependecy_min_version}, got {dep_version}")

            if dep.dependecy_max_version is not None and map_version(dep.dependecy_max_version) < dep_version:
                raise Exception(f"Dependency {dep.dependency_id} too new! "
                                f"Expected at most version {dep.dependecy_min_version}, got {dep_version}")

        for lock in plugin_locks:
            await lock.wait()

        plugin_obj["instance"] = plugin_obj["cls"]()

        for lock in plugin_obj["locks"]:
            await lock.set()

        cls.plugins[plugin_id] = plugin_obj

    @classmethod
    async def prepare_mod(cls, mod_id: str, mod_obj: dict):
        lowest_mc_version = min(map(map_version, ServerCore.minecraft_versions))

        if mod_obj["mc_version"] > lowest_mc_version:
            raise Exception(f"Expected at least minecraft version {mod_obj['mc_version']}, "
                            f"got {lowest_mc_version}")

        mod_locks = []

        for dep in mod_obj["dependencies"]:
            if dep.dependency_id not in cls.mods:
                raise Exception(f"Missing dependency {dep.dependency_id} "
                                f"for mod {mod_id}")

            lock = Event()

            dep_obj = cls.mods[dep.dependency_id]

            if dep_obj["instance"] is None:
                dep_obj["locks"].append(lock)
                mod_locks.append(lock)

            dep_version = dep_obj["mod_version"]

            if map_version(dep.dependecy_min_version) > dep_version:
                raise Exception(f"Dependency {dep.dependency_id} out of date! "
                                f"Expected at least version {dep.dependecy_min_version}, got {dep_version}")

            if dep.dependecy_max_version is not None and map_version(dep.dependecy_max_version) < dep_version:
                raise Exception(f"Dependency {dep.dependency_id} too new! "
                                f"Expected at most version {dep.dependecy_min_version}, got {dep_version}")

        for lock in mod_locks:
            await lock.wait()

        mod_obj["instance"] = mod_obj["cls"]()

        for lock in mod_obj["locks"]:
            await lock.set()

        cls.mods[mod_id] = mod_obj
