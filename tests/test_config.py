from __future__ import annotations

import argparse
from prayer.config import parse_args

def test_parse_args_defaults():
    """Test that default arguments are parsed correctly."""
    ns = parse_args([])
    assert ns.city == "Deggendorf"
    assert ns.country == "Germany"
    assert ns.method == 3
    assert ns.school == 0
    assert ns.log_level == "INFO"
    assert not ns.dry_run
    assert not ns.focus_now

def test_parse_args_custom():
    """Test that custom arguments are parsed correctly."""
    argv = [
        "--city", "Cairo",
        "--country", "Egypt",
        "--method", "5",
        "--school", "1",
        "--log-level", "DEBUG",
        "--dry-run",
            "--focus-now"
        ]
    ns = parse_args(argv)
    assert ns.city == "Cairo"
    assert ns.country == "Egypt"
    assert ns.method == 5
    assert ns.school == 1
    assert ns.log_level == "DEBUG"
    assert ns.dry_run
    assert ns.focus_now
