import numpy as np
import jsonpickle
import jsonpickle.ext.numpy as jsonpickle_numpy
from gamemodels.Tiles import Tile, Token
from gamemodels import BoardPieces

jsonpickle_numpy.register_handlers()


class Board:
    """Everything that stands on the board, so the tiles, corner-pieces and edge-pieces."""
    def __init__(self):
        self.tiles = {}  # key: tile-coordinate, value: Tile
        self.corner_pieces = {}  # key: corner-coordinate, value: CornerPiece
        self.edge_pieces = {}  # key: edge-coordinate, value: EdgePiece
        self.tokens = []
        self.pips = {}  # Points per corner location. key: corner_location, value: points
        self.harbors = {}   # key: corner_location, value: string sell type
        self.placeable_edge_spots = []  # Only needs to be updated when the tiles change

    @staticmethod
    def hashable_location(location: np.ndarray) -> tuple:
        """Converts a numpy-array location to a hashable form so it can be used in dictionaries and sets."""
        return tuple(location.astype(int))

    def set_tile(self, location: np.ndarray, tile: Tile) -> None:
        tile.set_location(location)
        self.tiles[self.hashable_location(location)] = tile
        if tile.start_token is not None:
            self.add_token_to_tile(tile.start_token, location)
        self.placeable_edge_spots = self.all_placeable_edge_spots()

    def set_corner_piece(self, location: np.ndarray, corner_piece: BoardPieces.CornerPiece) -> None:
        corner_piece.set_location(location)
        self.corner_pieces[self.hashable_location(location)] = corner_piece

    def set_edge_piece(self, location: np.ndarray, edge_piece: BoardPieces.EdgePiece) -> None:
        edge_piece.set_location(location)
        self.edge_pieces[self.hashable_location(location)] = edge_piece

    def get_tile(self, location: np.ndarray) -> Tile:
        if self.hashable_location(location) in self.tiles:
            return self.tiles.get(self.hashable_location(location))

    def get_corner_piece(self, location) -> BoardPieces.CornerPiece:
        if self.hashable_location(location) in self.corner_pieces:
            return self.corner_pieces.get(self.hashable_location(location))

    def get_edge_piece(self, location: np.ndarray) -> BoardPieces.EdgePiece:
        if self.hashable_location(location) in self.edge_pieces:
            return self.edge_pieces.get(self.hashable_location(location))

    def add_token_to_tile(self, number, tile_location) -> None:
        if number not in [token.number for token in self.tokens]:
            self.tokens.append(Token(number))
        for token in self.tokens:
            if token.number == number:
                token.add_tile(tile_location)
                self.get_tile(tile_location).add_token(token)
        self.calculate_pips()

    def get_token(self, number) -> Token:
        for token in self.tokens:
            if token.get_number() == number:
                return token
        return Token(number)

    def set_harbor(self, corner_location: np.ndarray, sell_type: str) -> None:
        self.harbors[self.hashable_location(corner_location)] = sell_type

    def get_harbor(self, corner_location: np.ndarray) -> str:
        return self.harbors.get(self.hashable_location(corner_location))

    def get_settlements_of_player(self, player_id: int) -> dict:
        """Returns a dictionary with all the locations and settlements of a certain player."""
        settlements = {}
        for location, corner in self.corner_pieces.items():
            if corner.get_player_id() == player_id:
                settlements[location] = corner
        return settlements

    def surround_with_water(self) -> None:
        """Makes sure that every land-tile is surrounded by other tiles. By surrounding them all with water."""
        for base_tile in list(self.tiles.values()):
            if base_tile.type != 'water':
                for around_tile_location in base_tile.surrounding_tiles_coordinates():
                    if self.hashable_location(around_tile_location) not in self.tiles:
                        self.set_tile(around_tile_location, Tile('water'))

    def save_layout(self, filename) -> None:
        """Save the layout (tiles and tokens) to a certain file."""
        with open(filename, 'w') as file:
            file.write(jsonpickle.encode((self.tiles, self.tokens), indent=4, keys=True))

    def load_layout(self, filename) -> None:
        """Load a layout (tiles and tokens) from a certain file."""
        with open(filename, 'r') as file:
            self.tiles, self.tokens = jsonpickle.decode(file.read(), keys=True)
        self.calculate_pips()
        self.placeable_edge_spots = self.all_placeable_edge_spots()

    def all_placeable_corner_spots(self) -> list:
        """Returns all the corner-coordinates that are placeable. AKA it lays adjacent to a land tile."""
        corner_spots = set()
        for tile in self.tiles.values():
            if tile.type != 'water':
                for spot in tile.surrounding_corner_coordinates(tile.location):
                    corner_spots.add(tuple(spot))
        return [np.array(spot) for spot in corner_spots]

    def all_placeable_edge_spots(self) -> list:
        """Returns all the edge-coordinates that are placeable. AKA it lays adjacent to a land tile."""
        placeable_edges = []
        placeable_corners = list(map(tuple, self.all_placeable_corner_spots()))
        for corner_location in placeable_corners:
            for surround_edge in BoardPieces.CornerPiece.surrounding_edge_coordinates(corner_location):
                edge = tuple(surround_edge)
                if edge not in placeable_edges:
                    if tuple(BoardPieces.EdgePiece.other_corner_location(edge, corner_location)) \
                            in placeable_corners:
                        placeable_edges.append(edge)
        return placeable_edges

    def valid_edge(self, edge_location) -> bool:
        """This edge-location isn't fully on water."""
        return self.get_edge_piece(edge_location) is None and tuple(edge_location) in self.placeable_edge_spots

    def surrounding_corners_free(self, corner_location) -> bool:
        """A check for looking if there is enough space around the spot."""
        for edge_location in BoardPieces.CornerPiece.surrounding_edge_coordinates(corner_location):
            new_corner_location = BoardPieces.EdgePiece.other_corner_location(edge_location, corner_location)
            if self.get_corner_piece(new_corner_location) is not None:
                return False
        return True

    def calculate_pips(self) -> None:
        """Calculate the probability-points in advance so it doesn't need to be done each time it's requested."""
        for token in self.tokens:
            for tile_location in token.tile_locations:
                for corner_location in Tile.surrounding_corner_coordinates(tile_location):
                    if tuple(corner_location) not in self.pips:
                        self.pips[tuple(corner_location)] = 0
                    self.pips[tuple(corner_location)] += token.probability(token.number)


def example_board() -> Board:
    """Returns a board with the example layout from the Settlers of Catan rule book"""
    board = Board()

    board.set_tile(np.array((0, 0)), Tile('desert'))

    board.set_tile(np.array((0, -1)), Tile('pasture', 4))
    board.set_tile(np.array((1, -1)), Tile('forest', 3))
    board.set_tile(np.array((1, 0)), Tile('fields', 4))
    board.set_tile(np.array((0, 1)), Tile('mountains', 3))
    board.set_tile(np.array((-1, 1)), Tile('forest', 11))
    board.set_tile(np.array((-1, 0)), Tile('hills', 6))

    board.set_tile(np.array((-1, -1)), Tile('pasture', 2))
    board.set_tile(np.array((0, -2)), Tile('forest', 9))
    board.set_tile(np.array((1, -2)), Tile('hills', 10))
    board.set_tile(np.array((2, -2)), Tile('mountains', 8))
    board.set_tile(np.array((2, -1)), Tile('pasture', 5))
    board.set_tile(np.array((2, 0)), Tile('pasture', 11))
    board.set_tile(np.array((1, 1)), Tile('fields', 6))
    board.set_tile(np.array((0, 2)), Tile('hills', 5))
    board.set_tile(np.array((-1, 2)), Tile('forest', 8))
    board.set_tile(np.array((-2, 2)), Tile('fields', 9))
    board.set_tile(np.array((-2, 1)), Tile('fields', 12))
    board.set_tile(np.array((-2, 0)), Tile('mountains', 10))
    board.surround_with_water()
    return board
