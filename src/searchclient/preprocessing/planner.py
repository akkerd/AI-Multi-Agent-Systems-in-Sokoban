"""
    Partial order planner
"""
from .mapper import *
from typing import List

import numpy as np
from scipy.sparse.csgraph import floyd_warshall
from queue import PriorityQueue
from typing import Tuple
from copy import deepcopy


class Action:

    def __init__(self, name, preconditions, effects):
        self.name = name
        self.preconditions = preconditions
        self.effects = effects


class State:

    def __init__(self):
        self.variables = {}

    def __hash__(self):
        return hash(frozenset(self.variables))


class Plan:

    def __init__(self, start_effects, goal_preconditions):
        self.initial_state = Action("Start", (), start_effects)
        self.goal_state = Action("Goal", goal_preconditions, ())


class PriorityPlanner:

    def __init__(self, wall_map:'WallMap', goal_map:'GoalMap'):
        self.priorities = []
        dead_end_priorities = []
        nodes_with_goals = {}
        corridor_priorities: 'List[List[Goal]]' = []
        for node in wall_map.nodes.values():
            if node.type_ is NodeType.DeadEnd:
                d_end_square = next(iter(node.squares))
                goal = goal_map.goals_pos[d_end_square]
                if goal is not None:
                    dead_end_priorities.append(goal)
            if node.type_ is NodeType.Corridor:
                dead_end_node = None
                junction_1: 'Node' = None
                for connected_node in node.connections:
                    if connected_node.type_ is NodeType.DeadEnd:
                        dead_end_node = connected_node
                    elif connected_node.type_ is NodeType.Junction:
                        if junction_1 is None:
                            junction_1 = connected_node
                if junction_1 is not None:
                    corr_squares: 'List' = order_corridor_list(junction_1, node)
                    reversed(corr_squares)
                    if dead_end_node is not None:
                        i = 0
                        for square in corr_squares:
                            goal = goal_map.goals_pos[square]
                            if goal is not None:
                                if len(corridor_priorities) <= i:
                                    corridor_priorities.append([])
                                corridor_priorities[i].append(goal)
                                i += 1
                        if i > 0:
                            nodes_with_goals[node] = i

    def get_next(self):
        pass

    def mark_solved(self):
        pass


class Planner:

    def __init__(self):
        self.size = None
        self.nrows = None
        self.mat = None
        self.predecessors = None

    def floyd_warshall(self, walls):
        if self.mat is None:
            self.size = len(walls[0])
            self.nrows = len(walls)
            fw_size = len(walls[0]) * len(walls)
            matrix = np.full((fw_size, fw_size), fill_value=9999, dtype='int16')

            matrix[0][0] = 0
            for col in range(1, len(walls[0])):
                if not walls[0][col]:
                    matrix[self._matrix_index(0, col)][self._matrix_index(0, col)] = 0
                    if not walls[0][col - 1]:
                        matrix[self._matrix_index(0, col - 1)][self._matrix_index(0, col)] = 1
                        matrix[self._matrix_index(0, col)][self._matrix_index(0, col - 1)] = 1

            for row in range(1, len(walls)):
                matrix[self._matrix_index(row, 0)][self._matrix_index(row, 0)] = 0
                if not walls[row-1][0] and not walls[row][0]:
                    matrix[self._matrix_index(row, 0)][self._matrix_index(row - 1, 0)] = 1
                    matrix[self._matrix_index(row-1, 0)][self._matrix_index(row, 0)] = 1

                for col in range(1, len(walls[0])):
                    matrix[self._matrix_index(row, col)][self._matrix_index(row, col)] = 0
                    if not walls[row][col]:
                        if not walls[row - 1][col]:
                            matrix[self._matrix_index(row, col)][self._matrix_index(row-1, col)] = 1
                            matrix[self._matrix_index(row-1, col)][self._matrix_index(row, col)] = 1
                        if not walls[row][col-1]:
                            matrix[self._matrix_index(row, col-1)][self._matrix_index(row, col)] = 1
                            matrix[self._matrix_index(row, col)][self._matrix_index(row, col-1)] = 1
            mat, pred = floyd_warshall(matrix, False, True)
            self.mat = mat.astype(int)
            self.predecessors = pred
        return self.mat, self.predecessors

    def _matrix_index(self, row, col):
        return row * self.size + col

    def _label(self, index):
        row, col = index // self.size, index % self.size
        return row, col

    def path_cells(self, cfrom, cto):
        pred = self.predecessors
        ifrom = self._matrix_index(*cfrom)
        ito = self._matrix_index(*cto)

        path = [ito]
        previous_cell = ito
        while previous_cell != ifrom:
            previous_cell = pred[ifrom][previous_cell]
            path.append(previous_cell)
        path = [self._label(ind) for ind in path]
        path.reverse()
        return path

# Given a goal, we need to look for the closest box, and then get cells we need to "liberate" to get it.
    def closest_cell(self, cfrom, cto_list):
        """cto_list is a list of possible cells, we need to find the closest one to cfrom"""
        ifrom = self._matrix_index(*cfrom)
        ito_list = [self._matrix_index(*cell) for cell in cto_list]
        dists = [self.mat[ifrom][c] for c in ito_list]
        ito = ito_list[dists.index(min(dists))]
        return self._label(ito)

    def dist(self, pos_a, pos_b):
        return self.mat[self._matrix_index(*pos_a)][self._matrix_index(*pos_b)]

    def boxes_goals_clustered(self, boxes_pos, goals_pos):
        """ Check is boxes are close to each other, goals close to each other."""
        # Sum of distances between boxes
        dist_boxes = 0
        bnot_checked = [x for x in boxes_pos]
        box = bnot_checked.pop(0)
        while len(bnot_checked) > 0:
            newbox = self.closest_cell(box, bnot_checked)
            dist_boxes += self.dist(box, newbox)
            box = newbox
            bnot_checked.remove(box)

        # Sum of distances between goals
        dist_goals = 0
        gnot_checked = [x for x in goals_pos]
        goal = gnot_checked.pop(0)
        while len(gnot_checked) > 0:
            newgoal = self.closest_cell(goal, gnot_checked)
            dist_goals += self.dist(goal, newgoal)
            goal = newgoal
            gnot_checked.remove(goal)

        # Sum of distances box-goal
        dist_goal_box = 0
        bnot_checked = [x for x in boxes_pos]
        for goal in goals_pos:
            # goal = goals_pos[i]
            box = self.closest_cell(goal, bnot_checked)
            dist_goal_box += self.dist(goal, box)
            bnot_checked.remove(box)

        return dist_boxes + dist_goals < dist_goal_box

    def choose_box_for_goal(self, state, **extras) -> ('int', '[]', '[]'):
        boxes_list = [(pos, letter.lower()) for pos, letter in state.boxes.items()]
        chosen = [False] * len(boxes_list)
        result = []
        goals_list = [goal for goal in state.goals.keys()]
        for g_index, goal in enumerate(goals_list, 0):
            box_dist = state.MAX_ROW * state.MAX_COL
            box_index = -1
            for b_index, (pos, letter) in enumerate(boxes_list, 0):
                if (not chosen[b_index]) and (state.goals[goal] in letter):
                    norm1 = self.dist(pos, goal)
                    box_index = b_index if norm1 < box_dist else box_index
                    box_dist = min(box_dist, norm1)
            chosen[box_index] = True
            if goal != boxes_list[box_index][0]:
                result.append((goal, boxes_list[box_index]))
        return result

    def grouping_function(self, state: 'State', wall_map: 'WallMap') -> 'List[List]':
        # Order by Node
        goals_in_node = {}
        for x, y in state.goals.keys():
            node = wall_map.map[x][y]
            if goals_in_node.get(node.id) is None:
                goals_in_node[node.id] = set()
            goals_in_node[node.id].add((x, y))
            if node.type_ == NodeType.DeadEnd:
                connect = next(iter(node.connections)).id
                if connect in goals_in_node:
                    self.join_areas(connect, node.id, goals_in_node)
            elif node.type_ == NodeType.Junction:
                for connect in node.connections:
                    if connect.id in goals_in_node:
                        if connect.type_ == NodeType.Corridor:
                            self.join_areas(connect.id, node.id, goals_in_node)
            elif node.type_ == NodeType.Corridor:
                for connect in node.connections:
                    if connect in goals_in_node:
                        if connect.type_ in (NodeType.Junction, NodeType.Corridor):
                            self.join_areas(connect.id, node.id, goals_in_node)
        return [[], []]

    @staticmethod
    def join_areas(id1, id2, goals_in_node):
        new_list = goals_in_node[id1].update(goals_in_node[id2])
        goals_in_node[id1] = new_list
        goals_in_node[id2] = new_list

    class PEntry(object):
        def __init__(self, priority, data):
            self.data = data
            self.priority = priority

        def __lt__(self, other):
            return self.priority < other.priority

    class Node:
        def __init__(self, data:'Tuple', parent:'Tuple or None'):
            self.data = data
            self.parent = parent
            self._hash = None

        def __hash__(self):
            if self._hash is None:
                self._hash = hash(self.data)
                if self.parent is not None:
                    self._hash += hash(self.parent) * 31

    # def is_still_reachable(self, state, pos1: Tuple, pos2: Tuple, blocks_to_block):
    #     walls = deepcopy(state.walls)
    #     boxes = state.boxes.copy()
    #     for x, y in blocks_to_block:
    #         walls[x][y] = True
    #         boxes.pop(x,y)
    #     frontier = PriorityQueue()
    #     frontier_set = set()
    #     explored = set()
    #
    #     leaf = self.Node(pos1, None)
    #     frontier.put(self.PEntry(self.dist(leaf.data, pos2), leaf))
    #     frontier_set.add(leaf)
    #     explored.add(leaf)
    #
    #     surrounding = [(x, y) for x in range(-1, 2) for y in range(-1, 2) if x != y and x * y == 0]
    #
    #     while frontier:
    #         leaf = frontier.get().data
    #         if leaf.data == pos2:
    #             break
    #         else:
    #             for x, y in surrounding:
    #                 child = self.Node((x + leaf.data[0], y + leaf.data[1]), leaf)
    #                 if child not in frontier_set \
    #                         and child not in explored \
    #                         and not walls[child.data[0]][child.data[1]]:
    #                     if boxes[]
    #                     frontier.put(self.PEntry(self.dist(child.data, pos2), child))
    #                     frontier_set.add(child)
    #             explored.add(leaf)
    #     if leaf.data == pos2:
    #         solution = [leaf.data]
    #         while leaf.parent is not None:
    #             parent = leaf.parent
