from state import State
from collections import defaultdict
import copy


class MultiAgentState(State):

    def __init__(self, copy: 'State' = None, size=None, copy_walls: 'bool' = False,agents_map = None,colors=None):
        super().__init__(copy, size, copy_walls)
        self.agents_map = agents_map
        self.colors = colors

    def get_child(self, joint_action):
        '''
        Hack'ish implementation of a multi-agent state, that uses the sa implementation. We do not check for conflicts.
        '''
        child = State(copy=self)
        new_agents_map = copy.deepcopy(self.agents_map)
        #TODO: we could add some cleaning such that we don't keep the parent, or set it more properly
        for agent_id, action in joint_action:
            agent = new_agents_map[agent_id]
            child.agent_row = agent['agent_row']
            child.agent_col = agent['agent_col']
            child = child.get_child(action)
            agent['agent_row'] = child.agent_row
            agent['agent_col'] = child.agent_col
        return MultiAgentState(copy=child, agents_map=new_agents_map,colors=self.colors)

    def get_agent_pos(self,agent_id):
        agent = self.agents_map[agent_id]
        return agent['agent_row'], agent['agent_col']

    def split_state(self,copy_walls=False):
        agents = copy.deepcopy(self.agents_map)
        for _, agent in agents.items():
            state = State()
            state.goals = defaultdict(lambda: None)
            state.boxes = defaultdict(lambda: None)
            state.agent_row = agent['agent_row']
            state.agent_col = agent['agent_col']
            state.goals_list = []
            state.MAX_ROW = self.MAX_ROW
            state.MAX_COL = self.MAX_COL

            if copy_walls:
                state.walls =  [row[:] for row in self.walls]
            else:
                state.walls = self.walls  # [row[:] for row in copy.walls]
            agent['initial_state'] = state
        for (row, col), char in self.goals.items():
            for agent_id in self.colors[char.upper()]:
                agent = agents[agent_id]
                agent['initial_state'].goals[(row, col)] = char
                agent['initial_state'].goals_list.append((row, col))
        for (row,col), char in self.boxes.items():
            for agent_id in self.colors[char.upper()]:
                agent = agents[agent_id]
                agent['initial_state'].boxes[(row, col)] = char
        return agents
