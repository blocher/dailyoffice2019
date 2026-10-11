import requests
import re


def parse_requirements(file_path):
    with open(file_path) as f:
        lines = f.readlines()
    reqs = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"([a-zA-Z0-9_\-\.]+)", line)
        if match:
            reqs.append(match.group(1))
    return reqs


def get_latest_version(pkg):
    url = f"https://pypi.org/pypi/{pkg}/json"
    resp = requests.get(url)
    if resp.status_code == 200:
        return resp.json()["info"]["version"]
    else:
        return "Not found"


def main():
    reqs = parse_requirements("requirements.txt")
    for pkg in reqs:
        latest = get_latest_version(pkg)
        print(f"{pkg}: Latest version = {latest}")


if __name__ == "__main__":
    main()
