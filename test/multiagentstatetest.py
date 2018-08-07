from test.helpertest import HelperTestCase
from multiagentstate import MultiAgentState
from conflictmanager import *
class MultiAgentStateTestCase(HelperTestCase):
    def testGetChild(self):
        """
	Test get child using a joint_action
	"""
        [agents, searchclient] = self.initMap('levels/MASimple.lvl')
        mastate = MultiAgentState(copy = searchclient.global_state, agents_map=searchclient.agents_map)
        joint_action1 = [(agent.id, agent.act()) for agent in agents]
        child1 = mastate.get_child(joint_action1)
        joint_action2 = [(agent.id, agent.act()) for agent in agents]
        child2 = child1.get_child(joint_action2)

        self.assertEqual((5,2), mastate.get_agent_pos('1'))
        self.assertEqual('A',mastate.boxes[(4,2)])
        self.assertEqual((4,2), child1.get_agent_pos('1'))
        self.assertEqual('A',child1.boxes[(3,2)])
        self.assertEqual(None,child1.boxes[(4,2)])
        self.assertEqual((3,2), child2.get_agent_pos('1'))
        self.assertEqual('A',child2.boxes[(2,2)])
        self.assertEqual(None,child2.boxes[(3,2)])

        self.assertEqual((8,2), mastate.get_agent_pos('0'))
        self.assertEqual('B',mastate.boxes[(9,2)])
        self.assertEqual((9,2), child1.get_agent_pos('0'))
        self.assertEqual('B',child1.boxes[(10,2)])
        self.assertEqual(None,child1.boxes[(9,2)])
        self.assertEqual((10,2), child2.get_agent_pos('0'))
        self.assertEqual('B',child2.boxes[(11,2)])
        self.assertEqual(None,child2.boxes[(10,2)])




if __name__ == '__main__':
    unittest.main()
