import os
import pathlib

import yaml
from bs4 import BeautifulSoup, Tag
from frictionless import Package
from lxml.html.diff import htmldiff
from lxml.html.clean import Cleaner
from jinja2 import Environment, PackageLoader

from website.filters import filters


def _parent_exists(path, page, version):
    file_name = f"{version['parent-sha']}.html"
    file_path = os.path.join(path, page, file_name)
    return os.path.exists(file_path)


def generate_difference_files(data_directory="data"):

    env = Environment(loader=PackageLoader("website", "site"))
    for k, v in filters.items():
        env.filters[k] = v

    base_dir = pathlib.Path(__file__).absolute().parent.parent
    page_dir = os.path.join(base_dir, "pages")

    config = yaml.safe_load(open(os.path.join(base_dir, "website", "_config.yaml")))
    # Override of base url from config
    if os.getenv("BASE_URL", False):
        config["base_url"] = os.getenv("BASE_URL")

    package = Package(os.path.join(base_dir, data_directory, "datapackage.json"))
    resource = package.get_resource("content-collected")
    related_resource_key = resource.schema.foreign_keys[0]["reference"]["resource"]

    pages = package.get_resource(related_resource_key)
    for page in pages:
        filtered_versions = [
            version for version in resource.read_rows() if version["id"] == page["id"]
        ]

        has_parent_version = set(
            [
                version["sha"]
                for version in filtered_versions
                if _parent_exists(page_dir, page["id"], version)
            ]
        )
        versions_from_latest = reversed(filtered_versions)
        context = {
            "versions": versions_from_latest,
            "has_parent_version": has_parent_version,
            "page_id": page["id"],
            "config": config,
            "datapackage": package,
        }

        version_index_template = env.get_template("_version_index.html")
        output_path = f"{page_dir}/{page['id']}/index.html"
        version_index_template.stream(**context).dump(output_path)

        for version in filtered_versions:
            generate_diffs(
                env,
                page_dir,
                page["id"],
                version["sha"],
                version["parent-sha"],
                version["date-recorded"],
            )


def generate_diffs(env, page_dir, page_id, current, previous, date_change_recorded):

    diff_dir = os.path.join(page_dir, page_id, "changes")

    diff_html_path = os.path.join(diff_dir, f"{current}.html")

    if not os.path.exists(diff_html_path):
        if not os.path.exists(diff_dir):
            os.makedirs(diff_dir)

        previous_path = os.path.join(page_dir, page_id, f"{previous}.html")
        current_path = os.path.join(page_dir, page_id, f"{current}.html")

        if not os.path.exists(current_path) or not os.path.exists(previous_path):
            return None

        with open(current_path) as f:
            current_content = "".join(f.readlines())

        with open(previous_path) as f:
            previous_content = "".join(f.readlines())

        cleaner = Cleaner(
            page_structure=False,
            meta=False,
            embedded=True,
            links=False,
            style=True,
            processing_instructions=True,
            inline_style=False,
            scripts=True,
            javascript=True,
            comments=True,
            frames=True,
            annoying_tags=False,
            remove_unknown_tags=False,
            safe_attrs_only=False,
            add_nofollow=True,
        )

        current_cleaned = cleaner.clean_html(current_content)
        previous_cleaned = cleaner.clean_html(previous_content)

        diff = htmldiff(previous_cleaned, current_cleaned)
        diff = BeautifulSoup(diff, "html.parser")

        for tag in diff.find_all("ins"):
            tag["style"] = "background-color: #e6ffee; text-decoration: none"

        for tag in diff.find_all("del"):
            tag["style"] = "background-color: #fdb8c0; text-decoration: none"

        for tag in diff.find_all("a"):
            tag["onclick"] = "return false;"

        # diff has no head section so reuse the one from current page
        # for stylesheets
        base_page = BeautifulSoup(current_content, "html.parser")
        base_page.body.decompose()

        base_page.html.append(Tag(name="body"))

        # insert diff meta data into diff page. Hopefully
        # helps show this is not the real page
        diff_metadata_template = env.get_template("_diffmeta.html")
        content = diff_metadata_template.render(
            {
                "page_id": page_id,
                "previous": previous,
                "current": current,
                "date_change_recorded": date_change_recorded,
            }
        )
        html = BeautifulSoup(content, "html.parser")
        base_page.body.append(html)

        base_page.body.append(diff)

        with open(diff_html_path, "w") as out:
            out.write(base_page.prettify())
            print(f"wrote {out.name}")

    else:
        print(f"Diff file {diff_html_path} already exists")
