import pygame

from Launcher import Zombie


class TestZombie:
    def test_spawn(self):
        """Test that a Zombie of a given class can be spawned."""
        # arrange
        pygame.display.set_mode()  # pre-req for `pygame.image.convert_alpha()`
        # act
        z = Zombie.spawn('c')
        # assert
        assert z.health == Zombie.ZOMBIE_TYPES['c']['MAX_HEALTH']
