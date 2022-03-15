import math
import random
import os
import sys
sys.path.append('../')

from copy import deepcopy   # noqa: E402
from gameflow import Dice   # noqa: E402
from gamemodels.GameState import GameState  # noqa: E402
from gameflow.ActionsAndTurns import Action     # noqa: E402

sys.setrecursionlimit(1000000)


def multiple_max(lst, func):
    """Returns multiple items if it has a shared first place."""
    max_outcome = max(map(func, lst))
    return [a for a in lst if func(a) == max_outcome]


def domain_knowledge_weights(experiment: GameState, valid_actions: list) -> list:
    """
    Domain knowledge in Monte-Carlo simulations from
    https://www.researchgate.net/publication/220716999_Monte-Carlo_Tree_Search_in_Settlers_of_Catan
    Adding weights to certain actions so it more closely matches smarter play.
    """
    weights = []
    for action in valid_actions:
        weight = 1
        if action.type == 'build':
            if action.get_info('build_type') == 'corner':
                weight += 10000
            else:
                player = experiment.get_player(experiment.next_turn.player_id)
                weight += player.edge_amount / player.corner_amount
        weights.append(weight)
    return weights


class Node:
    """A node in the MCTS-tree."""
    def __init__(self, game_state: GameState, parent=None, action_used=None):
        self.parent = parent
        self.action_used = action_used
        self.game_state = game_state
        self.children = None

        self.score = 0  # wi
        self.times_visited = 0  # ni
        self.impossible = False
        self.times_impossible = 0
        self.id = None
        self.simulations = []   # A simulation is a list of actions
        self.begin_simulations = []     # The node from which the simulation was started

    def create_child(self, action: Action):
        game_state_clone = deepcopy(self.game_state)
        game_state_clone.apply_action(action)
        return Node(game_state_clone, self, action)

    def average_reward(self) -> float:
        return self.score / self.times_visited

    def is_leaf_node(self) -> bool:
        return self.children is None

    def is_root_node(self) -> bool:
        return self.parent is None

    def number_simulations_parent(self) -> int:  # Ni
        """The total number simulations after the i-th move run by the parent node of the one considered."""
        return self.parent.times_visited

    def ucb(self, c) -> float:
        """
        Upper Confidence Bound, used to create balance between exploitation and exploration.
        The bigger the result, the more "interesting" it is to explore this child.
        """
        if self.parent is None:
            return 0
        if self.times_visited == 0:
            return float('inf')
        return (
            self.average_reward() +
            float(c) * math.sqrt(math.log(self.number_simulations_parent()) / self.times_visited)
        )

    def select(self, c):
        """
        Select the most "interesting" node to explore.
        This can be because it gives a better score,
        or the opponent is more likely to choose because it results in a better score for him,
        or because it is more likely too happen because the dice throws this more often,
        or simply because it hasn't been explored a lot yet.
        """
        if self.is_leaf_node():
            return self
        if self.game_state.next_turn.type == 'throw_dice':
            return self.children[Dice.throw_dice() - 2].select(c)
        else:
            return max(self.children, key=lambda node: node.ucb(c)).select(c)

    def expand(self) -> None:
        """Expands by taking the valid actions and transform them to other nodes and adding them to it's children."""
        turn_type = self.game_state.next_turn.type
        if turn_type == 'throw_dice':
            self.children = [self.create_child(Action.dice_throw(i)) for i in range(2, 13)]
        else:
            self.children = [self.create_child(action) for action in self.game_state.valid_actions()]

    def simulate(self, timeout) -> (list, list):
        """Take semi-random action until the end of the game is reached, return the outcome."""
        experiment = deepcopy(self.game_state)
        simulation = []     # is a list of actions
        while True:
            if experiment.amount_actions_done > timeout:
                self.impossible = True
                return [], simulation
            winners = experiment.winners()
            if len(winners) > 0:
                return winners, simulation

            if experiment.next_turn.type == 'throw_dice':
                action_chosen = Action.dice_throw(Dice.throw_dice())
            else:
                valid_actions = experiment.valid_actions()
                weights = domain_knowledge_weights(experiment, valid_actions)

                action_chosen = random.choices(valid_actions, weights, k=1)[0]

            simulation.append(action_chosen)
            experiment.apply_action(action_chosen)

    def backpropagate(self, winners, simulation: list, begin_simulation) -> None:
        """Backpropagate the outcome information back up the tree."""
        self.times_visited += 1
        self.simulations.append(simulation)
        self.begin_simulations.append(begin_simulation)
        if self.game_state.last_turn.player_id in winners:
            if len(simulation) == 0:
                self.score += float('inf')
            else:
                self.score += 1 + 0.1 / len(simulation)
        if not self.is_root_node():
            if self.impossible:
                self.impossible = False
                self.parent.impossible = True
                self.times_impossible += 1
            self.parent.backpropagate(winners, simulation, begin_simulation)

    def visualize_tree(self, c, previous='') -> str:
        """Visualize the tree in the terminal."""
        impossible_string = f"\033[91m{self.times_impossible}\033[0m, " if self.times_impossible != 0 else ''
        string = f"\n{previous}{self.id}|\033[92m{'{:5.2f}'.format(self.score)}/\033[93m{self.times_visited}" \
                 f"\033[94m:{'{:5.4f}'.format(self.ucb(c))}\033[0m, {impossible_string}last_turn: " \
                 f"{self.game_state.last_turn}, action: {self.action_used}, next_turn: {self.game_state.next_turn}"
        if len(previous) >= 3:
            if previous[-3:] == '├──':
                previous = previous[:-3] + '│  '
            elif previous[-3:] == '└──':
                previous = previous[:-3] + '   '
        if self.children is not None:
            for i in range(len(self.children)):
                child = self.children[i]
                front = previous
                if i+1 == len(self.children):
                    front += '└──'
                else:
                    front += '├──'
                string += f"{child.visualize_tree(c, front)}"
        return string

    def best_choice(self) -> Action:
        """Concludes what the best action has been looking at the tree."""
        most_visited_node = multiple_max(self.children, lambda node: node.times_visited)
        most_wins_node = max(most_visited_node, key=lambda node: node.score)
        return most_wins_node.action_used


def run_mcts(root_node: Node, iteration_amount: int, c: float, visualize_tree=False) -> None:
    """Run the Monte Carlo Tree Search process and iterate so many times."""

    print(root_node.times_visited)
    while root_node.times_visited < iteration_amount:

        if visualize_tree:
            visual = root_node.visualize_tree(c)[1:]
            os.system('cls' if os.name == 'nt' else 'clear')
            sys.stdout.write(visual)
        else:
            print(f"\r{'{:.1f}'.format(root_node.score)}/{root_node.times_visited}", end='')

        selected = root_node.select(c)  # Selection

        if selected.times_visited != 0:
            selected.expand()   # Expansion
            if selected.game_state.next_turn.type == 'throw_dice':
                selected = selected.children[Dice.throw_dice() - 2]
            else:
                selected = selected.children[0]

        winners, simulation = selected.simulate(100000)     # Simulation

        selected.backpropagate(winners, simulation, selected)   # Backpropagation

    print()


def end_of_simulation(game_state: GameState, simulation: list) -> GameState:
    """When applying a list of actions to a gamestate, what will the outcome gamestate be."""
    experiment = deepcopy(game_state)
    for action in simulation:
        experiment.apply_action(action)
    return experiment
