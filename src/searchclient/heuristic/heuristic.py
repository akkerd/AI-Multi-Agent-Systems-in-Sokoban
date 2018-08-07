"""
    Author: Mathias Kaas-Olsen
    Date:   2016-02-11
"""
from common import manhattan_distance
from abc import ABCMeta, abstractmethod
from state import State
from .h_funct import h_constant_reward as h
from .setscore import set_score


class Heuristic(metaclass=ABCMeta):

    def __init__(self, initial_state: 'State', heuristic_function, dist_function=manhattan_distance, norm='', **kwargs):
        self.initial_state = initial_state
        self.heuristic_function = heuristic_function
        self.goals_list = list(initial_state.goals.keys())
        self.score_reward = set_score(self, initial_state, dist_function)
        self.dist_function = dist_function
        self.norm = norm

    def h(self, state: 'State') -> 'int':
        return self.heuristic_function(self, state, self.dist_function, self.norm)

    @abstractmethod
    def f(self, state: 'State') -> 'int': pass

    @abstractmethod
    def __repr__(self): raise NotImplementedError


class AStar(Heuristic):
    def __init__(self, initial_state: 'State', heuristic_function, **kwargs):
        super().__init__(initial_state, heuristic_function, **kwargs)

    def f(self, state: 'State') -> 'int':
        h_ = self.h(state)
        return state.g + h_

    def __repr__(self):
        return 'A* evaluation'


class WAStar(Heuristic):
    def __init__(self, initial_state: 'State', w: 'int', heuristic_function, **kwargs):
        super().__init__(initial_state, heuristic_function, **kwargs)
        self.w = w

    def f(self, state: 'State') -> 'int':
        return state.g + self.w * self.h(state)

    def __repr__(self):
        return 'WA* ({}) evaluation'.format(self.w)


class Greedy(Heuristic):
    def __init__(self, initial_state: 'State', heuristic_function, **kwargs):
        super().__init__(initial_state, heuristic_function, **kwargs)
    
    def f(self, state: 'State') -> 'int':
        return self.h(state)
    
    def __repr__(self):
        return 'Greedy evaluation'


def factory(name, initial_state, weight_value=5, heuristic_function=h, **kwargs):
    if name == "astar":
        return AStar(initial_state, heuristic_function, **kwargs)
    elif name == "wastar":
        return WAStar(initial_state, weight_value, heuristic_function, **kwargs)
    elif name == "greedy":
        return Greedy(initial_state, heuristic_function, **kwargs)
    # Temporal default value
    else:
        return AStar(initial_state, heuristic_function, **kwargs)
