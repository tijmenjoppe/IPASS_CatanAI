from collections import Counter
import numpy as np
from gamemodels import BoardPieces


class Player:
    """The game model of a player."""
    def __init__(self, player_id, color):
        self.resources = Counter()  # key: String resource-type, Value: amount
        self.id = player_id
        self.color = color
        self.expandable_corner_locations = set()  # All the corner locations to which can be expanded
        self.expandable_edge_locations = set()  # All the edge locations to which can be expanded
        self.unexpandable_corners = set()
        self.trade_possibilities = []
        self.corner_amount = 0
        self.edge_amount = 0

    def get_color(self) -> (int, int, int):
        return self.color

    def get_id(self) -> int:
        return self.id

    def get_resources(self) -> dict:
        return dict(self.resources)

    def add_resources(self, resources: dict) -> None:
        self.resources.update(resources)

    def remove_resources(self, resources: dict) -> None:
        self.add_resources(negative_dict(resources))

    def has_resources(self, resources) -> bool:
        """Does this player have these resources."""
        copy = Counter(self.resources)
        copy.update(negative_dict(resources))
        return min(copy.values()) >= 0

    def get_expandable_corners(self) -> list:
        """Returns all the corner-locations this player can expand to."""
        return [np.array(corner) for corner in list(self.expandable_corner_locations)]

    def get_expandable_edges(self) -> list:
        """Returns all the edge-locations this player can expand to."""
        return [np.array(edge) for edge in list(self.expandable_edge_locations)]

    def update_expandable_corners(self, location, board, by_player_id) -> None:
        """Update the places this player can expand to, by placing a corner."""
        if by_player_id == self.id:
            # Adds new expandability options
            for edge_location in BoardPieces.CornerPiece.surrounding_edge_coordinates(location):
                if board.valid_edge(edge_location):
                    self.expandable_edge_locations.add(tuple(edge_location.astype(int)))

        # Removes the location and the surrounding corner locations from expandable
        self.expandable_corner_locations.discard(tuple(location))
        for edge_location in BoardPieces.CornerPiece.surrounding_edge_coordinates(location):
            new_corner_location = BoardPieces.EdgePiece.other_corner_location(edge_location, location)
            self.expandable_corner_locations.discard(tuple(new_corner_location))
            self.unexpandable_corners.add(tuple(new_corner_location))

    def update_expandable_edges(self, location, board, by_player_id) -> None:
        """Update the places this player can expand to, by placing a edge."""
        if by_player_id == self.id:
            for corner_location in BoardPieces.EdgePiece.connected_corner_coordinates(location):
                if board.get_corner_piece(corner_location) is None \
                        and tuple(corner_location) not in self.unexpandable_corners:
                    self.expandable_corner_locations.add(tuple(corner_location.astype(int)))
                for edge_location in BoardPieces.CornerPiece.surrounding_edge_coordinates(corner_location):
                    if board.valid_edge(edge_location):
                        self.expandable_edge_locations.add(tuple(edge_location.astype(int)))

        self.expandable_edge_locations.discard(tuple(location))

    def add_trade_possibility(self, trade):
        # TODO
        self.trade_possibilities.append(trade)

    def add_harbor(self, sell_type: str):
        # TODO
        pass


def negative_dict(dictionary: dict) -> dict:
    """Multiplies every value with minus one."""
    negative = {}
    for key, value in dictionary.items():
        negative[key] = -value
    return negative
