from gamemodels import BoardPieces


class Action:
    """A change of game-state, for example a placement of a settlement or a dice throw."""
    def __init__(self, action_type: str, extra_info: dict):
        self.type = action_type
        self.extra_info = extra_info

    def get_info(self, key):
        return self.extra_info[key]

    @classmethod
    def end_turn(cls):
        return Action('end_turn', {})

    @classmethod
    def place_corner(cls, corner: BoardPieces.CornerPiece, location):
        return Action('build', {'build_type': 'corner', 'corner_piece': corner, 'location': location})

    @classmethod
    def place_edge(cls, edge: BoardPieces.EdgePiece, location):
        return Action('build', {'build_type': 'edge', 'edge_piece': edge, 'location': location})

    @classmethod
    def dice_throw(cls, outcome):
        return Action('dice_throw', {'outcome': outcome})

    @classmethod
    def maritime_trade(cls, sell_resources, buy_resources):
        return Action('maritime_trade', {'sell': sell_resources, 'buy': buy_resources})

    def __repr__(self) -> str:
        string = str(self.type) + ': '
        if self.type == 'build':
            if self.get_info('build_type') == 'corner':
                string += f"{type(self.get_info('corner_piece')).__name__}"
            elif self.get_info('build_type') == 'edge':
                string += f"{type(self.get_info('edge_piece')).__name__}"
            string += f"{self.get_info('location')}"
        elif self.type == 'maritime_trade':
            string += f"{list(self.get_info('sell').keys())[0]} -> {list(self.get_info('buy').keys())[0]}"
        elif self.type == 'end_turn':
            pass
        elif self.type == 'dice_throw':
            string += str(self.get_info('outcome'))
        else:
            string += f"{self.extra_info}"
        return string

    def __eq__(self, other):
        return self.type == other.type and str(self.extra_info) == str(other.extra_info)

    def __hash__(self):
        return hash(self.type) + hash(str(self.extra_info))


class Turn:
    """Indicates who and what kind of action should be next."""
    def __init__(self, turn_type, player_id):
        self.type = turn_type
        self.player_id = player_id

    @classmethod
    def choose_turn(cls, player_id):
        return Turn('choose_turn', player_id)

    @classmethod
    def throw_dice(cls, player_id):
        return Turn('throw_dice', player_id)

    @classmethod
    def build(cls, player_id):
        return Turn('build', player_id)

    @classmethod
    def first_settlement(cls, player_id):
        return Turn('first_settlement', player_id)

    @classmethod
    def second_settlement(cls, player_id):
        return Turn('second_settlement', player_id)

    def __repr__(self):
        return f"{self.type}, player {self.player_id}"
