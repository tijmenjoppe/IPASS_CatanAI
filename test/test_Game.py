from unittest import TestCase
import numpy as np
from statistics import mode
from gameflow.ActionsAndTurns import Action, Turn
from gamemodels import Players, GameState, BoardPieces, Tiles
from gameflow import Dice


class TestDice(TestCase):
    def test_dice_throw(self):
        outcomes = []
        for i in range(1000):
            outcome = Dice.throw_dice()
            # Check if every outcome is between 2 and 12
            self.assertTrue(2 <= outcome <= 12)
            outcomes.append(outcome)

        # Check that the most common outcome is 7
        self.assertEqual(mode(outcomes), 7)


class TestGameState(TestCase):
    def setUp(self):
        self.game = GameState.GameState(Turn.choose_turn(0))
        self.game.add_player(Players.Player(0, (0, 0, 0)))
        self.game.add_player(Players.Player(1, (0, 0, 0)))
        self.game.board.set_tile(np.array((0, 0)), Tiles.Tile('hills'))
        self.game.board.set_tile(np.array((1, 0)), Tiles.Tile('forest'))
        self.game.get_player(0).add_resources({'brick': 4, 'lumber': 4, 'ore': 4, 'grain': 4, 'wool': 4})

    def test_build_settlement(self):
        settlement = BoardPieces.Settlement(0)
        self.game.apply_action(Action.place_corner(settlement, np.array((1, 0))))

        # Check that the building cost are taken from the player
        self.assertEqual(
            self.game.get_player(0).get_resources(),
            {'brick': 3, 'lumber': 3, 'ore': 4, 'grain': 3, 'wool': 3}
        )
        # Check that the settlement is placed at the correct location
        self.assertEqual(
            self.game.board.corner_pieces,
            {(1, 0): settlement}
        )
        # Check that the expandability options of the player are updated
        self.assertEqual(
            self.game.get_player(0).expandable_edge_locations,
            {(1, 0), (3, 1)}
        )

    def test_build_road(self):
        road = BoardPieces.Road(0)
        self.game.apply_action(Action.place_edge(road, np.array((3, 1))))

        # Check that the building cost are taken from the player
        self.assertEqual(
            self.game.get_player(0).get_resources(),
            {'brick': 3, 'lumber': 3, 'ore': 4, 'grain': 4, 'wool': 4}
        )
        # Check that the road is placed at the correct location
        self.assertEqual(
            self.game.board.edge_pieces,
            {(3, 1): road}
        )
        # Check that the expandability options of the player are updated
        self.assertEqual(
            self.game.get_player(0).expandable_corner_locations,
            {(1, 0), (2, 1)}
        )
        self.assertEqual(
            self.game.get_player(0).expandable_edge_locations,
            {(1, 0), (5, 2), (4, 3)}
        )

    def test_end_turn(self):
        self.game.apply_action(Action.end_turn())

        # Check that the turn is of the next player
        self.assertEqual(self.game.next_turn.player_id, 1)
        # Check that the next player needs to throw the dice
        self.assertEqual(self.game.next_turn.type, 'throw_dice')

    def test_maritime_trade(self):
        self.game.apply_action(Action.maritime_trade({'ore': 4}, {'brick': 1}))

        # Check that the player has the correct resource inventory
        self.assertEqual(
            self.game.get_player(0).get_resources(),
            {'brick': 5, 'lumber': 4, 'ore': 0, 'grain': 4, 'wool': 4}
        )

    def test_valid_actions(self):
        self.game.get_player(0).add_resources({'brick': 3, 'lumber': 3, 'grain': 1, 'wool': 1})
        self.game.apply_action(Action.place_corner(BoardPieces.Settlement(0), np.array((0, 0))))
        self.game.apply_action(Action.place_edge(BoardPieces.Road(0), np.array((1, 0))))
        self.game.apply_action(Action.place_edge(BoardPieces.Road(0), np.array((3, 1))))

        # Check that the valid action generated are correct
        self.assertEqual(
            self.game.valid_actions(),
            [
                Action.place_edge(BoardPieces.Road(0), np.array((0, 1))),
                Action.place_edge(BoardPieces.Road(0), np.array((4, 3))),
                Action.place_edge(BoardPieces.Road(0), np.array((5, 2))),
                Action.place_corner(BoardPieces.Settlement(0), np.array((2, 1))),
                Action.place_corner(BoardPieces.City(0), np.array((0, 0))),
                Action.maritime_trade({'brick': 4}, {'lumber': 1}),
                Action.maritime_trade({'brick': 4}, {'ore': 1}),
                Action.maritime_trade({'brick': 4}, {'grain': 1}),
                Action.maritime_trade({'brick': 4}, {'wool': 1}),
                Action.maritime_trade({'lumber': 4}, {'brick': 1}),
                Action.maritime_trade({'lumber': 4}, {'ore': 1}),
                Action.maritime_trade({'lumber': 4}, {'grain': 1}),
                Action.maritime_trade({'lumber': 4}, {'wool': 1}),
                Action.maritime_trade({'ore': 4}, {'brick': 1}),
                Action.maritime_trade({'ore': 4}, {'lumber': 1}),
                Action.maritime_trade({'ore': 4}, {'grain': 1}),
                Action.maritime_trade({'ore': 4}, {'wool': 1}),
                Action.maritime_trade({'grain': 4}, {'brick': 1}),
                Action.maritime_trade({'grain': 4}, {'lumber': 1}),
                Action.maritime_trade({'grain': 4}, {'ore': 1}),
                Action.maritime_trade({'grain': 4}, {'wool': 1}),
                Action.maritime_trade({'wool': 4}, {'brick': 1}),
                Action.maritime_trade({'wool': 4}, {'lumber': 1}),
                Action.maritime_trade({'wool': 4}, {'ore': 1}),
                Action.maritime_trade({'wool': 4}, {'grain': 1}),
                Action.end_turn(),
            ]
        )
