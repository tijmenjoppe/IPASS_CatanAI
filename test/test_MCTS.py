from unittest import TestCase
import math
from mcts import MCTS_Node
from gamemodels.GameState import GameState
from gamemodels.Players import Player
from gameflow.ActionsAndTurns import Action, Turn


class TestNode(TestCase):
    def setUp(self):
        self.c = math.sqrt(2)
        self.game = GameState(Turn.choose_turn(0))
        self.game.add_player(Player(0, (0, 0, 0)))
        self.root = MCTS_Node.Node(self.game)
        self.root.times_visited += 1

    def test_best_choice(self):
        """Test that it picks the best choice after the MCTS process is run."""
        game = GameState(Turn.choose_turn(0))
        game.add_player(Player(0, (0, 0, 0)))
        root = MCTS_Node.Node(game)
        root.children = [root.create_child(Action.dice_throw(i)) for i in range(2, 13)]
        root.children[5].times_visited += 1

        # Check that it picks the best action after the process
        self.assertEqual(root.best_choice(), Action.dice_throw(7))

    def test_select(self):
        """Test that the selection part works good."""
        # Check that it selects it self when it hasn't been simulated yet
        self.assertEqual(self.root.select(self.c), self.root)

        self.root.children = [self.root.create_child(Action.dice_throw(i)) for i in range(2, 13)]
        self.root.children[5].times_visited += 1
        for child in self.root.children:
            child.times_visited += 1
        self.root.children[5].score += 1

        # Check that it selects the right node
        self.assertEqual(self.root.select(self.c), self.root.children[5])

    def test_backpropagate(self):
        """Test that the backpropagate part works good."""
        first_child = self.root.create_child(Action.end_turn())
        self.root.children = [first_child]
        second_child = first_child.create_child(Action.dice_throw(7))
        first_child.children = [second_child]

        # This should be the state before the backpropagation
        self.assertEqual(self.root.times_visited, 1)
        self.assertEqual(first_child.times_visited, 0)
        self.assertEqual(first_child.children[0].times_visited, 0)

        second_child.backpropagate([0], [], None)

        # Check that the information is backpropagated correctly
        self.assertEqual(self.root.times_visited, 2)
        self.assertEqual(first_child.times_visited, 1)
        self.assertEqual(first_child.children[0].times_visited, 1)
