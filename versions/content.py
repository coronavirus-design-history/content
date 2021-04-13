import os
import base64
import pathlib

from datetime import datetime

import requests
import fire
import petl as etl

from frictionless import Package, transform, steps
from dotenv import load_dotenv

load_dotenv()

GITHUB_API = "https://api.github.com"
REPO = "test-and-trace-data/content-collector"


class Content:
    @staticmethod
    def collate():
        base_dir = pathlib.Path(__file__).absolute().parent.parent
        data_dir = os.path.join(base_dir, "data")
        datapackage = os.path.join(data_dir, "datapackage.json")

        package = Package(datapackage)
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
                        commit_list.append(commit)
                        resp = requests.get(
                            contents_url, params={"ref": commit["sha"]}, headers=headers
                        )
                        resp.raise_for_status()
                        content = resp.json()
                        decoded_bytes = base64.b64decode(content["content"])
                        decoded = str(decoded_bytes, "utf-8")
                        page_dir = os.path.join(base_dir, "pages", page_id)
                        if not os.path.exists(page_dir):
                            os.makedirs(page_dir)
                        outfile = os.path.join(page_dir, f"{commit['sha']}.html")
                        with open(outfile, "w") as f:
                            f.write(decoded)
                    else:
                        print(f"commit with sha {commit['sha']} already collected")

                if commit_list:
                    commit_list.sort(key=lambda x: x["commit"]["committer"]["date"])
                    for commit in commit_list:
                        etl.appendcsv(
                            etl.fromdicts(
                                [
                                    {
                                        "id": page_id,
                                        "sha": commit["sha"],
                                        "parent-sha": commit["parents"][0]["sha"],
                                        "date-recorded": commit["commit"]["committer"][
                                            "date"
                                        ],
                                    }
                                ]
                            ),
                            "data/content-collected.csv",
                        )
                    transform(
                        package,
                        steps=[
                            steps.resource_update(
                                name="content-collected",
                                path="data/content-collected.csv",
                            ),
                        ],
                    )
                    package.update(updated=datetime.now().isoformat())

                package.to_json(datapackage)

            except Exception as e:
                print(e)


if __name__ == "__main__":
    fire.Fire(Content)
