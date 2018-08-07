'''
    Author: Mathias Kaas-Olsen
    Date:   2016-02-11
'''


import argparse
import re
import sys

import memory

from collections import defaultdict

from state import State
from strategy import Strategy, factory as strategy_factory
from preprocessing.mapper import WallMap, GoalMap


class SearchClient:

    def __init__(self, server_messages, debug=False):
        self.initial_state = None
        if server_messages == 'Manual':
            return
        self.debug = debug
        colors_re = re.compile(r'^[a-z]+:\s*[0-9A-Z](\s*,\s*[0-9A-Z])*\s*$')
        try:
            # Read lines for colors. There should be none of these in warmup levels.
            line = server_messages.readline().rstrip()
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
            # self.initial_state = State(size=(nrows, ncols))
            # self.initial_state.agent_row = temp_agent_row
            # self.initial_state.agent_col = temp_agent_col
            # self.initial_state.walls = [row[:ncols] for row in tempwalls[:nrows]]
            # self.initial_state.boxes = [row[:ncols] for row in tempboxes[:nrows]]
            # self.initial_state.goals = [row[:ncols] for row in tempgoals[:nrows]]
            # self.initial_state.goals_list = goals_list
            # self.initial_state.goalletter = goalletter

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
            # if leaf.is_goal_state(): todo
            #     return leaf.extract_plan()
            if strategy_.is_goal_state(leaf):
                return leaf.extract_plan()

            strategy_.add_to_explored(leaf)
            for child_state in leaf.get_children():
                if not strategy_.is_explored(child_state) and not strategy_.in_frontier(child_state):
                    strategy_.add_to_frontier(child_state)

            iterations += 1

    def interleaved_search(self, strategy_: 'Strategy') -> '[State, ...]':
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

            # if leaf.is_goal_state(): todo
            #     return leaf.extract_plan()
            if strategy_.is_goal_state(leaf):
                return strategy_.extract_plan(leaf)

            strategy_.add_to_explored(leaf)
            for child_state in leaf.get_children():
                if not strategy_.is_explored(child_state) and not strategy_.in_frontier(child_state):
                    strategy_.add_to_frontier(child_state)

            iterations += 1


def main(strategy_name, subgoal_separ, debug):
    # Read server messages from stdin.
    server_messages = sys.stdin

    # Use stderr to print to console through server.
    print('SearchClient initializing. I am sending this using the error output stream.', file=sys.stderr, flush=True)

    # Read level and create the initial state of the problem.
    client = SearchClient(server_messages, debug)

    # client.preprocessing()
    #print(client.initial_state.goals_priorities, file=sys.stderr, flush=True)
    #print(client.initial_state.score, file=sys.stderr, flush=True)

    initial_state = client.initial_state
    w_map = WallMap(initial_state.walls)
    w_map.trim_map(initial_state.boxes, (initial_state.agent_row, initial_state.agent_col))
    g_map = GoalMap(initial_state.goals)
    strategy_ = strategy_factory(name=strategy_name,
                                 subgoals=subgoal_separ,
                                 wall_map = w_map,
                                 goal_map = g_map,
                                 initial_state=initial_state,
                                 weight_value=5)

    # ---------------------------------------------------------
    # complete_goals_list = deepcopy(client.initial_state.goals_list)
    # first_part = [i[1] for i in enumerate(complete_goals_list) if i[0] in (2, 3, 5)]
    #
    # tempstate = client.initial_state
    # tempstate.goals_list = first_part
    # strategy = StrategyBestFirst(AStar(tempstate))
    solution = client.search(strategy_)
    print('length solution:'+str(len(solution)), file=sys.stderr, flush=True)
    # tempstate = solution[-1]
    # tempstate.parent = None
    # tempstate.goals_list = complete_goals_list
    # strategy = StrategyBestFirst(AStar(tempstate))
    # client.initial_state = tempstate
    # solution.extend(client.search(strategy))
    # print('length solution:' + str(len(solution)), file=sys.stderr, flush=True)
    # ---------------------------------------------------------
    # todo: the idea here is achieve to do the search function a couple of times and concatenate the states

    if solution is None:
        print(strategy_.search_status(), file=sys.stderr, flush=True)
        print('Unable to solve level.', file=sys.stderr, flush=True)
        sys.exit(0)
    else:
        print('\nSummary for {}.'.format(strategy_), file=sys.stderr, flush=True)
        print('Found solution of length {}.'.format(len(solution)), file=sys.stderr, flush=True)
        print('{}.'.format(strategy_.search_status()), file=sys.stderr, flush=True)

        for state in solution:
            print("[" + str(state.action) + "]", file=sys.stderr, flush=True)
            response = server_messages.readline().rstrip()
            if response == 'false':
                print('Server responsed with "{}" to the action "{}" applied in:\n{}\n'.format(response, state.action, state), file=sys.stderr, flush=True)
                break


if __name__ == '__main__':
    # Program arguments.
    parser = argparse.ArgumentParser(description='Simple client based on state-space graph search.')
    parser.add_argument('--max_memory', metavar='<MB>', type=float, default=2048.0,
                        help='The maximum memory usage allowed in MB (soft limit, default 512).')
    parser.add_argument('-s', '--strategy', type=str, default='BFS',
                        help='The strategy to use for the algorithm (default BFS)')
    parser.add_argument('-g', '--subgoals', action='store_true',
                        help="Whether to use sub-goal separation or not.")
    parser.add_argument('-d', '--debug', action='store_true',
                        help="If the flag is not present, the exceptions will be caught by the client, if it"
                             "is present, they will be shown in the terminal.")
    args = parser.parse_args()

    # Set max memory usage allowed (soft limit).
    memory.max_usage = args.max_memory

    # Set strategy
    strategy = args.strategy

    # Run client.
    main(strategy_name=args.strategy, subgoal_separ=args.subgoals, debug=args.debug)

