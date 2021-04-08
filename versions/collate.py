import os
import base64

from datetime import datetime

import requests
import fire
import petl as etl

from frictionless import Package
from dotenv import load_dotenv

load_dotenv()

GITHUB_API = "https://api.github.com"
REPO = "test-and-trace-data/content-collector"


class Collate:
    @staticmethod
    def collate():
        package = Package("data/datapackage.json")

        pages = package.get_resource("content-pages")
        versions = package.get_resource("content-collected")
        collected_versions = set([item["sha"] for item in versions.read_rows()])

        page_ids = [page["id"] for page in pages.read_rows()]

        for page_id in page_ids:
            commit_list = []
            commits_url = f"{GITHUB_API}/repos/{REPO}/commits"
            page = f"collected/{page_id}.html"
            params = {"path": page}
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "Authorization": os.getenv("TOKEN"),
            }
            try:
                resp = requests.get(commits_url, params=params, headers=headers)
                resp.raise_for_status()
                commits = resp.json()
                contents_url = f"{GITHUB_API}/repos/{REPO}/contents/{page}"
                for commit in commits:
                    if commit["sha"] not in collected_versions:
                        commit_list.append(commit["sha"])
                        resp = requests.get(
                            contents_url, params={"ref": commit["sha"]}, headers=headers
                        )
                        resp.raise_for_status()
                        content = resp.json()
                        decoded_bytes = base64.b64decode(content["content"])
                        decoded = str(decoded_bytes, "utf-8")
                        outfile = os.path.join("pages", page, f"{commit['sha']}.html")
                        with open(outfile, "w") as f:
                            f.write(decoded)
                    else:
                        print(f"commit with sha {commit['sha']} already collected")

                pairs = list(map(tuple, zip(commit_list, commit_list[1:])))
                for pair in pairs:
                    print(pair)

                now = datetime.now().isoformat()
                for commit in commit_list:
                    etl.appendcsv(
                        etl.fromdicts(
                            [{"id": page_id, "sha": commit, "entry-date": now}]
                        ),
                        "data/content-collected.csv",
                    )

                if commit_list:
                    package.update(updated=now)
                    package.to_json("data/datapackage.json")

            except Exception as e:
                print(e)


if __name__ == "__main__":
    fire.Fire(Collate)
