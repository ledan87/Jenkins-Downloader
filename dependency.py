# ruff: noqa: D101, D102, D103, ANN401

"""Dependency Resolver."""

from __future__ import annotations

import logging
import re
import zipfile
from pathlib import Path
from typing import IO, Any
from urllib.request import urlopen

MANIFEST_CONTENT_PATTERN = re.compile("(?P<name>.+): (?P<content>.*)")


class Dependency:
    """Dependency class."""

    def __init__(
        self: Dependency, name: str, version: str, required_jenkins_version: str
    ) -> None:
        self.name = name
        self.version = version
        self.required_jenkins_version = required_jenkins_version
        self.logger = logging.getLogger(__name__)

    def download_link(self: Dependency) -> str:
        self.logger.info(f"Downloading {self.name} {self.version}")
        return (
            "https://updates.jenkins.io/download/plugins/"
            f"{self.name}/{self.version}/{self.name}.hpi"
        )

    def file_name(self: Dependency) -> str:
        return f"cache/{self.name}_{self.version}.hpi"

    def __str__(self: Dependency) -> str:
        return f"{self.name}:{self.version}"


def parse_manifest(manifest: IO[bytes]) -> Any:
    lines = [
        line
        for line in manifest.read().decode("utf-8").splitlines()
        if line.strip() != ""
    ]

    contents = {}
    lastname = ""

    for line in lines:
        m = MANIFEST_CONTENT_PATTERN.match(line)
        if m is not None:
            lastname = m.group("name")
            contents[lastname] = m.group("content").strip()
        else:
            contents[lastname] = contents[lastname] + line.strip()
    return contents


def get_manifest(dep: Dependency) -> Any:
    cache_path = Path("cache")
    cache_path.mkdir(parents=True, exist_ok=True)

    file_name = dep.file_name()
    if not Path(file_name).exists():
        url = dep.download_link()
        with urlopen(url) as response, Path(file_name).open("wb") as f:
            f.write(response.read())

    with zipfile.ZipFile(file_name) as zip:
        return parse_manifest(zip.open("META-INF/MANIFEST.MF"))


def get_dependencies(manifest: dict[str, str]) -> list[Dependency]:
    deps = []
    if "Plugin-Dependencies" in manifest:
        for dep in manifest["Plugin-Dependencies"].split(","):
            if ";" in dep:
                dep = dep.split(";")[0]
            name, version = dep.split(":")
            required_jenkins_version = get_jenkins_version(manifest)
            deps.append(Dependency(name, version, required_jenkins_version))
    return deps


def get_jenkins_version(manifest: dict[str, str]) -> str:
    return manifest["Jenkins-Version"]


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
        manifest = get_manifest(dep)
        deps.append(dep)
        deps.extend(
            get_recursive_dependencies_cached(get_dependencies(manifest), cache)
        )
    return deps


def get_recursive_dependencies(dependencies: list[Dependency]) -> list[Dependency]:
    deps = []
    for dep in dependencies:
        manifest = get_manifest(dep)
        deps.append(dep)
        deps.extend(get_recursive_dependencies(get_dependencies(manifest)))
    return deps
