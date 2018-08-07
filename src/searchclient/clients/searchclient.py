'''
    Author: Mathias Kaas-Olsen
    Date:   2016-02-11
'''


import re
import sys

import memory

from strategy import Strategy

from state import State
from collections import defaultdict

from multiagentstate import MultiAgentState


class SearchClient:

    def __init__(self, server_messages, first_line, debug=False):
        self.debug = debug
        colors_re = re.compile(r'^[a-z]+:\s*[0-9A-Z](\s*,\s*[0-9A-Z])*\s*$')
        try:
            # Read lines for colors. There should be none of these in warmup levels.
            line = first_line
            if colors_re.fullmatch(line) is not None:
                print('Invalid level (client does not support colors).', file=sys.stderr, flush=True)
                sys.exit(1)

            # Read lines for level.
            # init_row = 70; init_col = 70
            ncols = 0  # ; nrows = 0
            initial_state = State()

            tempwalls = []
            # [[False for _ in range(init_col)] for _ in range(init_row)]
            initial_state.boxes = defaultdict(lambda: None)
            # [[None for _ in range(init_col)] for _ in range(init_row)]
            initial_state.goals = defaultdict(lambda: None)
            # [[None for _ in range(init_col)] for _ in range(init_row)]

            temp_agent_row = None
            temp_agent_col = None
            goals_list = []

            row = 0
            while line:
                ncols = max(ncols, len(line))
                for col, char in enumerate(line):
                    if char == '+':
                        tempwalls.append((row, col))
                    elif char in "0123456789":
                        if temp_agent_row is not None:
                            print('Error, encountered a second agent (client only supports one agent).',
                                  file=sys.stderr, flush=True)
                            sys.exit(1)
                        temp_agent_row = row
                        temp_agent_col = col
                    elif char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                        initial_state.boxes[(row, col)] = char
                    elif char in "abcdefghijklmnopqrstuvwxyz":
                        initial_state.goals[(row, col)] = char
                        goals_list.append((row, col))
                row += 1
                line = server_messages.readline().rstrip()

            nrows = row
            initial_state.MAX_ROW, initial_state.MAX_COL = nrows, ncols
            initial_state.goals_list = goals_list
            initial_state.agent_row, initial_state.agent_col = temp_agent_row, temp_agent_col
            initial_state.walls = [[False for _ in range(ncols)] for _ in range(nrows)]
            for (i, j) in tempwalls:
                initial_state.walls[i][j] = True

            self.initial_state = initial_state

        except Exception as ex:
            print('Error parsing level: {}.'.format(repr(ex)), file=sys.stderr, flush=True)
            if debug:
                raise ex
            sys.exit(1)

    def search(self, strategy_: 'Strategy') -> '[State, ...]':
        print('Starting search with strategy {}.'.format(strategy_), file=sys.stderr, flush=True)
        strategy_.add_to_frontier(self.initial_state)

        iterations = 0
        while True:
            if iterations == 1000:
                print(strategy_.search_status(), file=sys.stderr, flush=True)
                iterations = 0

            if memory.get_usage() > memory.max_usage:
                print('Maximum memory usage exceeded.', file=sys.stderr, flush=True)
                return None

            if strategy_.frontier_empty():
                return None

            leaf = strategy_.get_and_remove_leaf()

            if self.debug:
                print(leaf, file=sys.stderr, flush=True)

            if strategy_.is_goal_state(leaf):
                return leaf.extract_plan()

            strategy_.add_to_explored(leaf)

            for child_state in leaf.get_children():
                if not strategy_.is_explored(child_state) and not strategy_.in_frontier(child_state):
                    strategy_.add_to_frontier(child_state)

            iterations += 1


class MultiAgentSearchClient:

    def __init__(self, server_messages, first_line):
        self.global_state = None
        if server_messages == 'Manual':
            return

        colors_re = re.compile(r'^[a-z]+:\s*[0-9A-Z](\s*,\s*[0-9A-Z])*\s*$')
        try:
            # Read lines for level.
            #self.initial_state = State()  # todo: esta linea todavia no. abajo cuando ya sepa los ints
            ncols = 0
            initial_state = State()
            tempwalls = []
            initial_state.boxes = defaultdict(lambda: None)
            initial_state.goals = defaultdict(lambda: None)
            goals_list = []
            # Read lines for colors.
            line = first_line
            colors = defaultdict(lambda: None)
            agents = defaultdict(lambda: None)
            #messes things up if there are no agents :O
            while colors_re.fullmatch(line) is not None:
                color_line = line.split(':')
                color = color_line[0]
                color_obs = color_line[1].split(',')
                agent_ids = set([x.strip() for x in color_obs if x.strip().isdigit()])
                for id_ in agent_ids:
                    if not id_ in agents:
                        agents[id_] = {
                            'goals': defaultdict(lambda: None),
                            'goals_list': list(),
                            'boxes': defaultdict(lambda: None),
                            'agent_row': None,
                            'agent_col': None
                        }
                boxes = set(color_obs) - agent_ids
                for box in boxes:
                    colors[box] = color
                line = server_messages.readline().rstrip()

            row = 0
            box_assigned = False
            while line:
                ncols = max(ncols, len(line))
                for col, char in enumerate(line):
                    if char == '+':
                        tempwalls.append((row, col))
                    elif char in "0123456789":
                        agents[char]['agent_row'] = row
                        agents[char]['agent_col'] = col
                    elif char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                        initial_state.boxes[(row, col)] = char
                    elif char in "abcdefghijklmnopqrstuvwxyz":
                        initial_state.goals[(row, col)] = char
                        goals_list.append((row, col))
                row += 1
                line = server_messages.readline().rstrip()
            nrows = row
            initial_state.MAX_ROW, initial_state.MAX_COL = nrows, ncols
            initial_state.goals_list = goals_list
            initial_state.walls = [[False for _ in range(ncols)] for _ in range(nrows)]
            for (i, j) in tempwalls:
                initial_state.walls[i][j] = True
            self.agents_map = agents
            self.colors = colors
            self.global_state = MultiAgentState(copy=initial_state,agents_map=agents,colors=colors)
        except Exception as ex:
            raise ex
            print('Error parsing level: {}.'.format(repr(ex)), file=sys.stderr, flush=True)
            sys.exit(1)


