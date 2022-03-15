import socket
import threading
from gamemodels.Board import Board
from gameflow.GameLeader import GameLeader
from gameflow.Client import Client


def get_user_input(question: str, acceptance_function, extra_help='No extra help available') -> str:
    """
    Prevents wrong user inputs, by using a acceptance_function,
    that should return a boolean that indicates if the user input is in the correct format.
    """
    answer = '__answer_test__'
    while not acceptance_function(answer):
        print()
        answer = input(f"{question} ")
        if answer.lower() in ('help', '?'):
            print(extra_help)
        elif not acceptance_function(answer):
            print("Not a valid answer :(\nUse 'help' for extra help")
    return answer


def is_valid_ipv4_address(address: str) -> bool:
    """Is this string in the ipv4 format."""
    # Source: https://stackoverflow.com/a/4017219/12892735
    try:
        socket.inet_pton(socket.AF_INET, address)
    except AttributeError:  # no inet_pton here, sorry
        try:
            socket.inet_aton(address)
        except socket.error:
            return False
        return address.count('.') == 3
    except socket.error:  # not a valid address
        return False

    return True


def is_valid_layout(path_name: str) -> bool:
    """Is this string a valid file path to a valid game-board layout."""
    try:
        test_board = Board()
        test_board.load_layout(path_name)
    except IOError:
        return False
    except Exception as e:
        print(f"not valid path {path_name}, {e}")
        return False
    return True


def start_menu():
    if get_user_input(
            'Do you want to join or host a game?',
            lambda a: a.lower() in ('join', 'host'),
            "Choose between 'join' and 'host'"
    ).lower() == 'join':

        ip = get_user_input(
            'To what ip do you want to connect?',
            lambda a: is_valid_ipv4_address(a) or a == '',
            "Leave empty for the default localhost, else format it like this '192.168.42.69'"
        )
        if ip == '':
            ip = '127.0.0.1'

        join_game(ip)

    else:

        player_amount = int(get_user_input(
            'How many players do you want to play with?',
            lambda a: a.isdecimal(),
            "Choose a decimal number, include the number of bots in this number"
        ))
        layout_name = get_user_input(
            'Leave empty for the default board layout, else give the path here.',
            lambda a: is_valid_layout(a) or a == '',
            "Give the complete path to the layout file, like 'saves/example_layout.txt'"
        )
        if layout_name == '':
            layout_name = 'saves/example_layout.txt'
        number_of_bots = int(get_user_input(
            'How many AI players do you want?',
            lambda a: a.isdecimal() and a <= str(player_amount),
            "The number of bots you want in the game, can't be more than the amount of players you selected earlier"
        ))
        if number_of_bots > 0:
            difficulties = [
                int(get_user_input(
                    f"What should the difficultie be of the {i}'th bot be?",
                    lambda a: a.isdecimal(),
                    "Give a decimal number. "
                    "The higher the smarter, but the lower the faster the processing time will be"
                ))
                for i in range(number_of_bots)]
        else:
            difficulties = []

        host_game(player_amount, layout_name, difficulties)


def join_game(ip: str):
    """Join as player in a game hosted at this ip."""
    from userinterfaces.GraphicalDecisionMaker import PlayerDecisionMaker
    client = Client(PlayerDecisionMaker(), ip=ip)
    client.run()


def create_bot(difficulty=1000):
    """Creates a MCTS bot with this difficulty value."""
    from mcts.MCTS_DecisionMaker import MCTS_DecisionMaker
    return Client(MCTS_DecisionMaker(difficulty))


def host_game(player_amount: int, layout_path: str, difficulties: list):
    """Host a game by starting a server and bots."""
    GameLeader(player_amount=player_amount, layout_path=layout_path)

    for difficulty in difficulties:
        new_stread = threading.Thread(target=create_bot(difficulty).run)
        new_stread.start()

    join_game('127.0.0.1')


if __name__ == '__main__':
    start_menu()
