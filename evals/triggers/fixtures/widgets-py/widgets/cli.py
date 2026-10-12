import click


@click.group()
def main():
    pass


@main.command()
@click.option("--template", default="basic")
def init(template):
    with open("widgets.toml", "w") as f:
        f.write(f'template = "{template}"\n')
    click.echo(f"created widgets.toml from {template}")
