import zipfile
from io import BytesIO
from urllib.request import urlopen
from dependency import Dependency, getRecursiveDependencies

dependencies = []
dependencies.append(Dependency("git", "4.11.5", "2.289.1"))
dependencies.append(Dependency("msbuild", "1.30", "2.289.1"))
dependencies.append(Dependency("workflow-aggregator", "590.v6a_d052e5a_a_b_5", "2.303.3"))

all_deps = getRecursiveDependencies(dependencies)

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