def render_datapackage(env, template, **kwargs):

    # render the html version
    datapackage_template = env.get_template("_datapackage.html")
    output_path = f"{env.outpath}/{template.name.replace('.json','.html')}"
    datapackage_template.stream(**kwargs).dump(output_path)

    # render the original file too
    output_path = f"{env.outpath}/{template.name}"
    template.stream(**kwargs).dump(output_path)


def render_markdown(env, template, **kwargs):
    content_template = env.get_template("_content.html")
    output_path = f"{env.outpath}/{template.name.replace('.md','.html')}"
    content_template.stream(**kwargs).dump(output_path)


def render_csv(env, template, **kwargs):

    # render original file
    output_path = f"{env.outpath}/{template.name}"
    template.stream(**kwargs).dump(output_path)

    # render site index page
    site_index_template = env.get_template("_index.html")
    output_path = f"{env.outpath}/index.html"
    site_index_template.stream(**kwargs).dump(output_path)
