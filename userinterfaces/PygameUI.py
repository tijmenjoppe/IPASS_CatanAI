import threading
import pygame
import numpy as np
from gamemodels.Tiles import Tile
from gamemodels import BoardPieces
from gamemodels.Players import Player
from gameflow.ActionsAndTurns import Action

tile_colors = {
    'hills': (194, 102, 38),
    'forest': (44, 72, 35),
    'mountains': (153, 137, 146),
    'fields': (244, 181, 39),
    'pasture': (108, 195, 47),
    'desert': (200, 166, 80),
    'water': (23, 155, 221),
}

WHITE = (255, 255, 255)


def distance_points(point1: np.ndarray, point2: np.ndarray) -> float:
    """Returns the distance between two points."""
    return np.linalg.norm(point1 - point2)


def closest_point_cursor(display_points: list, mouse_pos):
    """Returns the index of the point that is closest to the mouse position."""
    display_points = list(map(tuple, display_points))
    return display_points.index(min(display_points, key=lambda p: distance_points(p, np.array(mouse_pos))))


def mix_colors(color1, color2, mix: float):
    """Uses the value of 'mix' that is between 0.0 and 1.0 to mix the two colors."""
    return np.array(color1) * (1 - mix) + np.array(color2) * mix


class DisplayInfo:
    """Just holds settings information for the user interface."""
    def __init__(self,
                 corner_size_factor,
                 camera_offset,
                 settlement_size,
                 tile_font,
                 player_start,
                 player_width,
                 player_font,
                 log_start,
                 log_amount,
                 window_size,
                 ):
        self.corner_size_factor = corner_size_factor
        self.camera_offset = camera_offset
        self.settlement_size = settlement_size
        self.tile_font = tile_font
        self.player_start = np.array(player_start)
        self.player_width = np.array((player_width, 0))
        self.player_font = player_font
        self.log_start = log_start
        self.log_amount = log_amount
        self.window_size = window_size


class PygameUserInterface(threading.Thread):
    """A graphical user interface using pygame."""
    def __init__(self, game_state, size=(1000, 700), fps=20):
        threading.Thread.__init__(self)
        pygame.init()
        self.window = pygame.display.set_mode(size)
        self.title = "Settlers of Catan"
        self.clock = pygame.time.Clock()
        pygame.font.init()

        self.display_info = DisplayInfo(
            corner_size_factor=(40, 24),
            camera_offset=(300, 240),
            settlement_size=(15, 20),
            tile_font=pygame.font.SysFont('arial', 20),
            player_start=(20, 560),
            player_width=150,
            player_font=pygame.font.SysFont('arial', 15),
            log_start=(600, 10),
            log_amount=16,
            window_size=size
        )

        self.game_state = game_state
        self.fps = fps
        self.running = None
        self.turn_options = []
        self.events = []

        self.start()

    def corner_draw_location(self, corner_location):
        """Converts the location from the corner-coordinate-system to the display-coordinate-system."""
        return (
                BoardPieces.CornerPiece.display_coordinate(corner_location)
                * self.display_info.corner_size_factor
                + self.display_info.camera_offset
        )

    def edge_draw_location(self, edge_location):
        """Converts the location from the edge-coordinate-system to the display-coordinate-system."""
        return sum([self.corner_draw_location(corner_location)
                    for corner_location in BoardPieces.EdgePiece.connected_corner_coordinates(edge_location)]) / 2

    def draw_corner_dot(self, corner_location, color):
        """Draws a dot on this corner-coordinate location."""
        pygame.draw.circle(self.window, color, self.corner_draw_location(corner_location), 5)

    def draw_edge_dot(self, edge_location, color):
        """Draws a dot on this edge-coordinate location."""
        pygame.draw.circle(self.window, color, self.edge_draw_location(edge_location).astype(int), 5)

    def draw_tile(self, tile: Tile):
        """Draws the hexagonal tile in the correct location."""
        point_list = [
            self.corner_draw_location(corner_location)
            for corner_location in tile.surrounding_corner_coordinates(tile.location)
        ]
        pygame.draw.polygon(self.window, tile_colors[tile.type], point_list)
        pygame.draw.polygon(self.window, (0, 0, 0), point_list, 3)
        text = str(tile.tokens)[1:-1]
        base_location = (
                self.corner_draw_location(tile.surrounding_corner_coordinates(tile.location)[0]) + np.array((-10, 35))
        )
        self.window.blit(self.display_info.tile_font.render(text, False, (210, 210, 210)), base_location)

    def draw_road(self, road: BoardPieces.Road):
        """Draws the road in the form of a line."""
        points = map(self.corner_draw_location, road.connected_corner_coordinates(road.get_location()))
        pygame.draw.line(self.window, self.game_state.get_player(road.player_id).get_color(), *points, 5)

    def draw_settlement(self, settlement: BoardPieces.Settlement):
        """Draws the settlement in the form of a house."""
        location = self.corner_draw_location(settlement.get_location())
        points = [
            (location + np.array(relative) * self.display_info.settlement_size).astype(np.int64)
            for relative in
            ((0, -0.8), (0.5, -0.3), (0.5, 0.5), (-0.5, 0.5), (-0.5, -0.3))
        ]
        pygame.draw.polygon(self.window, self.game_state.get_player(settlement.player_id).get_color(), points)
        pygame.draw.polygon(self.window, (0, 0, 0), points, 2)

    def draw_city(self, city: BoardPieces.City):
        """Draws the settlement in the form of a house."""
        location = self.corner_draw_location(city.get_location())
        points = [
            (location + np.array(relative) * self.display_info.settlement_size).astype(np.int64)
            for relative in
            ((0, -0.8), (0.5, -0.3), (0.5, 0.5), (-0.5, 0.5), (-1, 0.5), (-1, -0.3), (-0.5, -0.3))
        ]
        pygame.draw.polygon(self.window, self.game_state.get_player(city.player_id).get_color(), points)
        pygame.draw.polygon(self.window, (0, 0, 0), points, 2)

    def draw_player_index(self, player: Player):
        """Draws the resources this player has."""
        base_location = self.display_info.player_start + self.display_info.player_width * player.get_id()
        title = f'Player {player.get_id()}:'
        self.window.blit(self.display_info.player_font.render(title, False, player.get_color()), base_location)
        i = 1

        for key in sorted(player.resources):
            resource = (key, player.resources.get(key))
            self.window.blit(
                self.display_info.player_font.render(f"{resource[0]}: {resource[1]}", False, player.get_color()),
                base_location + np.array((0, 20)) * i
            )
            i += 1

    def show_produce_stats(self):
        """Shows how much a corner-location produces from red to green."""
        for location, points in self.game_state.board.pips.items():
            if self.game_state.board.surrounding_corners_free(location):
                self.draw_corner_dot(location, mix_colors((255, 0, 0), (0, 255, 0), min((points / 42, 1))))

    def show_cursor_info(self, mouse_pos):
        """Shows coordinate information by hovering the mouse over it."""
        corner_locations = self.game_state.board.all_placeable_corner_spots()
        display_corners = list(map(tuple, (map(self.corner_draw_location, corner_locations))))
        corner_index = closest_point_cursor(display_corners, mouse_pos)
        self.draw_corner_dot(corner_locations[corner_index], (255, 0, 255))

        edge_locations = self.game_state.board.all_placeable_edge_spots()
        display_edges = list(map(tuple, (map(self.edge_draw_location, edge_locations))))
        edge_index = closest_point_cursor(display_edges, mouse_pos)
        self.draw_edge_dot(edge_locations[edge_index], (255, 0, 255))

        text_location = display_corners[corner_index] + np.array((30, 30))
        pygame.draw.rect(self.window, (100, 100, 100), (*text_location, 110, 35))

        self.window.blit(self.display_info.player_font.render(
            f"Corner: {corner_locations[corner_index]}", False, (255, 255, 255)
        ), text_location)
        self.window.blit(self.display_info.player_font.render(
            f"Edge:   {list(edge_locations[edge_index])}", False, (255, 255, 255)
        ), text_location + np.array([0, 17]))

    def show_expandables(self):
        """Shows what corner and edge locations the players can expand to."""
        for player in self.game_state.players.values():
            player: Player
            for expandable_corner in player.get_expandable_corners():
                if self.game_state.board.surrounding_corners_free(expandable_corner):
                    self.draw_corner_dot(expandable_corner, player.get_color())
            for expandable_edge in player.get_expandable_edges():
                self.draw_edge_dot(expandable_edge, player.get_color())

    def show_log(self):
        """Shows the history of actions taken."""
        text_location = self.display_info.log_start
        for line in self.game_state.log[-self.display_info.log_amount:]:
            self.window.blit(self.display_info.player_font.render(line,  False, (200, 200, 200)), text_location)
            text_location += np.array((0, 17))

    def show_options(self):
        """Shows the actions the player has as options."""
        for option in self.turn_options:
            option.draw(self)

    def show_turn(self):
        """Shows who's turn it is currently."""
        self.window.blit(self.display_info.player_font.render(str(self.game_state.next_turn), False, WHITE), (10, 5))

    def run(self):
        """The main loop of the user interface, this runs on a separate thread."""
        self.running = True
        while self.running:
            # Pygame necessary processes for receiving user input and displaying
            pygame.display.flip()
            self.clock.tick(self.fps)
            pygame.display.set_caption(self.title)
            self.events = pygame.event.get()
            for event in self.events:
                if event.type == pygame.QUIT:
                    self.running = False
            mouse_pos = pygame.mouse.get_pos()
            self.window.fill((0, 0, 0))

            if self.game_state is not None:
                # Drawing the state of the game
                for tile in dict(self.game_state.board.tiles).values():
                    self.draw_tile(tile)
                for edge in dict(self.game_state.board.edge_pieces).values():
                    if type(edge) is BoardPieces.Road:
                        self.draw_road(edge)
                for corner in dict(self.game_state.board.corner_pieces).values():
                    if type(corner) is BoardPieces.Settlement:
                        self.draw_settlement(corner)
                    elif type(corner) is BoardPieces.City:
                        self.draw_city(corner)
                for player in dict(self.game_state.players).values():
                    self.draw_player_index(player)

                # Showing insight
                # self.show_produce_stats()
                # self.show_expandables()
                self.show_turn()
                self.show_log()
                self.show_cursor_info(mouse_pos)
                self.show_options()

        pygame.quit()

    def get_decision(self, valid_actions: list) -> Action:
        """Get a action decided by the player."""
        self.turn_options = list(map(Option, valid_actions))
        i = 0
        for option in self.turn_options:
            if not option.option_on_board():
                option.set_line(i)
                i += 1

        wait_mouse_up = True
        while wait_mouse_up:
            for event in self.events:
                if event.type == pygame.MOUSEBUTTONUP:
                    wait_mouse_up = False

        while True:
            for event in self.events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    selected = closest_point_cursor(
                        list(map(lambda x: x.display_position(self), self.turn_options)),
                        pygame.mouse.get_pos()
                    )
                    self.turn_options = []
                    return valid_actions[selected]


class Option:
    """A action that can be displayed on the screen."""
    def __init__(self, action: Action):
        self.action = action
        self.line = 0

    def draw(self, pygame_ui: PygameUserInterface):
        """Draw this option on the screen."""
        point = self.display_position(pygame_ui)
        pygame.draw.circle(pygame_ui.window, (255, 255, 255), point, 5)
        if not self.option_on_board():
            pygame_ui.window.blit(pygame_ui.display_info.player_font.render(
                f"{self.action}", False, (200, 200, 200)
            ), point + np.array((10, -7)))

    def display_position(self, pygame_ui: PygameUserInterface):
        """What screen-position this option claims."""
        if self.action.type == 'build':
            if self.action.get_info('build_type') == 'corner':
                return pygame_ui.corner_draw_location(self.action.get_info('location')).astype(int)
            else:
                return pygame_ui.edge_draw_location(self.action.get_info('location')).astype(int)
        else:
            text_start = pygame_ui.display_info.log_start[0], pygame_ui.display_info.window_size[1] - 25
            return text_start + np.array((0, -20)) * self.line

    def option_on_board(self) -> bool:
        """Should this option be displayed at the bord, else it should be displayed on the side."""
        return self.action.type in ('build',)

    def set_line(self, line: int):
        self.line = line
