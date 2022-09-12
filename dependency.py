import os.path
import re
import zipfile
from urllib.request import urlopen

MANIFEST_CONTENT_PATTERN = re.compile("(?P<name>.+): (?P<content>.*)")

class Dependency:
    def __init__(self, name, version, requiredJenkinsVersion):
        self.name = name
        self.version = version
        self.requiredJenkinsVersion = requiredJenkinsVersion

    def download_link(self):
        print(f"Downloading {self.name} {self.version}")
        return f"https://updates.jenkins.io/download/plugins/{self.name}/{self.version}/{self.name}.hpi"

    def file_name(self):
        return f"cache/{self.name}_{self.version}.hpi"

    def __str__(self):
        return f"{self.name}:{self.version}"

def parse_manifest(manifest):
    lines = [line for line in manifest.read().decode("utf-8").splitlines() if line.strip() != ""]

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


def getManifest(dep):
    if not os.path.exists("cache"):
        os.makedirs("cache")

    file_name = dep.file_name()
    if not os.path.exists(file_name):
        url = dep.download_link()
        with urlopen(url) as response:
            open(file_name, "wb").write(response.read())

    with open(file_name, "rb") as file:
        with zipfile.ZipFile(file_name) as zip:
            return parse_manifest(zip.open("META-INF/MANIFEST.MF"))

def getDependencies(manifest):
    deps = []
    if "Plugin-Dependencies" in manifest:
        for dep in manifest["Plugin-Dependencies"].split(","):
            if ";" in dep:
                dep = dep.split(";")[0]
            name, version = dep.split(":")
            requiredJenkinsVersion = getJenkinsVersion(manifest)
            deps.append(Dependency(name, version, requiredJenkinsVersion))
    return deps

def getJenkinsVersion(manifest):
    return manifest["Jenkins-Version"]

# get recursive dependencies in a list and cache already resolved dependencies to avoid infinite loops
def getRecursiveDependenciesCached(dependencies, cache):
    deps = []
    for dep in dependencies:
        if dep in cache:
            continue
        
        # if dependency in cache has lower version than the one we want to resolve, we need to resolve it again
        if dep in cache and cache[dep] < dep.version:
            del cache[dep]

        cache.append(dep)
        manifest = getManifest(dep)
        deps.append(dep)
        deps.extend(getRecursiveDependenciesCached(getDependencies(manifest), cache))
    return deps

def getRecursiveDependencies(dependencies):
    deps = []
    for dep in dependencies:
        manifest = getManifest(dep)
        deps.append(dep)
        deps.extend(getRecursiveDependencies(getDependencies(manifest)))
    return deps

