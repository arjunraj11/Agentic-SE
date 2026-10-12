
import json
import re
import sys
from datetime import datetime
from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.parse import quote

API = "https://pypi.org/pypi/"


def get(url):
    try:
        with urlopen(url, timeout=15) as r:
            return json.load(r)
    except HTTPError as e:
        if e.code == 404:
            return None
        raise


def check(filename):
    packages, versions, releases = 0, 0, []

    with open(filename, encoding="utf-8") as f:
        lines = f.readlines()

    cache = {}

    for line in lines:
        line = line.split("#", 1)[0].strip()
        m = re.match(r"^([\w.-]+)(?:\[[^\]]+\])?\s*==\s*([^\s;]+)", line)
        if not m:
            continue

        name, version = m.groups()
        name_url = quote(name, safe="")
        version_url = quote(version, safe="")

        if name not in cache:
            cache[name] = get(f"{API}{name_url}/json")

        if cache[name] is None:
            packages += 1
            continue

        data = get(f"{API}{name_url}/{version_url}/json")
        if data is None:
            versions += 1
            continue

        urls = data.get("urls", [])
        if urls:
            t = urls[0].get("upload_time_iso_8601") or urls[0].get("upload_time")
            if t:
                releases.append((datetime.fromisoformat(t.replace("Z", "+00:00")), name, version))

    print(f"Dependencies checked: {len(lines)}")
    print(f"Packages not on PyPI: {packages}")
    print(f"Versions not on PyPI: {versions}")

    if releases:
        _, name, version = min(releases)
        year = min(releases)[0].year
        print(f"Oldest pinned release: {name}=={version}({year})")
    else:
        print("Oldest pinned release: None found")


check(sys.argv[1] if len(sys.argv) > 1 else "requirements.txt")
