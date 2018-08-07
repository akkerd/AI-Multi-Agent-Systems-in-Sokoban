'''
    Author: Mathias Kaas-Olsen
    Date:   2016-02-11
'''

from abc import ABCMeta, abstractmethod
from collections import deque, namedtuple
from time import perf_counter
from queue import PriorityQueue as prioque
from heuristic import factory as heuristic_factory
from state import State
from preprocessing import GoalMap, NodeType, one_freq_letter
from heuristic import Heuristic
from typing import List, Iterable, Tuple, Dict
from preprocessing import Planner
from heuristic.h_funct import _choose_box_for_goal
from common import goal_done
from .conditions import *
import memory


class Strategy(metaclass=ABCMeta):

    def __init__(self):
        self.explored = set()
        self.start_time = perf_counter()

    def add_to_explored(self, state: 'State'):
        self.explored.add(state)

    def is_explored(self, state: 'State') -> 'bool':
        return state in self.explored

    def explored_count(self) -> 'int':
        return len(self.explored)

    def time_spent(self) -> 'float':
        return perf_counter() - self.start_time

    def search_status(self) -> 'str':
        return '#Explored: {:4}, #Frontier: {:3}, Time: {:3.2f} s, Alloc: {:4.2f} MB, MaxAlloc: {:4.2f} MB'.format(
            self.explored_count(), self.frontier_count(), self.time_spent(), memory.get_usage(), memory.max_usage)

    def is_goal_state(self, state: 'State'):
        return state.is_subgoal_state()

    @abstractmethod
    def get_and_remove_leaf(self) -> 'State': raise NotImplementedError

    @abstractmethod
    def add_to_frontier(self, state: 'State'): raise NotImplementedError

    @abstractmethod
    def in_frontier(self, state: 'State') -> 'bool': raise NotImplementedError

    @abstractmethod
    def frontier_count(self) -> 'int': raise NotImplementedError

    @abstractmethod
    def frontier_empty(self) -> 'bool': raise NotImplementedError

    @abstractmethod
    def __repr__(self): raise NotImplementedError


class StrategyBFS(Strategy):
    def __init__(self):
        super().__init__()
        self.frontier = deque()
        self.frontier_set = set()

    def get_and_remove_leaf(self) -> 'State':
        leaf = self.frontier.popleft()
        self.frontier_set.remove(leaf)
        return leaf

    def add_to_frontier(self, state: 'State'):
        self.frontier.append(state)
        self.frontier_set.add(state)

    def in_frontier(self, state: 'State') -> 'bool':
        return state in self.frontier_set

    def frontier_count(self) -> 'int':
        return len(self.frontier)

    def frontier_empty(self) -> 'bool':
        return len(self.frontier) == 0

    def __repr__(self):
        return 'Breadth-first Search'


class StrategyDFS(Strategy):
    def __init__(self):
        super().__init__()
        self.frontier = deque()
        self.frontier_set = set()

    def get_and_remove_leaf(self) -> 'State':
        leaf = self.frontier.pop()
        self.frontier_set.remove(leaf)
        return leaf

    def add_to_frontier(self, state: 'State'):
        self.frontier.append(state)
        self.frontier_set.add(state)

    def in_frontier(self, state: 'State') -> 'bool':
        return state in self.frontier_set

    def frontier_count(self) -> 'int':
        return len(self.frontier)

    def frontier_empty(self) -> 'bool':
        return len(self.frontier) == 0

    def __repr__(self):
        return 'Depth-first Search'


class StrategyBestFirst(Strategy):
    def __init__(self, heuristic: 'Heuristic', **kwargs):
        super().__init__()
        self.heuristic = heuristic
        self.frontier = prioque()
        self.frontier_set = set()

    def get_and_remove_leaf(self) -> 'State':
        leaf = self.frontier.get().data
        # I have created a PEntry class to know how to compare the tuples (priority, state)
        self.frontier_set.remove(leaf)
        return leaf

    def add_to_frontier(self, state: 'State'):
        # I have created a PEntry class to know how to compare the tuples (priority, state)
        self.frontier.put(PEntry(self.heuristic.f(state), state))
        self.frontier_set.add(state)

    def in_frontier(self, state: 'State') -> 'bool':
        return state in self.frontier_set

    def frontier_count(self) -> 'int':
        return self.frontier.qsize()

    def frontier_empty(self) -> 'bool':
        return self.frontier.empty()

    def __repr__(self):
        return 'Best-first Search (PriorityQueue) using {}'.format(self.heuristic)


class StrategyCompBestFirst(StrategyBestFirst):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.goal_constant = 0

    def add_to_frontier(self, state: 'State'):
        self.frontier.put(AltPEntry(self.heuristic.f(state), state, self))
        self.frontier_set.add(state)


class PEntry(object):
    def __init__(self, priority, data):
        self.data = data
        self.priority = priority

    def __lt__(self, other):
        return self.priority < other.priority


class AltPEntry(PEntry):

    def __init__(self, priority, data, strategy):
        super().__init__(priority, data)
        self.data = data
        self.strategy = strategy

    @property
    def priority(self):
        return super().priority + self.strategy.goal_constant * (self.data.total_goals - self.data.solved_goals)

    @priority.setter
    def priority(self, val):
        super().priority = val


class SuperStrategy(Strategy):

    def __init__(self, name: 'str', **kwargs):
        super().__init__()
        self.name = name
        self.strategy = None
        self._frontier_len = 0
        self._explored_len = 0
        self.strategy_attributes = kwargs

    def get_and_remove_leaf(self) -> 'State':
        pass

    def add_to_frontier(self, state: 'State'):
        pass

    def in_frontier(self, state: 'State') -> 'bool':
        return self.strategy.in_frontier(state)

    def frontier_count(self) -> 'int':
        return self._frontier_len

    def frontier_empty(self) -> 'bool':
        return self.strategy.frontier_empty()

    def __repr__(self):
        if self.strategy is None:
            return 'SuperStrategy using {}'.format(self.name)
        else:
            return 'SuperStrategy using {}'.format(self.strategy)

    def add_to_explored(self, state: 'State'):
        self.strategy.explored.add(state)
        self._explored_len += 1

    def is_explored(self, state: 'State') -> 'bool':
        return state in self.strategy.explored

    def explored_count(self) -> 'int':
        return self._explored_len


class StrategySubGoalSeparation(SuperStrategy):

    def __init__(self, name: 'str', initial_state: 'State', **kwargs):

        super().__init__(name, **kwargs)
        # Attribute assignment
        self.current_goals: 'Dict' = {}
        self.initial_state: 'State' = initial_state

        priority_function = kwargs.get("priority_function")
        if priority_function is None:
            self.all_goals: 'List' = initial_state.goals
        else:
            self.all_goals: 'List' = priority_function(state=initial_state, **kwargs)
        self.planner: 'Planner' = kwargs.get("planner")
        self.goal_index: 'int' = 0
        self.goal_max_index: 'int' = len(self.all_goals)

        self.init = False
        self.strategy: 'Strategy' = None
        self.name: 'str' = name

    def get_and_remove_leaf(self) -> 'State':
        current_state = self.strategy.get_and_remove_leaf()
        if current_state.is_subgoal_state():
            plan = current_state.extract_plan()
            current_state: 'State' = plan[-1]
            if self.goal_index < self.goal_max_index:
                goals = self.all_goals[self.goal_index]
                if type(goals) != tuple:
                    goals = goals.copy()
                else:
                    goals = [goals]
                for goal in self.all_goals:
                    for g in goal:
                        letter = current_state.boxes.get(g)
                        g_ = current_state.goals.get(g)
                        if letter is not None and g_ == letter.lower()[0]:
                            goals.append(g)
                current_state.goals = self._add_goals_to_current(goals)
                self.strategy = _aux_factory(self.name,
                                             current_state,
                                             **self.strategy_attributes)
                self.strategy.add_to_frontier(current_state)
                current_state = self.strategy.get_and_remove_leaf()
                self.goal_index += 1
        self._frontier_len -= 1
        return current_state

    def is_goal_state(self, state: 'State') -> 'bool':
        if all(elem in self.current_goals for elem in self.initial_state.goals):
            return state.is_subgoal_state()
        else:
            return False

    def add_to_frontier(self, state: 'State'):
        if not self.init:
            self.init = True
            goals = self.all_goals[self.goal_index]
            for goal in self.all_goals:
                if type(goal) != list:
                    goal = [goal]
                for g_ in goal:
                    box = state.boxes.get(g_)
                    if box is not None and box[0] == state.goals.get(g_)[0]:
                        goals.append(g_)
            state = State(state)
            state.goals = self._add_goals_to_current(goals)
            if len(goals) == 1:
                self.strategy_attributes["norm"] = ''
            else:
                # aqui hay que mirar si todas las letras son iguales o no
                if not one_freq_letter(state.goals):
                    self.strategy_attributes["norm"] = 'bg'
                else:
                    if self.planner.boxes_goals_clustered(state.boxes.keys(), state.goals.keys()):
                        self.strategy_attributes["norm"] = 'bb'
                    else:
                        self.strategy_attributes["norm"] = ''
            self.strategy = _aux_factory(self.name,
                                         state,
                                         **self.strategy_attributes)
            self.goal_index += 1
        self.strategy.add_to_frontier(state)
        self._frontier_len += 1

    def _add_goals_to_current(self, goals) -> 'Dict[Tuple, str]':
        if type(goals) != list:
            goals = [goals]
        if type(next(iter(goals))) == tuple:
            for pos in goals:
                self.current_goals[pos] = self.initial_state.goals[pos]
        else:
            for goal in goals:
                self.current_goals[goal.position] = goal
        return self.current_goals.copy()

    def __repr__(self):
        if self.strategy is None:
            return 'StrategySubGoalSeparation using {}'.format(self.name)
        else:
            return 'StrategySubGoalSeparation using {}'.format(self.strategy)


SpecialCase = namedtuple("SpecialCase", ["condition", "strategy", "goal_correction"])


class SubgoalsSpecialCasesStrategy(StrategySubGoalSeparation):

    def __init__(self, name, initial_state, special_cases: 'List[SpecialCase]', **kwargs):
        super().__init__(name, initial_state, **kwargs)
        self.special_cases = special_cases or []
        # self.goal_reorganization(initial_state, **kwargs)

    def __repr__(self):
        return 'SubgoalsSpecialCasesStrategy using {}'.format(self.special_cases)

    def get_and_remove_leaf(self) -> 'State':
        current_state = self.strategy.get_and_remove_leaf()
        if current_state.is_subgoal_state():
            # TODO: It is very possible that extracting the plan level is not actually necessary
            plan = current_state.extract_plan()
            current_state: 'State' = plan[-1]

            if self.goal_index < self.goal_max_index:
                goals = self.all_goals[self.goal_index]
                current_state.goals = self._add_goals_to_current(goals)

                # Chose which strategy to run according to the conditions
                for case in self.special_cases:
                    if case.condition(current_state, **self.strategy_attributes):
                        self.all_goals, self.goal_index, self.goal_max_index = \
                            case.goal_correction(self.all_goals, self.goal_index, self.goal_max_index)
                        goals_corr = self.all_goals[self.goal_index]
                        for g in goals:
                            if g not in goals_corr:
                                current_state.goals.pop(g)
                        if not one_freq_letter(current_state.goals):
                            self.strategy_attributes["norm"] = 'bg'
                        else:
                            if self.planner.boxes_goals_clustered(current_state.boxes.keys(), current_state.goals.keys()):
                                self.strategy_attributes["norm"] = 'bb'
                            else:
                                self.strategy_attributes["norm"] = ''

                        self.strategy = _aux_factory(case.strategy, current_state, **self.strategy_attributes)
                        break
                else:
                    if not one_freq_letter(current_state.goals):
                        self.strategy_attributes["norm"] = 'bg'
                    else:
                        if self.planner.boxes_goals_clustered(current_state.boxes.keys(), current_state.goals.keys()):
                            self.strategy_attributes["norm"] = 'bb'
                        else:
                            self.strategy_attributes["norm"] = ''
                    self.strategy = _aux_factory(self.name, current_state, **self.strategy_attributes)

                self.strategy.add_to_frontier(current_state)
                self.goal_index += 1
                current_state = self.strategy.get_and_remove_leaf()
        self._frontier_len -= 1
        return current_state

    def goal_reorganization(self, state: "State", wall_map: "WallMap", planner: "Planner", **extras):
        goal_boxes = planner.choose_box_for_goal(state)
        priority_dict = {
            "de_corr": [],
            "rooms": [],
            "j_n_corr": [],
        }
        for goal_group in self.all_goals:
            for goal in goal_group:
                node = wall_map.map[goal[0]][goal[1]]
                if node.type_ == NodeType.Corridor:
                    for connection in node.connections:
                        if connection.type_ == NodeType.DeadEnd:
                            priority_dict["de_corr"].append(goal_group)
                            break
                    else:
                        priority_dict["j_n_corr"].append(goal_group)
                    break
                elif node.type_ == NodeType.DeadEnd:
                    priority_dict["de_corr"].append(goal_group)
            else:
                priority_dict["rooms"].append(goal_group)
        self.all_goals = priority_dict["de_corr"] + priority_dict["rooms"] + priority_dict["j_n_corr"]

    def add_to_frontier(self, state: 'State'):
        if not self.init:
            self.init = True
            goals = self.all_goals[self.goal_index]
            state = State(state)
            state.goals = self._add_goals_to_current(goals)

            # Chose which strategy to run according to the conditions
            for case in self.special_cases:
                if case.condition(state, **self.strategy_attributes):
                    self.all_goals, self.goal_index, self.goal_max_index = \
                        case.goal_correction(self.all_goals, self.goal_index, self.goal_max_index)
                    goals_corr = self.all_goals[self.goal_index]
                    for g in goals:
                        if g not in goals_corr:
                            state.goals.pop(g)
                    if not one_freq_letter(state.goals):
                        self.strategy_attributes["norm"] = 'bg'
                    else:
                        if self.planner.boxes_goals_clustered(state.boxes.keys(), state.goals.keys()):
                            self.strategy_attributes["norm"] = 'bb'
                        else:
                            self.strategy_attributes["norm"] = ''
                    self.strategy = _aux_factory(case.strategy, state, **self.strategy_attributes)
                    break
            else:
                if not one_freq_letter(state.goals):
                    self.strategy_attributes["norm"] = 'bg'
                else:
                    if self.planner.boxes_goals_clustered(state.boxes.keys(), state.goals.keys()):
                        self.strategy_attributes["norm"] = 'bb'
                    else:
                        self.strategy_attributes["norm"] = ''
                self.strategy = _aux_factory(self.name, state, **self.strategy_attributes)

            self.goal_index += 1
        self.strategy.add_to_frontier(state)
        self._frontier_len += 1


class RemoveFromPathStrategy(Strategy):

    DummyHeuristic = namedtuple("DummyHeuristic", ["goals_list"])

    def __init__(self, name, **kwargs):
        super().__init__()
        self.name = name
        self.planner = kwargs.get("planner")
        self.strategy = None
        self.init = False
        self.kwargs = kwargs.copy()
        self.priority_function = kwargs.get("priority_function")
        self.wall_map = kwargs.get("wall_map")
        self.goal_map = kwargs.get("goal_map")
        self.walled_boxes = {}

    def add_to_frontier(self, state: 'State'):
        if not self.init:
            path_ab, path_gb, b_pos = self._path_to_clear(state)
            self._placement_location(state, path_ab, path_gb, b_pos)
            self.kwargs["goal_map"] = GoalMap(state.goals)
            priority_function = self.kwargs["priority_function"]
            self.kwargs["priority_function"] = self.StarPriority(priority_function, b_pos)
            self.strategy = StrategySubGoalSeparation(self.name, state, **self.kwargs)
            # Reorganization of goals: solve the * first.

            asterisk_goals = [x if type(x) == list else [x] for x in self.strategy.all_goals if
                              "*" in state.goals.get(x[0])]
            normal_goals = [x for x in self.strategy.all_goals if "*" not in state.goals.get(x[0])]
            normal_goals_aux = []
            for goal in normal_goals:
                goal = goal[0]
                if state.boxes.get(goal) is not None and state.goals.get(goal)[0] == state.boxes.get(goal)[0].lower():
                    if asterisk_goals:
                        asterisk_goals[0].append(goal)
                    else:
                        asterisk_goals.append([goal])
                else:
                    normal_goals_aux.append([goal])
            self.strategy.all_goals = asterisk_goals + normal_goals_aux
            self.strategy.goal_max_index = len(self.strategy.all_goals)
            self.init = True
        self.strategy.add_to_frontier(state)

    def get_and_remove_leaf(self) -> 'State':
        current_state = self.strategy.get_and_remove_leaf()
        if current_state.is_subgoal_state():
            current_state.goals = {k: v for k, v in current_state.goals.items() if "*" not in v}
            for pos, letter in current_state.boxes.items():
                if "*" in letter:
                    current_state.boxes[pos] = letter[0]
            for b_pos, b_char in self.walled_boxes.items():
                current_state.walls[b_pos[0]][b_pos[1]] = False
                current_state.boxes[b_pos] = b_char
            self.walled_boxes = {}
        return current_state

    def in_frontier(self, state: 'State') -> 'bool':
        return self.strategy.in_frontier(state)

    def frontier_count(self) -> 'int':
        return self.strategy.frontier_count()

    def frontier_empty(self) -> 'bool':
        return self.strategy.frontier_empty()

    def __repr__(self):
        return "RemoveFromPathStrategy"

    def _path_to_clear(self, state: 'State') -> 'Iterable[Tuple[int, int]], Tuple[int, int]':
        # Path to be cleared
        temp_heur = self.DummyHeuristic(goals_list=list(state.goals.keys()))
        boxes_list = [(pos, letter.lower()) for pos, letter in state.boxes.items()]
        dist_between_boxes, chosen, dist_goals = \
            _choose_box_for_goal(temp_heur, state, boxes_list, self.planner.dist)
        path_gb = []
        path_ab = []
        g_pos = None
        for dist, goal in dist_goals:
            if dist > 0:
                g_pos = goal
                break
        box = None
        for index, (b_pos, letter) in enumerate(boxes_list):
            if chosen[index] and (state.goals.get(b_pos) is None or state.goals.get(b_pos) != letter[0].lower()):
                path_ab += self.planner.path_cells((state.agent_row, state.agent_col), b_pos)
                path_gb += self.planner.path_cells(b_pos, g_pos)
                box = b_pos
                break
        return path_ab, path_gb, box

    def _placement_location(self, state, path_ab, path_gb, b_pos):
        box_is_marked = set()
        nodes_with_unsolved_goals = set()
        for pos, letter in self.goal_map.goals_pos.items():
            if state.boxes.get(pos) is None or state.boxes.get(pos)[0].lower() != letter:
                nodes_with_unsolved_goals.add(self.wall_map.map[pos[0]][pos[1]])
        path = path_ab + path_gb
        path_goal_box = set(path_gb)
        path_set = set(path)
        path_gb_set = set(path_gb)
        for pos in path:
            if pos != b_pos:
                box = state.boxes.get(pos)
                gl = state.goals.get(pos)
                if box is not None and pos not in box_is_marked and (gl is None or box[0].lower() != gl[0]):
                    box_is_marked.add(pos)
                    first_free = 1
                    state.boxes[pos] = box + "*"
                    frontier = [pos]
                    expl_squares = set()
                    # BFS on the squares
                    empty_space = None
                    if pos in path_goal_box:
                        curr_path = path_gb_set
                    else:
                        curr_path = path_set
                    while frontier:
                        curr_frontier = []
                        for i, j in frontier:
                            node = self.wall_map.map[i][j]
                            # if node in nodes_with_unsolved_goals and node.type_ == NodeType.Corridor:
                            #     expl_squares.add((i, j))
                            # else:
                            if (i, j) not in curr_path and state.goals.get((i, j)) is None \
                                    and state.boxes.get((i, j)) is None:
                                if first_free > 0:
                                    state.goals[(i, j)] = "#"  # state.boxes.get(pos).lower()
                                    curr_frontier.append((i, j))
                                    empty_space = (i, j)
                                    first_free -= 1
                                else:
                                    state.goals[(i, j)] = "*"  # state.boxes.get(pos).lower()
                                    frontier = []  # Stop exterior loop
                                break  # Break current loop
                            else:
                                for mod_i, mod_j in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                                    try:
                                        if not state.walls[i + mod_i][j + mod_j] \
                                                and (i + mod_i, j + mod_j) not in expl_squares \
                                                and (state.boxes.get((i + mod_i, j + mod_j)) is None
                                                     or "*" in state.boxes.get((i + mod_i, j + mod_j))):
                                            curr_frontier.append((i + mod_i, j + mod_j))
                                    except IndexError:
                                        pass
                                expl_squares.add((i, j))
                            frontier = curr_frontier
                    if empty_space is not None:
                        state.goals.pop(empty_space)
        for pos, b_char in state.boxes.items():
            if "*" not in b_char and pos != b_pos and not goal_done(state, pos):
                self.walled_boxes[pos] = b_char
                state.walls[pos[0]][pos[1]] = True
        for box in self.walled_boxes.keys():
            state.boxes.pop(box)

    class StarPriority:

        def __init__(self, priority_function, ref_point):
            self.priority_function = priority_function
            self.ref_point = ref_point

        def __call__(self, wall_map: "WallMap", goal_map: "GoalMap", **extras):
            results = self.priority_function(wall_map, goal_map, **extras)
            planner: 'Planner' = extras["planner"]
            new_results = []
            for g_list in results:
                for goal in g_list:
                    new_results.append([goal])
            return sorted(new_results, key= lambda x, ref=self.ref_point, planner=planner: -planner.dist(ref,x[0]))


# SpecialCase = namedtuple("SpecialCase", ["condition", "strategy", "goal_correction"])


def factory(name, initial_state: 'State', subgoals=False, **kwargs) -> 'Strategy':
    if subgoals is not False:
        if subgoals == "spc":
            kwargs["special_cases"] = []
            kwargs["special_cases"].append(SpecialCase(condition=box_on_the_way,
                                                       strategy="rmv",
                                                       goal_correction=extract_first))
            return SubgoalsSpecialCasesStrategy(name, initial_state, **kwargs)
        else:
            return StrategySubGoalSeparation(name, initial_state, **kwargs)
    else:
        return _aux_factory(name, initial_state, **kwargs)


def _aux_factory(name, initial_state, **kwargs) -> 'Strategy':
    if name == "bfs":
        return StrategyBFS()
    elif name == "dfs":
        return StrategyDFS()
    elif name == "rmv":
        return RemoveFromPathStrategy("astar", **kwargs)
    else:
        return StrategyBestFirst(heuristic_factory(name, initial_state, **kwargs), **kwargs)
