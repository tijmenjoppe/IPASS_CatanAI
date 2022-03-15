from gameflow.ActionsAndTurns import Action, Turn
from gamemodels.Players import Player
from gamemodels import BoardPieces, Board
from gameflow import Dice


class GameState:
    """A state of the game."""
    def __init__(self, first_turn: Turn, end_game_points=10, board=Board.Board()):
        self.board = board
        self.players = {}
        self.last_turn = first_turn
        self.next_turn = first_turn  # Indicates who or what should take the next turn
        self.end_game_points = end_game_points  # The number of victory points a player needs to have to win
        self.amount_actions_done = 0
        self.log = []

    def add_player(self, player: Player) -> None:
        self.players[str(player.get_id())] = player

    def get_player(self, player_id) -> Player:
        return self.players[str(player_id)]

    def update_turn(self, new_turn: Turn) -> None:
        """Replace who's turn it is next."""
        self.last_turn, self.next_turn = self.next_turn, new_turn

    def apply_action(self, action: Action) -> None:
        """THE way to change the gamestate, by applying a action to the gamestae."""
        self.amount_actions_done += 1
        active_player = self.get_player(self.next_turn.player_id)

        if action.type == 'end_turn':
            self.update_turn(Turn.throw_dice((self.next_turn.player_id + 1) % len(self.players)))

        elif action.type == 'build':
            if action.get_info('build_type') == 'corner':
                corner_piece = action.get_info('corner_piece')
                self.board.set_corner_piece(action.get_info('location'), corner_piece)
                self.update_expandability_corner(active_player.get_id(), action.get_info('location'))
                active_player.corner_amount += 1

                if self.next_turn.type == 'first_settlement':
                    if self.next_turn.player_id < len(self.players) - 1:
                        self.update_turn(Turn.first_settlement(active_player.get_id() + 1))
                    else:
                        self.update_turn(Turn.second_settlement(active_player.get_id()))

                elif self.next_turn.type == 'second_settlement':
                    # TODO distribute first resources
                    if self.next_turn.player_id == 0:
                        self.update_turn(Turn.choose_turn(active_player.get_id()))
                    else:
                        self.update_turn(Turn.second_settlement(active_player.get_id() - 1))

                else:
                    active_player.remove_resources(corner_piece.build_materials())
                    self.update_turn(Turn.choose_turn(self.next_turn.player_id))

            elif action.get_info('build_type') == 'edge':
                self.board.set_edge_piece(action.get_info('location'), action.get_info('edge_piece'))
                active_player.remove_resources(action.get_info('edge_piece').build_materials())
                self.update_expandability_edge(active_player.get_id(), action.get_info('location'))
                active_player.corner_amount += 1
                self.update_turn(Turn.choose_turn(self.next_turn.player_id))

        elif action.type == 'dice_throw':
            for tile_locations in self.board.get_token(action.get_info('outcome')).get_tile_locations():
                self.board.get_tile(tile_locations).distribute_resources(self)
            self.update_turn(Turn.choose_turn(self.next_turn.player_id))

        elif action.type == 'maritime_trade':
            active_player.remove_resources(action.get_info('sell'))
            active_player.add_resources(action.get_info('buy'))
            self.update_turn(Turn.choose_turn(self.next_turn.player_id))

    def valid_actions(self) -> list:
        """Returns a list of all the valid actions the player whose turn it is can make."""
        player = self.get_player(self.next_turn.player_id)
        valid_actions = []

        if self.next_turn.type == 'throw_dice':
            valid_actions.extend(Dice.dice_weights.keys())

        elif self.next_turn.type == 'choose_turn':
            # build road actions
            if player.has_resources(BoardPieces.Road.build_materials()):
                for edge_location in player.get_expandable_edges():
                    if self.board.get_edge_piece(edge_location) is None:
                        road = BoardPieces.Road(player.get_id())
                        valid_actions.append(Action.place_edge(road, edge_location))

            # build settlement actions
            if player.has_resources(BoardPieces.Settlement.build_materials()):
                for corner_location in player.get_expandable_corners():
                    settlement = BoardPieces.Settlement(player.get_id())
                    valid_actions.append(Action.place_corner(settlement, corner_location))

            # build city actions
            if player.has_resources(BoardPieces.City.build_materials()):
                for settlement in self.board.get_settlements_of_player(player.get_id()).values():
                    city = BoardPieces.City(player.get_id())
                    valid_actions.append(Action.place_corner(city, settlement.get_location()))

            # maritime trade actions
            for sell_resource_type, amount in player.resources.items():
                if amount >= 4:
                    for buy_resource_type in ('brick', 'lumber', 'ore', 'grain', 'wool'):
                        if sell_resource_type != buy_resource_type:
                            valid_actions.append(Action.maritime_trade({sell_resource_type: 4}, {buy_resource_type: 1}))

            valid_actions.append(Action.end_turn())

        elif self.next_turn.type in ('first_settlement', 'second_settlement'):
            for corner_spot in self.board.all_placeable_corner_spots():
                if self.board.get_corner_piece(corner_spot) is None:
                    if self.board.surrounding_corners_free(corner_spot):
                        settlement = BoardPieces.Settlement(player.get_id())
                        settlement.set_location(corner_spot)
                        valid_actions.append(Action.place_corner(settlement, corner_spot))

        return valid_actions

    def is_valid_action(self, action: Action) -> bool:
        return action in self.valid_actions()

    def victory_points(self, player_id) -> int:
        """The number of victory points a certain player has."""
        victory_points = 0
        for corner in self.board.corner_pieces.values():
            if corner.player_id == player_id:
                if type(corner) == BoardPieces.Settlement:
                    victory_points += 1
                elif type(corner) == BoardPieces.City:
                    victory_points += 2
        # TODO give victory points for longest road and
        return victory_points

    def winners(self) -> list:
        """
        A list of players that have enough victory points.
        Nobody means the game isn't done yet and the list is empty
        """
        return [player.get_id() for player in self.players.values()
                if self.victory_points(player.get_id()) >= self.end_game_points]

    def update_expandability_corner(self, player_id, location) -> None:
        """Updating all the player on where they can expand to, now that this player has build on this location."""
        for player in self.players.values():
            player.update_expandable_corners(location, self.board, player_id)

    def update_expandability_edge(self, player_id, location) -> None:
        """Updating all the player on where they can expand to, now that this player has build on this location."""
        for player in self.players.values():
            player.update_expandable_edges(location, self.board, player_id)
