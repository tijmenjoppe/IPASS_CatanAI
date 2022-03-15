import time
import sys
sys.path.append('../')

import gameflow.Client as Client    # noqa: E402
from gameflow.ActionsAndTurns import Action     # noqa: E402
from gamemodels.GameState import GameState      # noqa: E402


class PlayerDecisionMaker(Client.DecisionMaker):
    """A decision maker, that in this case asks the player on a pygame window."""
    def __init__(self):
        super().__init__()
        from userinterfaces import PygameUI
        self.ui = PygameUI.PygameUserInterface(None)

    def set_game(self, game_state: GameState):
        self.game = game_state
        self.ui.game_state = game_state

    def make_decision(self) -> Action:
        """Decides which action will be taken next."""
        valid_actions = self.game.valid_actions()
        if len(valid_actions) == 1:
            time.sleep(0.3)
            return valid_actions[0]
        print("\nOptions:")
        for i in range(len(valid_actions)):
            print(f"{i}:\t{valid_actions[i]}")
        print()
        return self.ui.get_decision(valid_actions)

    def set_player_id(self, player_id: int):
        super().set_player_id(player_id)
        # TODO fix so it actually displays the new title
        self.ui.title = f"Settlers of Catan, Player {player_id}"


if __name__ == '__main__':
    client = Client.Client(PlayerDecisionMaker())
    client.run()
