from test.helpertest import HelperTestCase
from agent import StatespaceSearchAgent
from conflictmanager import *
class AgentTestCase(HelperTestCase):
    def testInterleavePlan(self):
        """
	Interleave a plan with noops
	"""
        [agents, searchclient] = self.initMap('levels/testcases/MAMoveBoxConflict.lvl')
        agent0 = agents[0]
        agent0.interleave_plan(units=2,start_time=-1)
        agent0_actions = [str(agent0.act()) for _ in range(0,len(agent0.solution))]
        self.assertEqual(['NoOp','NoOp','Push(N,N)','Push(N,N)','Push(N,N)'], agent0_actions)

if __name__ == '__main__':
    unittest.main()
