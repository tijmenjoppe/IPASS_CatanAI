import socket
import sys
sys.path.append('../')

from gameflow.NetworkBasis import NetworkBasis  # noqa: E402
from gameflow.ActionsAndTurns import Action     # noqa: E402
from gamemodels.GameState import GameState  # noqa: E402


class Client(NetworkBasis):
    """A client that connects to the game-leader/server."""
    def __init__(self, decision_maker, ip='127.0.0.1', port=20903):
        super().__init__(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
        self.socket.connect((ip, port))
        self.decision_maker = decision_maker

        self.running = None
        self.game = None

    def run(self) -> None:
        """The main loop of listening and reacting to what the game-leader sends."""
        self.running = True
        while self.running:
            in_data = self.receive()
            print("Server sends:", in_data)

            if 'set_player_id' in in_data:
                self.decision_maker.set_player_id = in_data.get('set_player_id')
            if 'set_game' in in_data:
                self.game = in_data.get('set_game')
                self.decision_maker.set_game(self.game)
            if 'game_over' in in_data:
                if in_data.get('game_over'):
                    self.running = False
            if 'apply_action' in in_data:
                self.game.log.append(f"player {self.game.next_turn.player_id} {in_data.get('apply_action')}")
                self.game.apply_action(in_data.get('apply_action'))
            if 'get_action' in in_data:
                decision = self.decision_maker.make_decision()
                self.send({'apply_action': decision})

        self.socket.close()


class DecisionMaker:
    """A interface for classes that make the actual choices."""
    def __init__(self):
        self.game = None
        self.player_id = None

    def set_game(self, game_state: GameState) -> None:
        self.game = game_state

    def set_player_id(self, player_id: int) -> None:
        self.player_id = player_id

    def make_decision(self) -> Action:
        """This is a placeholder"""
        pass
