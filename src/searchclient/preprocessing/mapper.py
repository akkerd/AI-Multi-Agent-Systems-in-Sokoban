"""
    Pre-processing module.
        Class Mapper
"""
from typing import List, Dict, Tuple, Set, Iterable
from state import State
from heuristic.h_funct import _choose_box_for_goal

"Default value for the Goal to assign priority."
_DEFAULT_GOAL_REWARD = 6


class NodeType:
    """
        Class to define the different types of node that we have.
    """
    DeadEnd = Corridor = Junction = Room = None

    def __init__(self, name: 'str', prefix: 'str'):
        self.name = name
        self.prefix = prefix

    def __repr__(self):
        return self.name


NodeType.DeadEnd = NodeType("Dead End", "d_")
NodeType.Corridor = NodeType("Corridor", "c_")
NodeType.Junction = NodeType("Junction", "j_")
NodeType.Room = NodeType("Room", "r_")


class Node:
    """
        Node with the info of the connections, the areas and such
        information can be added as needed.
    """
    node_num: int = 0

    def __init__(self, node_type: "NodeType"):
        Node.node_num += 1
        self.type_: "NodeType" = node_type
        self.squares: "Set[Tuple[int, int]]" = set()
        self.id: "str" = self.type_.prefix + str(Node.node_num)
        self.connections: "Set[Node]" = set()

    def add_squares(self, square: Tuple[int, int]):
        self.squares.add(square)

    def add_connection(self, node: "Node"):
        self.connections.add(node)

    def __repr__(self):
        connection_list = [x.id for x in self.connections]
        return "Class:" + repr(self.__class__) \
            + " Type:" + repr(self.type_) \
            + " Id:" + repr(self.id) \
            + " Squares:" + repr(self.squares) \
            + " Connections:" + repr(connection_list)


# class Goal:
#
#     def __init__(self, position: "Tuple[int, int]", letter: "str", value: "int"=_DEFAULT_GOAL_REWARD):
#         self.position = position
#         self.letter = letter
#         self.value = value
#
#     def __repr__(self):
#         return str(self.position) + " '" + self.letter + "' " + str(self.value)
#
#     def __eq__(self, other):
#         if type(other) == tuple:
#             return  other == self.position
#         elif type(other) == str:
#             return other == self.letter
#         elif type(other) == Goal:
#             return other.position == self.position \
#                     and other.letter == self.letter
#         else:
#             return False
#
#     def __ne__(self, other):
#         return not self.__eq__(other)
#
#
class IncoherentRoomException(Exception):
    message = "Found an incoherent room."

    def __init__(self, wall_sections: "int"=None, n_accessors: "int"=None, position: "Iterable[Tuple[int,int]]"=None):
        super(Exception, self).__init__()
        self.wall_sections = wall_sections
        self.n_accessors = n_accessors
        self.position = position

    def __repr__(self):
        result = IncoherentRoomException.message
        if self.wall_sections is not None:
            result += " wall_sections: " + str(self.wall_sections)
        if self.n_accessors is not None:
            result += " n_accessors:" + str(self.n_accessors)
        if self.position is not None:
            result += " position:" + str(self.position)
        return result


class WallMap:
    """
        This class takes the True-False map of walls and detects:
        - Corridors : Squares with only 2 exits
        - Junctions : Squares with more than 2 exits and more tan 2 wall sections
        - Dead Ends : Squares with only 1 wall section and 1 exit
        - Rooms : The rest
    """

    surrounding_squares = ((-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1))

    def __init__(self, wall_map: "List[List[bool]]"):
        """
            Receives the wall map in matrix (List of Lists of Boolean) form and
            parses it into Dead Ends, Corridors, Rooms and Junctions.
        """
        self._area_number = 1
        self.height: int = len(wall_map)
        self.width: int = len(wall_map[0])
        self.nodes: Dict[str, Node] = {}  # Format node.id, node
        self.map: List[List[Node]] = [[None for _ in range(self.width)] for _ in range(self.height)]
        for i in range(1, self.height - 1):
            for j in range(1, self.width - 1):
                self._find_nodes(wall_map, i, j)

    def _find_nodes(self, wall_map, i, j):
        if wall_map[i][j]:
            return
        count_sections = 0
        n_accesses = 0
        found = []
        same_section = False

        for (i_neighbour, j_neighbour) in WallMap.surrounding_squares:
            if wall_map[i + i_neighbour][j + j_neighbour]:
                if not same_section:
                    same_section = True
                    count_sections += 1
            else:
                same_section = False
            if i_neighbour == 0 or j_neighbour == 0:
                if not wall_map[i + i_neighbour][j + j_neighbour]:
                    n_accesses += 1
                if self.map[i + i_neighbour][j + j_neighbour] is not None:
                    node = self.map[i + i_neighbour][j + j_neighbour]
                    found.append(node)

        if count_sections > 1 and wall_map[i + 0][j - 1] and wall_map[i - 1][j - 1]:
            count_sections -= 1

        for (i_neighbour, j_neighbour) in [a for a in WallMap.surrounding_squares if a[0]*a[1] != 0]:
            if count_sections <= 1:
                break
            elif not wall_map[i + i_neighbour][j + j_neighbour] \
                    and wall_map[i + i_neighbour][j] \
                    and wall_map[i][j + j_neighbour]:
                count_sections -= 1

        if n_accesses > 0:
            if n_accesses == 1:
                node = self._add_new_node(NodeType.DeadEnd)
            else:
                if count_sections > 1:
                    if n_accesses == 2:
                        node, found = self._add_new_area(found, NodeType.Corridor)
                    else:
                        node = self._add_new_node(NodeType.Junction)
                else:
                    node, found = self._add_new_area(found, NodeType.Room)

            for connected_node in found:
                node.add_connection(connected_node)
                connected_node.add_connection(node)

            node.add_squares((i, j))
            self.map[i][j] = node

    def _add_new_node(self, node_type):
        node = Node(node_type)
        self.nodes[node.id] = node
        return node

    def _add_new_area(self, found, node_type):
        found_of_type = []
        found_connections = []

        for node in found:
            if node.type_ is node_type:
                found_of_type.append(node)
            else:
                found_connections.append(node)

        if not found_of_type:
            node = self._add_new_node(node_type)
        else:
            node = found_of_type[0]
            rest_of_nodes = found_of_type[1:]
            for n in rest_of_nodes:
                if node is not n and node.type_ is node_type:
                    for square in n.squares:
                        self.map[square[0]][square[1]] = node
                        node.add_squares(square)
                    for connect in n.connections:
                        connect.connections.discard(n)
                        connect.add_connection(node)
                        node.add_connection(connect)
                    del self.nodes[n.id]
        return node, found_connections

    def trim_map(self, boxes, agent_pos: 'List[Tuple[int, int]] or Tuple[int, int]') -> List[Tuple[int, int]]:
        """
            Removes the map nodes that don't connect to any of the agents and returns
            the locations of the boxes that can't be accessed.
            :param boxes: Dict of boxes.
            :param agent_pos: List of the position of the agents.
            :return: A list of the boxes that cannot be accessed, and therefore should be removed.
        """
        if type(agent_pos) != list:
            agent_pos = [agent_pos]
        connected_nodes = set()

        for pos in agent_pos:
            node: 'Node' = self.map[pos[0]][pos[1]]
            connected_nodes.add(node)
            nodes_to_explore = [node]

            while nodes_to_explore:
                nodes_to_explore_aux = []
                for node in nodes_to_explore:
                    for connection in node.connections:
                        if connection not in connected_nodes:
                            nodes_to_explore_aux.append(connection)
                            connected_nodes.add(connection)
                nodes_to_explore = nodes_to_explore_aux
        new_nodes = {}
        # unnaccessible_boxes = []
        for k, v in self.nodes.items():
            if v in connected_nodes:
                new_nodes[k] = v
            else:
                for square in v.squares:
                    self.map[square[0]][square[1]] = None
                    boxes.pop(square, None)
                    # if boxes.get(square):
                        # unnaccessible_boxes.append(square)
        for box_i, box_j in list(boxes.keys()):
            if self.map[box_i][box_j] is None:
                boxes.pop((box_i, box_j))
        self.nodes = new_nodes
        # return unnaccessible_boxes

    def str_nodes(self) -> str:
        result = ""
        for name, node in self.nodes.items():
            result += (repr(name) + " -> " + repr(node) + "\n")
        return result

    def str_map(self) -> str:
        """
            Prints in stdout the generated area map.
        """
        result = ""
        for row in self.map:
            for col in row:
                text = "0"
                if col is not None:
                    text = col.id
                result += "{0:5s}\t".format(text)
            result += "\n"
        return result

    def generate_graphviz(self, filename: 'str', comment: 'str') -> None:
        """
            Generates a pdf file using graphviz for visualization
            purposes
        """
        from graphviz import Graph
        dot = Graph(comment=comment, strict=True)
        for key, node in self.nodes.items():
            dot.node(str(node.id), str(node.id))
            for connected_node in node.connections:
                dot.edge(str(node.id), str(connected_node.id))
        dot.render(filename)


class GoalMap:

    def __init__(self, goal_map: "Dict[Tuple[int, int], str]" = None):
        self.goals_pos: "Dict[Tuple[int, int], str]" = {}
        self.goals_ch: "Dict[str, List[Tuple[int, int]]]" = {}
        for (i, j), letter in goal_map.items():
            self._add_goal(letter, i, j)

    def _add_goal(self, letter, row, col):
        pos = (row, col)
        self.goals_pos[pos] = letter
        g_list = self.goals_ch.get(letter)
        if g_list is None:
            g_list = []
            self.goals_ch[letter] = g_list
        g_list.append(pos)

    def str_goals(self) -> str:
        """
            Print the goal values of the map in a map
        """
        result = ""
        for character, g_list in self.goals_ch:
            result += character + " -> "
            for goal in g_list:
                result += goal
            result += "\n"
        return result


def calculate_goal_reward(goal_map: "GoalMap", wall_map: "WallMap", base_reward: int = _DEFAULT_GOAL_REWARD):
    for node in wall_map.nodes.values():
        if node.type_ is NodeType.Corridor:
            dead_end_node = None
            junction_1: "Node" = None
            for connected_node in node.connections:
                if connected_node.type_ is NodeType.DeadEnd:
                    dead_end_node = connected_node
                elif connected_node.type_ is NodeType.Junction:
                    if junction_1 is None:
                        junction_1 = connected_node
            if junction_1 is not None:
                node.squares = order_corridor_list(junction_1, node)
            else:
                raise IncoherentRoomException(position=node.squares)
            if dead_end_node is not None:
                pos = next(iter(junction_1.squares))
                if goal_map.goals_pos[pos] is not None:
                    goal = goal_map.goals_pos[pos]
                    if goal is not None:
                        goal.value = base_reward - 1
                reward = base_reward
                for square in node.squares:
                    goal = goal_map.goals_pos[square]
                    if goal is not None:
                        goal.value = reward
                        reward += 1
                d_end_square = next(iter(dead_end_node.squares))
                goal = goal_map.goals_pos[d_end_square]
                if goal is not None:
                    goal.value = reward


def order_corridor_list(from_node: "Node", node: "Node"):
    square_list = list(node.squares)
    for square in square_list:
        (square_from,) = from_node.squares
        if abs(square_from[0] - square[0]) + abs(square_from[1] - square[1]) == 1:
            first_square = square
            break
    else:
        raise IncoherentRoomException(position=node.squares)
    square_list.remove(first_square)
    result_list = [first_square]
    current_square = first_square
    while square_list:  # This could probably be better achieved with a dict.
        for square in square_list:
            if (abs(square[0] - current_square[0]) + abs(square[1] - current_square[1])) == 1:
                result_list.append(square)
                square_list.remove(square)
                current_square = square
                break
    return result_list


def goals_sets(wall_map: "WallMap", goal_map: "GoalMap", **extras):

    state = extras.get("state")
    planner: "Planner" = extras.get("planner")
    goals_nodes = [wall_map.map[pos[0]][pos[1]] for pos in goal_map.goals_pos.keys()]
    if one_freq_letter(goal_map):
        # We will not use subplanner if there is only 1 type of letter in the level or one very frequent
        return [list(goal_map.goals_pos.keys())]

    c_to_be_ordered = {}

    for node in goals_nodes:
        # Linking deadend with its corridor
        if node.type_ is NodeType.DeadEnd:
            node.id = list(node.connections)[0].id
        elif node.type_ is NodeType.Junction:
            # Linking junction with a corridor if it is linked to only one corridor
            listconec = list(node.connections)
            if (listconec[0].type_ is NodeType.Corridor) and (listconec[1].type_ is not NodeType.Corridor):
                node.id = listconec[0].id
            elif (listconec[1].type_ is NodeType.Corridor) and (listconec[0].type_ is not NodeType.Corridor):
                node.id = listconec[1].id
        elif node.type_ is NodeType.Corridor:
            for conn in node.connections:
                if conn.type_ is NodeType.DeadEnd:
                    c_to_be_ordered[node.id] = (conn, node)
                    break

    goals_ids = [node.id for node in goals_nodes]
    goals_ids_dict = dict(zip(goal_map.goals_pos.keys(), goals_ids))
    goals_sets = {}
    for key, value in sorted(goals_ids_dict.items()):
        goals_sets.setdefault(value, []).append(key)

    final_goals_sets = {
            "de_corr": [],
            "rooms": [],
            "j_n_corr": [],
    }
    asoc_dict = dict(planner.choose_box_for_goal(**extras))
    dict_exits = {}

    for keyid, xx in sorted(goals_sets.items()):
        if keyid in c_to_be_ordered.keys():
            val = c_to_be_ordered[keyid]
            squares = order_corridor_list(*val)
            if goal_map.goals_pos.get(next(iter(val[0].squares))) is not None:
                newvals = [list(val[0].squares)]  # should be only 1 element, because it will be a deadend or junction
            else:
                newvals = []
            newvals.extend([[s] for s in squares if s in xx])
            if len(newvals) != len(xx):
                raise IncoherentRoomException(position=squares)
            goals_sets[keyid] = newvals
            final_goals_sets["de_corr"].extend(newvals)
        else:
            if planner is not None and state is not None:
                for goal in xx:
                    node = wall_map.map[goal[0]][goal[1]]
                    if node.type_ == NodeType.Corridor:
                        path = set(planner.path_cells(goal, asoc_dict[goal][0]))
                        for conn in node.connections:
                            junct_square = next(iter(conn.squares))
                            if junct_square in path:
                                registry = dict_exits.get(node.id)
                                if registry is None:
                                    registry = {}
                                    dict_exits[node.id] = registry
                                inner_reg = registry.get(junct_square)
                                if inner_reg is None:
                                    inner_reg = []
                                    registry[junct_square] = inner_reg
                                inner_reg.append(goal)
                                break
                        else:
                            registry = dict_exits.get(node.id)
                            if registry is None:
                                registry = {}
                                dict_exits[node.id] = registry
                            inner_reg = registry.get("None")
                            if inner_reg is None:
                                inner_reg = []
                                registry["None"] = inner_reg
                            inner_reg.append(goal)
                        break
                else:
                    final_goals_sets["rooms"].append(xx)

    for node_id, exits in dict_exits.items():
        exit_keys = exits.keys()
        if "None" in exit_keys:
            pass
        elif len(exit_keys) == 1:
            pos = next(iter(exit_keys))
            squares = order_corridor_list(wall_map.map[pos[0]][pos[1]], wall_map.nodes[node_id])
            newvals = []
            for square in squares:
                goal = goal_map.goals_pos.get(square)
                if goal is not None:
                    newvals.append([square])
            final_goals_sets["j_n_corr"].extend(newvals)
    # # This thing should not be used because it is not working as expected.
    # if maxfreq >= 0.7:
    #     goals_chs = {}
    #     for key, value in sorted(goal_map.goals_ch.items()):
    #         for v in value:
    #             goals_chs[v] = key
    #     max_ch = [k for k in goals_ch_freq if goals_ch_freq[k] == maxfreq][0]
    #     # We will merge all the subsets that contains the same letter if it is really common in the level
    #     sets_to_merge = []
    #     inds_to_delete = []
    #     for i,s in enumerate(final_goals_sets):
    #         chs = [goals_chs[p] for p in s]
    #         if (len(set(chs)) == 1) and (chs[0] == max_ch):
    #             sets_to_merge.extend(s)
    #             inds_to_delete.append(i)
    #     final_goals_sets =[final_goals_sets[i] for i in range(len(final_goals_sets)) if i not in inds_to_delete]
    #     final_goals_sets.append(sets_to_merge)

    final_goals_sets["j_n_corr"].reverse()
    return final_goals_sets["de_corr"] + final_goals_sets["rooms"] + final_goals_sets["j_n_corr"]
    # when we order by id, we get first corridors then junctions then rooms (c_, j_, r_)


def one_freq_letter(goals: 'Dict[Tuple[int, int], str] or GoalMap', **extras):
    goals_ch_freq = {}
    ch_sets = {}
    if type(goals) == GoalMap:
        goals = goals.goals_pos
    for key, value in sorted(goals.items()):
        ch_sets.setdefault(value, []).append(key)
    for k, v in ch_sets.items():
        goals_ch_freq[k] = len(v) / len(goals)
    maxfreq = max(goals_ch_freq.values())

    return maxfreq >= 0.7


