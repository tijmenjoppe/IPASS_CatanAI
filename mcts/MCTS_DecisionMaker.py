import math
import sys
sys.path.append('../')

import gameflow.Client as Client    # noqa: E402
from gameflow.ActionsAndTurns import Action     # noqa: E402
from mcts.MCTS_Node import Node, run_mcts, multiple_max      # noqa: E402


class MCTS_DecisionMaker(Client.DecisionMaker):
    """A decision maker, that in this case uses the MCTS process."""
    def __init__(self, iteration_amount, c=math.sqrt(2)):
        super().__init__()
        self.iteration_amount = iteration_amount
        self.c = c  # exploration parameter
        self.past_usable = None

    def make_decision(self) -> Action:
        """Decides which action will be taken next."""
        if len(self.game.valid_actions()) == 1:
            return self.game.valid_actions()[0]
        else:
            if self.past_usable is None:
                root_node = Node(self.game)
            else:
                root_node = self.past_usable

            run_mcts(root_node, self.iteration_amount, self.c)

            most_visited_node = multiple_max(root_node.children, lambda node: node.times_visited)
            most_wins_node = max(most_visited_node, key=lambda node: node.score)
            if most_wins_node.game_state.next_turn.player_id == root_node.game_state.next_turn.player_id:
                self.past_usable = most_wins_node
                self.past_usable.parent = None
            else:
                self.past_usable = None
            return most_wins_node.action_used


if __name__ == '__main__':
    g_client = Client.Client(MCTS_DecisionMaker(1000))
    g_client.run()
