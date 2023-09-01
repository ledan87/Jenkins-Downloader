import zipfile

from dependency import Dependency, get_manifest, get_recursive_dependencies

dependencies = [
    Dependency("git", "5.0.2", "2.289.1"),  # git integration
    Dependency("msbuild", "1.30", "2.289.1"),
    Dependency("mstest", "1.0.0", "2.289.1"),
    Dependency("http_request", "1.18", "2.361.4"),
    Dependency("ssh-agent", "333.v878b_53c89511", "2.332.4"),
    Dependency("ssh-slaves", "2.877.v365f5eb_a_b_eec", "2.361.4"),
    Dependency("cmakebuilder", "4.1.1", "2.361.4"),  # cmake
    Dependency("subversion", "2.16.0", "2.361.4"),  # svn
    Dependency("xunit", "2.3.9", "2.289.1"),  # xunit
    Dependency("powershell", "1.4", "2.289.1"),
    Dependency("pipeline-stage-view", "2.33", "2.361.4"),
    # from here we have some dependencies that have been present
    Dependency("workflow-aggregator", "590.v6a_d052e5a_a_b_5", "2.303.3"),
    Dependency("javadoc", "226.v71211feb_e7e9", "2.361.4"),
    Dependency("conditional-buildstep", "1.4.2", "2.361.4"),
    Dependency("jenkins-multijob-plugin", "1.31", "2.289.1"),
    Dependency("envinject-api", "1.199.v3ce31253ed13", "2.332.1"),
    Dependency("build-pipeline-plugin", "1.5.8", "1.619"),
    Dependency("dashboard-view", "2.9.11", "2.289.1"),
    Dependency("antisamy-markup-formatter", "1.1", "2.289.1"),
    Dependency("throttle-concurrents", "2.6", "2.289.1"),
    Dependency("sshd", "3.249.v2dc2ea_416e33", "2.289.1"),
    Dependency("ssh", "2.6.1", "2.289.1"),
    Dependency("windows-slaves", "1.8.1", "2.289.1"),
    Dependency("matrix-auth", "2.6.6", "2.289.1"),
    Dependency("command-launcher", "84.v4a_97f2027398", "2.289.1"),
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
            name = manifest["Long-Name"]
        else:
            if "Long-Name: JavaScript GUI Lib" in manifest:
                name = (
                    f"JavaScript GUI Lib: {manifest['Long-Name: JavaScript GUI Lib']}"
                )
            else:
                name = f"Pipeline: {manifest['Long-Name: Pipeline']}"
    except KeyError:
        name = dep.name
    if name.startswith("Jenkins "):
        name = name[8:]
    print(f"{name}; {dep.version}")  # noqa: T201



with zipfile.ZipFile("jenkins-plugins.zip", "w") as zip:
    for hpi in latest_deps.values():
        # write hpi to zip with name from file_name
        zip.write(hpi.file_name(), arcname=f"{hpi.name}.hpi")
