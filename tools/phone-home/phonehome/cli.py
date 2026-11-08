"""Command-line entry point."""
import click
from .capture import capture as do_capture


@click.group()
def main():
    """Capture, analyze, report, and replay phone network activity."""


@main.command()
@click.option('--app', required=True)
@click.option('--target', required=True)
@click.option('--duration', type=click.IntRange(min=1), default=60, show_default=True)
@click.option('--iface', default='tailscale0', show_default=True)
def capture(app, target, duration, iface):
    """Capture traffic from one target phone."""
    try:
        do_capture(app, target, duration, iface)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc


@main.command()
def analyze():
    """Analyze an existing capture."""
    raise click.ClickException("Analysis is not implemented yet.")


@main.command()
def report():
    """Generate a report from an analyzed run."""
    raise click.ClickException("Reporting is not implemented yet.")


@main.command()
def render():
    """Replay an analyzed run in a browser."""
    raise click.ClickException("Rendering is not implemented yet.")
