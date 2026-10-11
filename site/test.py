import subprocess
import json


def get_outdated_packages():
    result = subprocess.run(["pip", "list", "--outdated", "--format=json"], capture_output=True, text=True, check=True)
    return {pkg["name"]: pkg for pkg in json.loads(result.stdout)}


def get_dependency_tree():
    result = subprocess.run(["pipdeptree", "--json"], capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def find_constraints(outdated, tree):
    constraints = {}

    for package in tree:
        name = package["package"]["key"]
        if name in outdated:
            parents = [dep["package_name"] for dep in package.get("dependencies", [])]
            constraints[name] = {
                "current_version": outdated[name]["version"],
                "latest_version": outdated[name]["latest_version"],
                "required_by": [],
            }

    # Now determine what requires each outdated package
    for package in tree:
        for dep in package.get("dependencies", []):
            dep_name = dep["key"]
            if dep_name in constraints:
                constraints[dep_name]["required_by"].append(package["package"]["key"])

    return constraints


def print_constraints_report(constraints):
    for name, info in constraints.items():
        print(f"{name} ({info['current_version']} → {info['latest_version']}):")
        if info["required_by"]:
            print("  🔒 Constrained by:", ", ".join(info["required_by"]))
        else:
            print("  ✅ Freely upgradable (no constraints)")
        print()


if __name__ == "__main__":
    outdated = get_outdated_packages()
    tree = get_dependency_tree()
    constraints = find_constraints(outdated, tree)
    print_constraints_report(constraints)
