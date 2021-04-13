import os
import pathlib
import fire
import sass
import staticjinja
import yaml

from datetime import datetime
from shutil import copytree, rmtree, copy
from frictionless import Package
from pynpm import NPMPackage

from versions.tools import generate_difference_files
from website.filters import filters
from website.readers import read_datapackage, read_markdown, read_csv
from website.renderers import render_datapackage, render_markdown, render_csv


class StaticSite:
    @staticmethod
    def generate(data_directory="data"):
        """Generate pages for a static site"""

        try:
            data, site_dir, temp_dir = StaticSite.gather_resources(data_directory)
            generate_difference_files(site_dir, data_directory)
            web = staticjinja.Site.make_site(
                searchpath=temp_dir,
                outpath=site_dir,
                contexts=[
                    (f"{data_directory}/datapackage.json", read_datapackage),
                    (".*.md", read_markdown),
                    (".*.csv", read_csv),
                ],
                rules=[
                    (f"{data_directory}/datapackage.json", render_datapackage),
                    (".*.md", render_markdown),
                    (".*.csv", render_csv),
                ],
                encoding="utf8",
                followlinks=False,
                extensions=None,
                staticpaths=["example.csv", "screenshots"],
                env_globals=data,
                env_kwargs={"trim_blocks": True, "lstrip_blocks": True},
                mergecontexts=False,
                filters=filters,
            )
            web.render()
        finally:
            if os.path.exists(temp_dir):
                rmtree(temp_dir)

    @staticmethod
    def gather_resources(data_directory):
        base_dir = pathlib.Path(__file__).absolute().parent.parent
        site_dir = os.path.join(base_dir, "_site")
        if os.path.exists(site_dir):
            rmtree(site_dir)
        os.makedirs(site_dir)

        # copy collected page versions
        page_dest_dir = os.path.join(site_dir, "pages")
        page_src_dir = os.path.join(base_dir, "pages")
        copytree(page_src_dir, page_dest_dir, dirs_exist_ok=True)

        # create temp directory for assembling site
        temp_dir = os.path.join(base_dir, "_temp")
        if os.path.exists(temp_dir):
            rmtree(temp_dir)
        current_dir = pathlib.Path(__file__).absolute().parent
        site_source_dir = os.path.join(current_dir, "site")
        copytree(site_source_dir, temp_dir)
        copy(
            os.path.join(current_dir, "package.json"),
            os.path.join(temp_dir, "package.json"),
        )
        # compile any scss (copy assets to _assets, then run compile)
        assets = os.path.join(temp_dir, "assets")
        if os.path.exists(assets):
            # install npm packages
            npm = NPMPackage(assets)
            npm.install()

            # create temporary duplicate of the assets dir
            _assets = os.path.join(temp_dir, "_assets")
            copytree(assets, _assets)
            rmtree(assets)

            # compile assets
            sass.compile(
                dirname=(_assets, assets),
                output_style="compressed",
                include_paths=[temp_dir],
            )

            # tidy up
            rmtree(_assets)
            rmtree(os.path.join(temp_dir, "node_modules"))
            os.remove(os.path.join(temp_dir, "package.json"))
            os.remove(os.path.join(temp_dir, "package-lock.json"))

            copytree(
                os.path.join(base_dir, data_directory), os.path.join(temp_dir, "data")
            )

        # global data to pass to static site generation
        config = yaml.safe_load(open(os.path.join(current_dir, "_config.yaml")))
        package = Package(f"{data_directory}/datapackage.json")
        data = {
            "config": config,
            "generated_at": datetime.now(),
            "datapackage": package,
        }
        # Override of base url from config
        if os.getenv("BASE_URL", False):
            data["config"]["base_url"] = os.getenv("BASE_URL")

        return data, site_dir, temp_dir


if __name__ == "__main__":
    fire.Fire(StaticSite)
