import numpy as np


class BoardPiece:
    """A interface for all the pieces that stand on the board."""
    def __init__(self, player_id):
        self.player_id = player_id
        self.location = None

    def set_location(self, location) -> None:
        self.location = location

    def get_location(self) -> np.ndarray:
        return self.location

    def get_player_id(self) -> int:
        return self.player_id

    def __repr__(self) -> str:
        return f"{type(self)}, player {self.player_id}, {self.location}"


class CornerPiece(BoardPiece):
    """All the board-pieces that stand on the corner-coordinate-system, AKA the spots in the three-way intersections."""
    def __init__(self, player_id):
        super().__init__(player_id)
    
    @classmethod
    def location_type(cls, corner_location) -> int:
        """
        A corner-coordinate can be on the top of a tile, the bottom of a tile,
        or inside (which should never be the case obviously).
        Outcomes of this function mean:
        0:Top, 1:Bottom or 2:Inside
        """
        return sum(corner_location) % 3
    
    @classmethod
    def surrounding_edge_coordinates(cls, corner_location) -> list:
        """Returns the coordinates of the three edges surrounding this corner location."""
        positive_negative = {0: 1, 1: -1, 2: None}[cls.location_type(corner_location)]
        if positive_negative is not None:
            return [
                np.array((2*corner_location[0], 2*corner_location[1] + positive_negative)),
                np.array((2*corner_location[0] + positive_negative, 2*corner_location[1])),
                np.array((2*corner_location[0] - positive_negative, 2*corner_location[1] - positive_negative)),
            ]

    @classmethod
    def display_coordinate(cls, corner_location) -> np.ndarray:
        """
        Returns the location in the display-coordinate-system.
        The function is just: x-y, x+y
        """
        return np.array((corner_location[0] - corner_location[1], sum(corner_location)), dtype=np.int8)


class EdgePiece(BoardPiece):
    """All the board-pieces that stand on the edge-coordinate-system, AKA the lines between two tiles."""
    def __init__(self, player_id):
        super().__init__(player_id)

    @classmethod
    def connected_corner_coordinates(cls, edge_location) -> list:
        """The corner-locations this edge-location is connected to."""
        corners = []
        for p in (-1, 1):
            corners.append(np.array([
                (edge_location[d] + p*(edge_location[d] % 2 == 1)) / 2
                for d in range(len(edge_location))]))
        return corners

    @classmethod
    def other_corner_location(cls, edge_location, reference_corner_location) -> np.ndarray:
        """
        When you have the edge-location and one corner-location
        the other corner-location can be faster calculated this way.
        The relation is really interesting:
        corner_location_a + corner_location_b = edge_location
        """
        return edge_location - np.array(reference_corner_location)


class Settlement(CornerPiece):
    """The Settlers of Catan Settlement piece."""
    def __init__(self, player_id):
        super().__init__(player_id)

    @staticmethod
    def give_resources(tile_type: str) -> dict:
        """What resources should be given when adjacent to a tile-type"""
        return {
            'hills': {'brick': 1},
            'forest': {'lumber': 1},
            'mountains': {'ore': 1},
            'fields': {'grain': 1},
            'pasture': {'wool': 1},
            'water': {},
            'desert': {},
        }.get(tile_type)

    @staticmethod
    def build_materials() -> dict:
        return {
            'brick': 1,
            'grain': 1,
            'wool': 1,
            'lumber': 1,
        }


class City(CornerPiece):
    """The Settlers of Catan City piece."""
    def __init__(self, player_id):
        super().__init__(player_id)

    @staticmethod
    def give_resources(tile_type: str) -> dict:
        """What resources should be given when adjacent to a tile-type"""
        return {
            'hills': {'brick': 2},
            'forest': {'lumber': 2},
            'mountains': {'ore': 2},
            'fields': {'grain': 2},
            'pasture': {'wool': 2},
            'water': {},
            'desert': {},
        }.get(tile_type)

    @staticmethod
    def build_materials() -> dict:
        return {
            'ore': 3,
            'grain': 2,
        }


class Road(EdgePiece):
    """The Settlers of Catan Road piece."""
    def __init__(self, player_id):
        super().__init__(player_id)

    @staticmethod
    def build_materials() -> dict:
        return {
            'brick': 1,
            'lumber': 1,
        }
