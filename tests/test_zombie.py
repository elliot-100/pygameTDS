"""Tests for `Zombie` class."""

from src.zombies import Zombie


def test_new() -> None:
    """Test that Zombie can be created."""
    # arrange
    # act
    z = Zombie(
        x=0,
        y=0,
    )
    # assert
    assert z
