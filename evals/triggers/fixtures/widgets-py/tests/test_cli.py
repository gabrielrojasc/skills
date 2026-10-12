from click.testing import CliRunner

from widgets.cli import main


def test_init_writes_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(main, ["init", "--template", "web"])
    assert result.exit_code == 0
    assert (tmp_path / "widgets.toml").read_text() == 'template = "web"\n'
