from click.testing import CliRunner
from phonehome.cli import main


def test_help_lists_commands():
    result = CliRunner().invoke(main, ["--help"])
    assert result.exit_code == 0
    for name in ("capture", "analyze", "report", "render"):
        assert name in result.output
