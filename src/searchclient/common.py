from state import State
from typing import Tuple


def manhattan_distance(cell1, cell2):
    """
    Manhattan distance between cells
    :param cell1: tuple (row, col)
    :param cell2: tuple (row, col)
    :return: manhattan distance (1-norm)
    """
    return abs(cell2[0] - cell1[0])+abs(cell2[1] - cell1[1])


def max_index(a, b):
    mult = [a[i]*b[i] for i in range(len(a))]
    maxval = max(mult)
    return mult.index(maxval)


def goal_done(state: 'State', pos: Tuple[int, int]) -> 'bool':
    goal = state.goals.get(pos)
    box = state.boxes.get(pos)
    if goal is not None \
            and box is not None \
            and goal[0] == box[0].lower():
        return True
    else:
        return False
