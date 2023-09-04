# ruff: noqa: D101, D102, D103, ANN401

"""Dependency Resolver."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import IO
from urllib.request import urlopen

from packaging import version

MANIFEST_CONTENT_PATTERN = re.compile("(?P<name>.+): (?P<content>.*)")

__cached__: dict[str, Dependency] = {}


class Dependency:
    """Dependency class."""

    def __init__(self: Dependency, name: str, version: str) -> None:
        self.name = name
        self.version = version
        self.manifest = self.__load_manifest()
        self.dependencies: list[Dependency] = self.__load_dependencies()
        self.__visited = False

    @classmethod
    def create(cls: type[Dependency], name: str, version: str) -> Dependency:
        id = f"{name}"
        if id in __cached__:
            dep = __cached__[id]
            if parse_version(version) > parse_version(dep.version):
                print(  # noqa: T201
                    f"Found a new version of {dep.name}: {version} was {dep.version}"
                )
                dep.version = version
            return dep
        else:
            dep = cls(name, version)
            __cached__[id] = dep
            return dep

    @property
    def download_link(self: Dependency) -> str:
        return (
            "https://updates.jenkins.io/download/plugins/"
            f"{self.name}/{self.version}/{self.name}.hpi"
        )

    @property
    def file_name(self: Dependency) -> str:
        return f"{self.name}_{self.version}.hpi"

    @property
    def long_name(self: Dependency) -> str:
        try:
            if "Long-Name" in self.manifest:
                name = self.manifest["Long-Name"]
            else:
                if "Long-Name: JavaScript GUI Lib" in self.manifest:
                    name = f"JavaScript GUI Lib: {self.manifest['Long-Name: JavaScript GUI Lib']}"
                else:
                    name = f"Pipeline: {self.manifest['Long-Name: Pipeline']}"
        except KeyError:
            name = self.name
        if name.startswith("Jenkins "):
            name = name[8:]
        return name

    @property
    def required_jenkins_version(self: Dependency) -> str:
        if "Jenkins-Version" not in self.manifest:
            return "0"
        return self.manifest["Jenkins-Version"]

    @property
    def all_dependencies(self: Dependency) -> list[Dependency]:
        deps = []
        for dep in self.dependencies:
            deps.append(dep)
            deps.extend(dep.all_dependencies)
        return deps

    def __str__(self: Dependency) -> str:
        return f"{self.name}:{self.version}"

    def __load_manifest(self: Dependency) -> dict[str, str]:
        cache_path = Path("cache")
        cache_path.mkdir(parents=True, exist_ok=True)

        file_name = cache_path / self.file_name
        if not file_name.exists():
            url = self.download_link
            print(f'Downloading {self.name} {self.version} from "{url}"')  # noqa: T201
            with urlopen(url) as response, Path(file_name).open("wb") as f:
                f.write(response.read())

        with zipfile.ZipFile(file_name) as zip:
            return self.__parse_manifest(zip.open("META-INF/MANIFEST.MF"))

    def __parse_manifest(self: Dependency, manifest: IO[bytes]) -> dict[str, str]:
        """Parse manifest file.

        Parse the manifest file and provide all entries as dict.
        """
        lines = [
            line
            for line in manifest.read().decode("utf-8").splitlines()
            if line.strip() != ""
        ]

        contents = {}
        line_name = ""

        for line in lines:
            m = MANIFEST_CONTENT_PATTERN.match(line)
            if m is not None:
                line_name = m.group("name")
                contents[line_name] = m.group("content").strip()
            else:
                contents[line_name] = contents[line_name] + line.strip()
        return contents

    def __load_dependencies(self: Dependency) -> list[Dependency]:
        deps = []
        if "Plugin-Dependencies" in self.manifest:
            for dep in self.manifest["Plugin-Dependencies"].split(","):
                if ";" in dep:
                    dep = dep.split(";")[0]
                name, version = dep.split(":")
                deps.append(Dependency.create(name, version))
        return deps

    def print_tree(
        self: Dependency, latest_deps: dict[str, Dependency], level: int = 0
    ) -> None:
        indent = "  " * level
        if self.__visited:
            print(f"{indent}{self.name}:{self.version} (already printed)")
        else:
            print(f"{indent}{self.name}:{self.version}")
            self.__visited = True
            for dependency in self.dependencies:
                dependency.print_tree(latest_deps, level + 1)
        # if level == 0:
        #     for d in __cached__.values():
        #         d.__visited = False  # noqa: SLF001


def get_recursive_dependencies_cached(
    dependencies: list[Dependency], cache: dict[Dependency, str]
) -> list[Dependency]:
    """Get recursive dependencies in a list.

    Cache already resolved dependencies to avoid infinite loops.
    """
    deps = []
    for dep in dependencies:
        if dep in cache:
            continue

        # if dependency in cache has lower version than the one we want to resolve, we
        # need to resolve it again
        if dep in cache and cache[dep] < dep.version:
            del cache[dep]

        cache[dep] = dep.version
        deps.append(dep)
        deps.extend(get_recursive_dependencies_cached(dep.dependencies, cache))
    return deps


def parse_version(version_str: str) -> version.Version:
    """Parse version string to version.Version."""
    try:
        return version.parse(version_str)
    except version.InvalidVersion:
        # version string is not compliant
        # try to remove the last part of the version string
        # e.g. "590.v6a_d052e5a_a_b_5" -> "590"
        # e.g. "1.199.v3ce31253ed13" -> "1.199"
        match = re.search(r"\D", version_str)
        if match:
            return version.parse(version_str[: match.start()])
        else:
            raise
