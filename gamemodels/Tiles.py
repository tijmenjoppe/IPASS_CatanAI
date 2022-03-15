import numpy as np
from gameflow import Dice
from gameflow.ActionsAndTurns import Action


class Tile:
    """The hexagonal tile that forms the board and layout."""
    def __init__(self, tile_type, start_token=None):
        self.type = tile_type
        self.location = None
        self.start_token = start_token
        self.tokens = []

    def set_location(self, location: np.ndarray) -> None:
        self.location = location

    def surrounding_tiles_coordinates(self) -> list:
        """Returns the locations of the tiles surrounding this tile. In the tile-coordinate-system."""
        return [self.location+np.array(relative) for relative in ((-1, 0), (0, -1), (1, -1), (1, 0), (0, 1), (-1, 1))]

    @classmethod
    def surrounding_corner_coordinates(cls, tile_location) -> list:
        """Returns the locations of adjacent corner spots. In the corner-coordinate-system."""
        base = np.array((2*tile_location[0]+tile_location[1], 2*tile_location[1]+tile_location[0]))
        return [base+np.array(relative) for relative in ((0, 0), (1, 0), (2, 1), (2, 2), (1, 2), (0, 1))]

    def add_token(self, token) -> None:
        self.tokens.append(token)

    def distribute_resources(self, game_state) -> None:
        """Gives resources to all the players that have settlements adjacent too the tile."""
        for corner_location in self.surrounding_corner_coordinates(self.location):
            corner = game_state.board.get_corner_piece(corner_location)
            if corner is None:
                continue
            owner = game_state.get_player(corner.get_player_id())
            owner.add_resources(corner.give_resources(self.type))


class Token:
    """The number tokens laying on the tiles"""
    def __init__(self, number):
        self.number = number
        self.tile_locations = []

    def get_number(self):
        return self.number

    def add_tile(self, tile_location):
        self.tile_locations.append(tile_location)

    def get_tile_locations(self):
        return self.tile_locations

    @classmethod
    def probability(cls, number):
        """The chance this token will be thrown in one throw."""
        return Dice.dice_weights[Action.dice_throw(number)]

    def __repr__(self):
        return str(self.get_number())
