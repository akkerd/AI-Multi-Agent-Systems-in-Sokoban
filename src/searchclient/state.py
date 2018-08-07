'''
    Author: Mathias Kaas-Olsen
    Date:   2016-02-11
'''


import random
# import sys
from action import ALL_ACTIONS, ActionType
from typing import Tuple


class State:
    _RANDOM = random.Random(2)
    # MAX_ROW = 70
    # MAX_COL = 70

    def __init__(self, copy: 'State' = None, size=None, copy_walls: 'bool' = False):
        '''
        If copy is None: Creates an empty State.
        If copy is not None: Creates a copy of the copy state.

        The lists walls, boxes, and goals are indexed from top-left of the level, row-major order (row, col).
               Col 1  Col 2  Col 3  Col 4
        Row 0: (0,0)  (0,1)  (0,2)  (0,3)  ...
        Row 1: (1,0)  (1,1)  (1,2)  (1,3)  ...
        Row 2: (2,0)  (2,1)  (2,2)  (2,3)  ...
        ...

        For example, self.walls is a list of size [MAX_ROW][MAX_COL] and
        self.walls[2][7] is True if there is a wall at row 3, column 8 in this state.

        Note: The state should be considered immutable after it has been hashed, e.g. added to a dictionary!
        '''
        self._hash = None

        if copy is None:
            if size is not None:
                self.MAX_ROW, self.MAX_COL = size
            else:
                self.MAX_ROW, self.MAX_COL = 70, 70

            self.agent_row = None
            self.agent_col = None

            self.walls = None  # [[False for _ in range(self.MAX_COL)] for _ in range(self.MAX_ROW)]
            self.boxes = None  # [[None for _ in range(self.MAX_COL)] for _ in range(self.MAX_ROW)]
            self.goals = None  # [[None for _ in range(self.MAX_COL)] for _ in range(self.MAX_ROW)]
            # self.goals_list = None

            self.parent = None
            self.action = None

            self.g = 0
        else:
            self.agent_row = copy.agent_row
            self.agent_col = copy.agent_col
            self.MAX_ROW, self.MAX_COL = copy.MAX_ROW, copy.MAX_COL
            if copy_walls:
                self.walls = [row[:] for row in copy.walls]
            else:
                self.walls = copy.walls  # [row[:] for row in copy.walls]
            self.boxes = copy.boxes.copy()
            self.goals = copy.goals  # [row[:] for row in copy.goals]
            # self.goals_list = copy.goals_list

            self.parent = copy.parent
            self.action = copy.action

            self.g = copy.g

    def get_child(self, action):
        # Determine if action is applicable.
        child = None
        if action.action_type is ActionType.NoOp:
            child = State(self)
            child.agent_row = self.agent_row
            child.agent_col = self.agent_col
            child.parent = self
            child.action = action
            child.g += 1
        else:
            new_agent_row = self.agent_row + action.agent_dir.d_row
            new_agent_col = self.agent_col + action.agent_dir.d_col
            if action.action_type is ActionType.Move:
                if self.is_free(new_agent_row, new_agent_col):
                    child = State(self)
                    child.agent_row = new_agent_row
                    child.agent_col = new_agent_col
                    child.parent = self
                    child.action = action
                    child.g += 1
            elif action.action_type is ActionType.Push:
                if self.box_at(new_agent_row, new_agent_col):
                    new_box_row = new_agent_row + action.box_dir.d_row
                    new_box_col = new_agent_col + action.box_dir.d_col
                    if self.is_free(new_box_row, new_box_col):
                        child = State(self)
                        child.agent_row = new_agent_row
                        child.agent_col = new_agent_col
                        child.boxes[(new_box_row, new_box_col)] = child.boxes.pop((new_agent_row, new_agent_col))
                        # child.boxes[new_box_row][new_box_col] = self.boxes[new_agent_row][new_agent_col]
                        # child.boxes[new_agent_row][new_agent_col] = None
                        child.parent = self
                        child.action = action
                        child.g += 1

            elif action.action_type is ActionType.Pull:
                if self.is_free(new_agent_row, new_agent_col):
                    box_row = self.agent_row + action.box_dir.d_row
                    box_col = self.agent_col + action.box_dir.d_col
                    if self.box_at(box_row, box_col):
                        child = State(self)
                        child.agent_row = new_agent_row
                        child.agent_col = new_agent_col
                        child.boxes[(self.agent_row, self.agent_col)] = child.boxes.pop((box_row, box_col))
                        # child.boxes[self.agent_row][self.agent_col] = self.boxes[box_row][box_col]
                        # child.boxes[box_row][box_col] = None
                        child.parent = self
                        child.action = action
                        child.g += 1
        return child

    def get_children(self) -> '[State, ...]':
        """
        Returns a list of child states attained from applying every applicable action in the current state.
        The order of the actions is random.
        """
        children = []
        for action in ALL_ACTIONS:
            child = self.get_child(action)
            if child:
                children.append(child)
        State._RANDOM.shuffle(children)
        return children

    def is_initial_state(self) -> 'bool':
        return self.parent is None

    def is_goal_state(self) -> 'bool':  # TODO This is old and probably wont work, fix.
        for row in range(self.MAX_ROW):
            for col in range(self.MAX_COL):
                goal = self.goals[row][col]
                box = self.boxes[row][col]
                if goal is not None and (box is None or goal not in box.lower()):
                    return False
        return True

    def is_subgoal_state(self) -> 'bool':
        for pos in self.goals:
            goal = self.goals.get(pos)
            box = self.boxes.get(pos)
            if goal is not None and (box is None or goal not in box.lower()):
                return False
        return True

    def is_free(self, row: 'int', col: 'int') -> 'bool':
        return not self.walls[row][col] and self.boxes.get((row, col)) is None

    def box_at(self, row: 'int', col: 'int') -> 'bool':
        return self.boxes.get((row, col)) is not None

    def extract_plan(self) -> '[State, ...]':
        plan = []
        state = self
        while not state.is_initial_state():
            plan.append(state)
            state = state.parent
        plan.reverse()
        return plan

    def goal_done(self, pos: Tuple[int, int]) -> 'bool':
        goal = self.goals.get(pos)
        box = self.boxes.get(pos)
        if goal is not None \
                and box is not None \
                and goal[0] == box[0].lower():
            return True
        else:
            return False

    def __hash__(self):
        if self._hash is None:
            prime = 31
            _hash = 1
            _hash = _hash * prime + self.agent_row
            _hash = _hash * prime + self.agent_col
            # _hash = _hash * prime + hash(self.action or 0)
            # _hash = _hash * prime + self.action
            _hash = _hash * prime + hash(frozenset(self.boxes.items()))
            # hash(tuple(tuple(row) for row in self.boxes))
            _hash = _hash * prime + hash(frozenset(self.goals.items()))
            #  hash(tuple(tuple(row) for row in self.goals))
            _hash = _hash * prime + hash(tuple(tuple(row) for row in self.walls))
            self._hash = _hash
        return self._hash

    def __eq__(self, other):
        if self is other: return True
        if not isinstance(other, State): return False
        if self.agent_row != other.agent_row: return False
        if self.agent_col != other.agent_col: return False
        if self.boxes != other.boxes: return False
        if self.goals != other.goals: return False
        if self.walls != other.walls: return False
        return True

    def __repr__(self):
        lines = []
        for row in range(self.MAX_ROW):
            line = []
            for col in range(self.MAX_COL):
                if self.boxes.get((row, col)) is not None: line.append(self.boxes.get((row, col))[0])
                elif self.goals.get((row, col)) is not None: line.append(self.goals.get((row, col)))
                elif self.walls[row][col]: line.append('+')
                elif self.agent_row == row and self.agent_col == col: line.append('0')
                else: line.append(' ')
            lines.append(''.join(line))
        return '\n'.join(lines)
