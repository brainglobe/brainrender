from brainrender import cli
from click.testing import CliRunner


def test_cli():
    runner = CliRunner()
    runner.invoke(cli.main, ["TH", "-d"])


def test_cli_args():
    runner = CliRunner()
    runner.invoke(cli.main, ["TH", "STR", "c", "-d"])


def test_cli_atlas():
    runner = CliRunner()
    runner.invoke(cli.main, ["TH", "-a", "allen_human_500um", "-d"])
