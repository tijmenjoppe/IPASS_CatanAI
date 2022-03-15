import socket
import time
import threading
import sys
sys.path.append('../')

from gameflow.ActionsAndTurns import Action, Turn   # noqa: E402
from gamemodels import Players, GameState, Board    # noqa: E402
from gameflow import Dice   # noqa: E402
from gameflow.NetworkBasis import NetworkBasis  # noqa: E402

player_colors = [
    (0, 100, 255),
    (255, 50, 50),
    (200, 200, 200),
    (255, 255, 0),
]


class Client(NetworkBasis):
    """A representation of the client for the gameleader."""
    def __init__(self, client_address, client_socket, player_id):
        super().__init__(client_socket)
        self.client_address = client_address
        self.player_id = player_id

    def set_player_id(self, player_id) -> None:
        self.player_id = player_id
        self.socket.send(bytes(player_id))


class GameLeader(threading.Thread):
    """
    He who controls the game/game-flow, and communicates this to the players/clients.
    Could also be called server.
    """
    def __init__(self, ip="0.0.0.0", port=20903, player_amount=4, layout_path='../saves/example_layout.txt'):
        threading.Thread.__init__(self)

        self.player_amount = player_amount
        self.game = GameState.GameState(Turn.first_settlement(0), end_game_points=10)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((ip, port))
        self.clients = []
        self.game.board.load_layout(layout_path)

        print("Server started")
        self.start()

    def get_client(self, player_id) -> Client:
        for client in self.clients:
            if client.player_id == player_id:
                return client

    def wait_players(self) -> None:
        print("Waiting for client request..")
        for player_index in range(self.player_amount):
            self.socket.listen(1)
            client_socket, client_address = self.socket.accept()
            new_thread = Client(client_address, client_socket, player_index)
            new_thread.send({'set_player_id': player_index})
            self.game.add_player(Players.Player(player_index, player_colors[player_index]))
            self.clients.append(new_thread)
            print("New connection added:", client_address)

    def send_startup_info(self) -> None:
        """Send the initial setup/layout to all the players."""
        self.send_all({'set_game': self.game})

    def run(self) -> None:
        """This will be run in a separate thread."""
        self.wait_players()
        self.send_startup_info()
        self.game_loop()

    def game_loop(self) -> None:
        """The flow of the game by taking turns."""
        while len(self.game.winners()) == 0:
            action = None
            if self.game.next_turn.type == 'throw_dice':
                # This action is chosen on the GameLeader/server side to prevent a player from "committing fraud"
                time.sleep(0.3)
                action = Action.dice_throw(Dice.throw_dice())
            else:
                # Get action from client
                valid_turn = False
                while not valid_turn:
                    turn_client = self.get_client(self.game.next_turn.player_id)
                    turn_client.send({'get_action': self.game.next_turn})

                    action = turn_client.receive().get('apply_action')
                    valid_turn = self.game.is_valid_action(action)
                    if not valid_turn:
                        print(f"{action} not a valid turn")

            print(f"Player {self.game.next_turn.player_id}: {action}")
            self.game.apply_action(action)
            self.game.log.append(f"player {self.game.next_turn.player_id} {action}")
            self.send_all({'apply_action': action})

        self.send_all({'game_over': True})
        print(f"Game Over, player {str(self.game.winners())[1:-1]} won!")
    
    def send_all(self, message) -> None:
        for client in self.clients:
            client: Client
            client.send(message)


if __name__ == '__main__':
    # Generates the example board
    test_board = Board.example_board()
    test_board.save_layout('../saves/example_layout.txt')
