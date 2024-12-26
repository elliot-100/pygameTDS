def test_class_imports() -> None:
    """Test that classes can be imported from modules."""
    # arrange
    # act
    from Launcher import Camera, HealthBar, Projectile, Zombie, ZombieClass
    from src.blood_particle import BloodParticle
    from src.chest import Chest
    from src.cursor import Cursor
    from src.energy_orb import EnergyOrb
    from src.floating_text import FloatingText
    from src.muzzle_flash import MuzzleFlash
    from src.weapons import Weapon, WeaponCategory
    # assert
    assert BloodParticle
    assert Camera
    assert Chest
    assert Cursor
    assert EnergyOrb
    assert FloatingText
    assert HealthBar
    assert MuzzleFlash
    assert Projectile
    assert Weapon
    assert WeaponCategory
    assert Zombie
    assert ZombieClass
