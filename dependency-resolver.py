import zipfile

from dependency import Dependency, get_manifest, get_recursive_dependencies

dependencies = [
    Dependency("git", "4.11.5", "2.289.1"),
    Dependency("msbuild", "1.30", "2.289.1"),
    Dependency("workflow-aggregator", "590.v6a_d052e5a_a_b_5", "2.303.3"),
    Dependency("ssh-agent", "333.v878b_53c89511", "2.332.4"),
    Dependency("ssh-slaves", "2.877.v365f5eb_a_b_eec", "2.361.4"),
    Dependency("http_request", "1.18", "2.361.4"),
    Dependency("javadoc", "226.v71211feb_e7e9", "2.361.4"),
]

all_deps = get_recursive_dependencies(dependencies)

# get latest version of each plugin
latest_deps: dict[str, Dependency] = {}
for dep in all_deps:
    if dep.name not in latest_deps or dep.version > latest_deps[dep.name].version:
        latest_deps[dep.name] = dep

# get highest jenkins version of all latest plugins
highest_jenkins_version = "0"
for dep in latest_deps.values():
    if dep.required_jenkins_version > highest_jenkins_version:
        highest_jenkins_version = dep.required_jenkins_version

# print highest jenkins version
print(f"Highest Jenkins Version: {highest_jenkins_version}")  # noqa: T201

# print latest dependencies with version and required jenkins version
for dep in latest_deps.values():
    manifest = get_manifest(dep)
    try:
        if "Long-Name" in manifest:
            print(f"{manifest['Long-Name']}; {dep.version}")  # noqa: T201
        # elif "Implementation-Title" in manifest:
        #     print(f"{manifest['Implementation-Title']}; {dep.version}")  # noqa: T201
        else:
            if "Long-Name: JavaScript GUI Lib" in manifest:
                name = f"JavaScript GUI Lib {manifest['Long-Name: JavaScript GUI Lib']}"
            else:
                name = f"Pipeline: {manifest['Long-Name: Pipeline']}"
            print(f"{name}; {dep.version}")  # noqa: T201
    except KeyError:
        print(f"{dep.name}; {dep.version}")

with zipfile.ZipFile("jenkins-plugins.zip", "w") as zip:
    for hpi in latest_deps.values():
        # write hpi to zip with name from file_name
        zip.write(hpi.file_name(), arcname=f"{hpi.name}.hpi")
