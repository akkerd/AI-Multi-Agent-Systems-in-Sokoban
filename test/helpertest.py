import unittest
from clients.searchclient import MultiAgentSearchClient
from agent import StatespaceSearchAgent
from clients.main import is_multi_agent
class HelperTestCase(unittest.TestCase):
    def setUp(self):
        unittest.TestCase.setUp(self)

    def tearDown(self):
        unittest.TestCase.tearDown(self)

    def initMap(self,map_):
        #TODO: remove from here and extract method in multiagentclient to do this
        with open(map_,'r') as file:
            is_multi, first_line = is_multi_agent(file)
            if is_multi_agent:
                searchclient = MultiAgentSearchClient(file,first_line)
                agents = []
                agent_init_states = searchclient.global_state.split_state()
                for agent_id in sorted(agent_init_states):
                    initial_state = agent_init_states[agent_id].initial_state
                    agent = StatespaceSearchAgent(agent_id)
                    agent.set_search_strategy(strategy_str='bfs')
                    agent.search(initial_state)
                    agents.append(agent)
                return [agents,searchclient]
            else:
                raise NotImplementedError()

