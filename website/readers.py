import json
import markdown


def read_datapackage(template):
    package = template.environment.globals["datapackage"]
    versions = package.get_resource("content-collected")
    return {
        "json": json.dumps(
            package.to_dict(), sort_keys=True, indent=2, separators=(",", ": ")
        ),
        "versions": versions,
    }


def read_markdown(template):
    markdown_formatter = markdown.Markdown(output_format="html5")
    with open(template.filename) as markdownfile:
        markdown_content = markdownfile.read()
        return {"html": markdown_formatter.convert(markdown_content)}


def read_csv(template):
    package = template.globals["datapackage"]
    resource_name = template.name.split("/")[-1].replace(".csv", "")
    resource = package.get_resource(resource_name)
    related_resource_key = resource.schema.foreign_keys[0]["reference"]["resource"]
    pages = package.get_resource(related_resource_key)
    return {"filename": template.name, "resource": resource, "pages": pages}
