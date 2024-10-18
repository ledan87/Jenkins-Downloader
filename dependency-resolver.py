# ruff: noqa: T201
import zipfile
from collections import defaultdict
from pathlib import Path

from dependency import Dependency, parse_version

max_jenkins_version = parse_version("2.367")

required_packages = [
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
    Dependency.create("cloudbees-bitbucket-branch-source", "803.vd9c5e84c41fa_"),
    Dependency.create("sonar", "2.15"),
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

# load all dependencies
all_deps_of_required_packages: defaultdict[str, list[Dependency]] = defaultdict(list)
for d in required_packages:
    all_deps_of_required_packages[d.name].append(d)
    for dep in d.all_dependencies:
        all_deps_of_required_packages[dep.name].append(dep)


def get_latest_version(list_of_deps: list[Dependency]) -> Dependency:
    latest = list_of_deps[0]
    for dep in list_of_deps:
        if parse_version(dep.version) > parse_version(latest.version):
            latest = dep
    return latest


latest_deps: dict[str, Dependency] = {}
latest_deps = {
    name: get_latest_version(deps)
    for name, deps in all_deps_of_required_packages.items()
}

# get plugins that violate the jenkins version
jenkins_requirement_missed = False
for dep in latest_deps.values():
    if parse_version(dep.required_jenkins_version) > max_jenkins_version:
        jenkins_requirement_missed = True
        print(
            f"{dep.long_name} violates max Jenkins version {dep.required_jenkins_version}"
        )
if jenkins_requirement_missed:
    print(f"Some plugins violate the max Jenkins version {max_jenkins_version}")
    raise SystemExit(1)

for dep in required_packages:
    print()
    print("Dependencies of " + dep.name)
    dep.print_tree(latest_deps)

# print latest dependencies with version and required jenkins version
for dep in latest_deps.values():
    print(f"{dep.long_name}; {dep.version}")

current_size = 0
zip_number = 1
with zipfile.ZipFile(f"jenkins-plugins_{zip_number}.zip", "w") as zip:
    for hpi in sorted(latest_deps.values(), key=lambda x: x.name):
        # write hpi to zip with name from file_name
        file_size = Path("cache/" + hpi.file_name).stat().st_size

        print(f"{hpi.name}.hpi: {file_size} bytes")
        if current_size + file_size > 100 * 1024 * 1024.0:
            zip.close()
            zip_number += 1
            zip = zipfile.ZipFile(f"jenkins-plugins_{zip_number}.zip", "w")
            current_size = 0

        zip.write("cache/" + hpi.file_name, arcname=f"{hpi.name}.hpi")
        current_size += file_size
