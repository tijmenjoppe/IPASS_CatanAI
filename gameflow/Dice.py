import random
from gameflow.ActionsAndTurns import Action

dice_weights = {
    Action.dice_throw(2): 3, Action.dice_throw(12): 3,
    Action.dice_throw(3): 6, Action.dice_throw(11): 6,
    Action.dice_throw(4): 8, Action.dice_throw(10): 8,
    Action.dice_throw(5): 11, Action.dice_throw(9): 11,
    Action.dice_throw(6): 14, Action.dice_throw(8): 14,
    Action.dice_throw(7): 17,
}


def throw_dice(dice_amount=2, amount_sides=6) -> int:
    """Generates a random number with the chance distribution."""
    return sum([random.randint(1, amount_sides) for i in range(dice_amount)])
