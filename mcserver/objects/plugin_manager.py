from dataclasses import dataclass, field
from importlib._bootstrap import module_from_spec
from importlib._bootstrap_external import spec_from_file_location
from os import listdir
from os.path import exists
from typing import List, Optional, Dict, Union, Tuple, Type, Any

from anyio import Event, create_task_group

from mcserver.objects.server_core import ServerCore
from mcserver.utils.misc import map_version


@dataclass
class Dependency:
    dependency_id: str
    dependency_min_version: str
    dependency_max_version: Optional[str] = None


@dataclass
class Extension:
    id: str
    mc_version: tuple
    version: tuple
    cls: type
    dependencies: List[Dependency] = field(default=[])
    _locks: list = field(default=[])
    _instance: object = field(default=None)


def plugin(plugin_id: str,
           minecraft_version: str,
           plugin_version: str,
           dependencies: List[Dependency] = None):
    dependencies = dependencies or []

    def decorator(cls: Type):
        if plugin_id in [e.id for e in PluginManager.plugins]:
            raise ValueError(f"Plugin with ID {plugin_id} has already been registered!")
        PluginManager.plugins.append(Extension(
            plugin_id,
            map_version(minecraft_version),
            map_version(plugin_version),
            cls,
            dependencies,
        ))
        return cls
    return decorator


def mod(mod_id: str,
        minecraft_version: str,
        mod_version: str,
        dependencies: List[Dependency] = None):
    dependencies = dependencies or []

    def decorator(cls: type):
        if mod_id in [e.id for e in PluginManager.mods]:
            raise ValueError(f"Mod with ID {mod_id} has already been registered!")
        PluginManager.mods.append(Extension(
            mod_id,
            map_version(minecraft_version),
            map_version(mod_version),
            cls,
            dependencies,
        ))
        return cls
    return decorator


class PluginManager:
    plugins: List[Extension] = []
    mods: List[Extension] = []

    @classmethod
    def get_plugin(cls, plugin_id: str) -> Any:
        return [pl for pl in cls.plugins if pl.id == plugin_id][0]._instance

    @classmethod
    def get_mod(cls, mod_id: str) -> Any:
        return [md for md in cls.mods if md.id == mod_id][0]._instance

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
            for plugin_id, plugin_obj in cls.plugins:
                await tg.spawn(cls.prepare_plugin, plugin_id, plugin_obj)
            for mod_id, mod_obj in cls.mods:
                await tg.spawn(cls.prepare_mod, mod_id, mod_obj)

    @classmethod
    async def prepare_plugin(cls, plugin_obj: Extension):
        lowest_mc_version = min(map(map_version, ServerCore.minecraft_versions))

        if plugin_obj.mc_version > lowest_mc_version:
            raise Exception(f"Expected at least minecraft version {plugin_obj.mc_version}, "
                            f"got {lowest_mc_version}")

        plugin_locks = []

        for dep in plugin_obj.dependencies:
            if dep.dependency_id not in cls.plugins:
                raise Exception(f"Missing dependency {dep.dependency_id} "
                                f"for plugin {plugin_obj.id}")

            lock = Event()

            dep_obj = cls.get_plugin(dep.dependency_id)

            if dep_obj._instance is None:
                dep_obj._locks.append(lock)
                plugin_locks.append(lock)

            dep_version = dep_obj.version

            if map_version(dep.dependency_min_version) > dep_version:
                raise Exception(f"Dependency {dep.dependency_id} out of date! "
                                f"Expected at least version {dep.dependency_min_version}, got {dep_version}")

            if dep.dependency_max_version is not None and map_version(dep.dependency_max_version) < dep_version:
                raise Exception(f"Dependency {dep.dependency_id} too new! "
                                f"Expected at most version {dep.dependency_min_version}, got {dep_version}")

        for lock in plugin_locks:
            await lock.wait()

        plugin_obj._instance = plugin_obj.cls()

        for lock in plugin_obj._locks:
            await lock.set()

    @classmethod
    async def prepare_mod(cls, mod_obj: Extension):
        lowest_mc_version = min(map(map_version, ServerCore.minecraft_versions))

        if mod_obj.mc_version > lowest_mc_version:
            raise Exception(f"Expected at least minecraft version {mod_obj.mc_version}, "
                            f"got {lowest_mc_version}")

        mod_locks = []

        for dep in mod_obj.dependencies:
            if dep.dependency_id not in cls.mods:
                raise Exception(f"Missing dependency {dep.dependency_id} "
                                f"for mod {mod_obj.id}")

            lock = Event()

            dep_obj = cls.get_mod(dep.dependency_id)

            if dep_obj._instance is None:
                dep_obj._locks.append(lock)
                mod_locks.append(lock)

            dep_version = dep_obj.version

            if map_version(dep.dependency_min_version) > dep_version:
                raise Exception(f"Dependency {dep.dependency_id} out of date! "
                                f"Expected at least version {dep.dependency_min_version}, got {dep_version}")

            if dep.dependency_max_version is not None and map_version(dep.dependency_max_version) < dep_version:
                raise Exception(f"Dependency {dep.dependency_id} too new! "
                                f"Expected at most version {dep.dependency_min_version}, got {dep_version}")

        for lock in mod_locks:
            await lock.wait()

        mod_obj._instance = mod_obj.cls()

        for lock in mod_obj._locks:
            await lock.set()