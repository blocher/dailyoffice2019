#!/usr/bin/env python3
import argparse, json, re, sys, urllib.request
from packaging.requirements import Requirement
from packaging.version import Version, InvalidVersion

COMMENT_RE = re.compile(r'^\s*#')
EMPTY_RE = re.compile(r'^\s*$')

def latest_stable(name):
    url = f"https://pypi.org/pypi/{name}/json"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.load(resp)
    except Exception as e:
        raise RuntimeError(f"Failed to fetch {name}: {e}")
    # Prefer latest non-prerelease from releases; fall back to info.version
    versions = []
    for v in data.get("releases", {}):
        try:
            ver = Version(v)
            if not ver.is_prerelease and not ver.is_devrelease and not ver.is_postrelease:
                # only consider versions that actually have files
                files = data["releases"].get(v) or []
                if files:
                    versions.append(ver)
        except InvalidVersion:
            continue
    if versions:
        return str(max(versions))
    return data.get("info", {}).get("version")

def transform_line(line):
    if COMMENT_RE.match(line) or EMPTY_RE.match(line):
        return line  # keep comments/blank lines as-is

    # Preserve inline comments by splitting once
    requirement_part, *comment = line.split("#", 1)
    comment_suffix = f"  # {comment[0]}" if comment else ""

    req_str = requirement_part.strip()
    if not req_str:
        return line

    try:
        req = Requirement(req_str)
    except Exception:
        # Not a normal requirement (e.g., -e git+...), keep as-is
        return line

    # Skip URLs, editable installs, or direct references (PEP 508 @ file/url)
    if req.url or any(str(s).startswith("@") for s in req.specifier):
        return line

    latest = latest_stable(req.name)
    if not latest:
        return line

    # Keep extras and markers; replace specifier with >=latest
    extras = f"[{','.join(sorted(req.extras))}]" if req.extras else ""
    marker = f" ; {req.marker}" if req.marker else ""

    return f"{req.name}{extras}>={latest}{marker}{comment_suffix}\n"

def main():
    p = argparse.ArgumentParser(description="Bump requirements to minimum=latest versions.")
    p.add_argument("-i", "--input", default="requirements.txt")
    p.add_argument("-o", "--output", default="requirements.proposed.txt")
    args = p.parse_args()

    out_lines = []
    with open(args.input, "r", encoding="utf-8") as f:
        for line in f:
            try:
                out_lines.append(transform_line(line))
            except Exception as e:
                sys.stderr.write(f"Warning: {e}\n")
                out_lines.append(line)  # fall back to original

    with open(args.output, "w", encoding="utf-8") as f:
        f.writelines(out_lines)

    print(f"Wrote {args.output}")

if __name__ == "__main__":
    main()
