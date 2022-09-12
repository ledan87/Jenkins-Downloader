import zipfile
import re
from io import BytesIO
import os.path
from urllib.request import urlopen

MANIFEST_CONTENT_PATTERN = re.compile("(?P<name>.+): (?P<content>.*)")

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

def getManifest(dep):

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

dependency = Dependency("workflow-aggregator", "590.v6a_d052e5a_a_b_5", "2.303.3")

all_deps = getRecursiveDependencies([dependency])

# get latest version of each plugin
latest_deps = {}
for dep in all_deps:
    if dep.name not in latest_deps or dep.version > latest_deps[dep.name].version:
        latest_deps[dep.name] = dep

# get highest jenkins version of all latest plugins
highest_jenkins_version = "0"
for dep in latest_deps.values():
    if dep.requiredJenkinsVersion > highest_jenkins_version:
        highest_jenkins_version = dep.requiredJenkinsVersion

#print highest jenkins version
print(f"Highest Jenkins Version: {highest_jenkins_version}")

#print latest dependencies with version and required jenkins version
for dep in latest_deps.values():
    print(f"{dep.name}:{dep.version} (Jenkins Version: {dep.requiredJenkinsVersion})")

with zipfile.ZipFile("jenkins-plugins.zip", "w") as zip:
    for hpi in latest_deps.values():
        #write hpi to zip with name from file_name
        zip.write(hpi.file_name(), arcname = f"{hpi.name}.hpi")