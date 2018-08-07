'''
    Author: Mathias Kaas-Olsen
    Date:   2016-02-11
'''


import argparse
import re
import sys
import copy
import memory
from agent import StatespaceSearchAgent
from state import State
from conflictmanager import ConflictManager
from collections import defaultdict
from strategy import StrategyBFS, StrategyDFS, StrategyBestFirst
from heuristic.heuristic import AStar, WAStar, Greedy
from heuristic.h_funct import h_multiagent_generator
from multiagentstate import MultiAgentState


class MultiAgentSearchClient:
    def __init__(self, server_messages):
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
            initial_state.goals =  defaultdict(lambda: None)
            goals_list = []
            # Read lines for colors.
            line = server_messages.readline().rstrip()
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
                    colors[box] = agent_ids
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

def main(strategy_str):
    # Read server messages from stdin.
    server_messages = sys.stdin

    # Use stderr to print to console through server.
    print('MultiAgentSearchClient initializing. I am sending this using the error output stream.', file=sys.stderr, flush=True)

    # Read level and create the initial state of the problem.
    client = MultiAgentSearchClient(server_messages);

    #Add a strategy for each agent
    agents = []
    solution_length = 0
    agent_init_states = client.global_state.split_state()

    for agent_id in sorted(client.agents_map.keys()):
        agent = StatespaceSearchAgent(id=agent_id)
        agents.append(agent)
        agent.initial_state = agent_init_states[agent.id]['initial_state']
    for agent in agents:
        agent.set_search_strategy(strategy_str=strategy_str,heuristic_function=h_multiagent_generator(agent,agents))

    
    # Find and resolve Conflicts with the ConflictManager
    conflict_manager = ConflictManager(agents)

    while True:
        joint_action = []
        joint_action_ids = []
        agent_init_states = None
        for agent in agents:
            # note: plan/replan
            if not agent.solution or len(agent.solution) is 0:
                # note: lazy instatiate
                if not agent_init_states: 
                    agent_init_states = client.global_state.split_state()
                initial_state = agent_init_states[agent.id]['initial_state']
                agent.search(initial_state)
                # TODO: this is very inefficient. Consider when to do better
                conflict_manager.solve_conflicts( conflict_manager.getconflicts() )
        if max(agents, key = lambda agent: len(agent.solution)) is 0:
            print(agent.strategy.search_status(), file=sys.stderr, flush=True)
            print('Unable to solve level.', file=sys.stderr, flush=True)
            sys.exit(0)
            
        for agent in agents:
            action = agent.act()
            joint_action.append(str(action))
            joint_action_ids.append((agent.id, action))
        action_str = '['+','.join(joint_action) +']'
        print(action_str, flush=True)
        response = server_messages.readline().rstrip()
        if response == 'false':
            # TODO state does not exist.
            print('Server responsed with "{}" to the action "{}" applied in:\n{}\n'.format(response, state.action, state), file=sys.stderr, flush=True)
            break

        client.global_state = client.global_state.get_child(joint_action_ids)
        solution_length = solution_length + 1
        if client.global_state.is_subgoal_state():
            print('\nSummary for {}.'.format(strategy), file=sys.stderr, flush=True)
            print('Found solution of length {}.'.format(solution_length), file=sys.stderr, flush=True)
            print('{}.'.format(agent.strategy.search_status()), file=sys.stderr, flush=True)
            return


if __name__ == '__main__':
    # Program arguments.
    parser = argparse.ArgumentParser(description='Simple client based on state-space graph search.')
    parser.add_argument('--max_memory', metavar='<MB>', type=float, default=512.0, help='The maximum memory usage allowed in MB (soft limit, default 512).')
    parser.add_argument('-s','--strategy', type=str, default='BFS', help='The strategy to use for the algorithm (default BFS)')
    args = parser.parse_args()

    # Set max memory usage allowed (soft limit).
    memory.max_usage = args.max_memory

    # Set searchclient
    strategy = args.strategy

    # Run client.
    main(strategy)
