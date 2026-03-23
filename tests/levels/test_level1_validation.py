from pathlib import Path
import yaml
import pytest

from src.validation.runner import validate_level

PUBLIC_FIXTURES = sorted(Path("tests/fixtures/level1").glob("*.yaml"))
PRIVATE_FIXTURES = sorted(Path("tests/fixtures_private/level1").glob("*.yaml"))


def get_teams():
    with open("config/teams.yaml") as f:
        config = yaml.safe_load(f)
    return [team["id"] for team in config["teams"]]


@pytest.mark.parametrize("team", get_teams())
@pytest.mark.parametrize("fixture", PUBLIC_FIXTURES, ids=lambda p: p.stem)
def test_team_level1_public(team, fixture):
    passed, message = validate_level(team, "level1", fixture)
    assert passed, message


@pytest.mark.parametrize("team", get_teams())
@pytest.mark.parametrize("fixture", PRIVATE_FIXTURES, ids=lambda p: p.stem)
def test_team_level1_private(team, fixture):
    passed, message = validate_level(team, "level1", fixture)
    assert passed, message
