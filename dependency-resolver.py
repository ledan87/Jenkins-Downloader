# ruff: noqa: T201
import zipfile

from dependency import Dependency, parse_version

dependencies = [
    Dependency.create("git", "5.0.2"),  # git integration
    Dependency.create("msbuild", "1.30"),
    Dependency.create("mstest", "1.0.0"),
    Dependency.create("http_request", "1.18"),
    Dependency.create("ssh-agent", "333.v878b_53c89511"),
    Dependency.create("ssh-slaves", "2.877.v365f5eb_a_b_eec"),
    Dependency.create("cmakebuilder", "4.1.1"),  # cmake
    Dependency.create("subversion", "2.16.0"),  # svn
    Dependency.create("xunit", "2.3.9"),  # xunit
    Dependency.create("powershell", "1.4"),
    Dependency.create("pipeline-stage-view", "2.33"),
    # from here we have some dependencies that have been present
    Dependency.create("workflow-aggregator", "590.v6a_d052e5a_a_b_5"),
    Dependency.create("jenkins-multijob-plugin", "1.31"),
    Dependency.create("envinject-api", "1.199.v3ce31253ed13"),
    Dependency.create("build-pipeline-plugin", "1.5.8"),
    Dependency.create("antisamy-markup-formatter", "1.1"),
    Dependency.create("throttle-concurrents", "2.6"),
    Dependency.create("sshd", "3.249.v2dc2ea_416e33"),
    Dependency.create("ssh", "2.6.1"),
    Dependency.create("windows-slaves", "1.8.1"),
    Dependency.create("matrix-auth", "2.6.6"),
    Dependency.create("command-launcher", "84.v4a_97f2027398"),
]


# get latest version of each plugin
latest_deps: dict[str, Dependency] = {}
for d in dependencies:
    for dep in [d, *d.all_dependencies]:
        if dep.name not in latest_deps or parse_version(dep.version) > parse_version(
            latest_deps[dep.name].version
        ):
            if dep.name in latest_deps:
                print(  # noqa: T201
                    f"Found new version of {dep.name}: {parse_version(dep.version)} "
                    f"was {parse_version(latest_deps[dep.name].version)}"
                )
            latest_deps[dep.name] = dep

# get highest jenkins version of all latest plugins
highest_jenkins_version = parse_version("0")
for dep in latest_deps.values():
    current_jenkins_version = parse_version(dep.required_jenkins_version)
    if current_jenkins_version > highest_jenkins_version:
        highest_jenkins_version = current_jenkins_version

# print highest jenkins version
print(f"Highest Jenkins Version: {highest_jenkins_version}")


for dep in dependencies:
    print()
    print("Dependencies of " + dep.name)  # noqa:
    dep.print_tree(latest_deps)

# print latest dependencies with version and required jenkins version
for dep in latest_deps.values():
    print(f"{dep.long_name}; {dep.version}")


with zipfile.ZipFile("jenkins-plugins.zip", "w") as zip:
    for hpi in latest_deps.values():
        # write hpi to zip with name from file_name
        zip.write("cache/" + hpi.file_name, arcname=f"{hpi.name}.hpi")
