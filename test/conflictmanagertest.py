from test.helpertest import HelperTestCase
from agent import StatespaceSearchAgent
from conflictmanager import *
class ConflictManagerTestCase(HelperTestCase):
    def getConflictManager(self,map_):
        [agents, searchclient] = self.initMap(map_)
        conflictmanager = ConflictManager(agents)
        return conflictmanager

    def conflictInPos(self,totalconflicts, positions):
        for iteration, iterationconflict in enumerate(totalconflicts, start=0):
            if iteration in positions:
                self.assertEqual(len(iterationconflict),1,"Failed at it: "+str(iteration))
            else:
                self.assertEqual(len(iterationconflict),0,"Failed at it: "+str(iteration))


    def testAddConflict(self):
        """
        Test adding a conflict
        """
        agent1 = StatespaceSearchAgent(None)
        agent2 = StatespaceSearchAgent(None)

        conflict1 = Conflict(agent1,agent2)
        conflict2 = Conflict(agent2,agent1)
        self.assertEquals(conflict1, conflict2)

    def testMoveToSameCell(self):
        """
        Test that we cannot move to same cell
        """
        conflictmanager = self.getConflictManager('levels/testcases/MAMoveToSameCellConflict.lvl')
        totalconflicts = conflictmanager.getconflicts()
        self.conflictInPos(totalconflicts,[1])

    def testSwapCellConflict(self):
        """
        Test that a we cannot swap cells
        """
        conflictmanager = self.getConflictManager('levels/testcases/MASwapCellConflict.lvl')
        totalconflicts = conflictmanager.getconflicts()
        self.conflictInPos(totalconflicts,[0])

    def testMoveBoxConflict(self):
        """
        Move agent into same field as box
        """
        conflictmanager = self.getConflictManager('levels/testcases/MAMoveBoxConflict.lvl')
        totalconflicts = conflictmanager.getconflicts()
        self.conflictInPos(totalconflicts,[0])

    def testPushSameBoxConflict(self):
        """
        Push the same box by to agents
        """
        conflictmanager = self.getConflictManager('levels/testcases/MAPushSameBoxConflict.lvl')
        totalconflicts = conflictmanager.getconflicts()
        self.conflictInPos(totalconflicts,[1,2])

    def testSwapBoxesConflict(self):
        """
        Swap boxes
        """
        conflictmanager = self.getConflictManager('levels/testcases/MASwapBoxesConflict.lvl')
        totalconflicts = conflictmanager.getconflicts()
        self.conflictInPos(totalconflicts,[1])
        conflict = next(iter(totalconflicts[1]))
        #self.assertEqual( type(conflict).__name__, 'DeadlockConflict')

    def testBoxesPosition(self):
    	conflictmanager = self.getConflictManager('environment_levels/MAsimple3.lvl')
    	agent2 = conflictmanager.agents[1]
    	self.assertEqual(agent2.initial_state.boxes[(3,1)], 'B')
    	self.assertEqual(agent2.solution[0].boxes[(3,1)],'B')

    def testGetOccupiedInDeadLock(self):
        conflictmanager = self.getConflictManager('environment_levels/MAsimple3.lvl')
        agent2 = conflictmanager.agents[1]
        self.assertEqual(conflictmanager.get_occupied(agent2,3,1,0), 'B')

    def testResolveDeadlockPullBox(self):
        conflictmanager = self.getConflictManager('environment_levels/MAsimple3.lvl')
        totalconflicts = conflictmanager.getconflicts()
        self.conflictInPos(totalconflicts,[3,11])
        conflict = next(iter(totalconflicts[3]))
        self.assertEqual( type(conflict).__name__, 'DeadlockConflict')
        conflictmanager.solve_deadlock_conflict(conflict)
        agent1 = conflictmanager.agents[0]
        agent2 = conflictmanager.agents[1]
        agent1actions = [str(agent1.act()) for _ in range(0,len(agent1.solution))]
        agent2actions = [str(agent2.act()) for _ in range(0,len(agent2.solution))]
        self.assertEqual(['NoOp' for _ in range(0,29)] + ['Move(W)', 'Move(W)', 'Move(S)', 'Move(S)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Push(N,N)'],agent1actions)
        self.assertEqual(['Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(N)', 'Move(N)', 'Move(W)', 'Move(W)', 'Move(W)', 'Move(W)', 'Move(W)', 'Move(W)', 'Move(W)', 'Move(W)', 'Pull(E,W)', 'Pull(E,W)', 'Pull(E,W)', 'Pull(E,W)', 'Pull(E,W)', 'Pull(E,W)', 'Pull(E,W)', 'Pull(E,W)', 'Pull(S,W)', 'Pull(S,N)']+['NoOp' for _ in range(0,14)], agent2actions)

    def testResolveDeadlockPushBox(self):
        conflictmanager = self.getConflictManager('levels/testcases/MAResolveDeadlockPush.lvl')
        totalconflicts = conflictmanager.getconflicts()
        self.conflictInPos(totalconflicts,[3,11])
        conflict = next(iter(totalconflicts[3]))
        self.assertEqual( type(conflict).__name__, 'DeadlockConflict')
        conflictmanager.solve_deadlock_conflict(conflict)
        agent1 = conflictmanager.agents[0]
        agent2 = conflictmanager.agents[1]
        agent1actions = [str(agent1.act()) for _ in range(0,len(agent1.solution))]
        agent2actions = [str(agent2.act()) for _ in range(0,len(agent2.solution))]
        self.assertEqual(['NoOp' for _ in range(0,21)] + ['Move(W)', 'Move(W)', 'Move(S)', 'Move(S)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Push(N,N)'],agent1actions)
        self.assertEqual(['Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(N)', 'Move(N)', 'Move(W)', 'Move(W)', 'Move(W)', 'Move(W)', 'Move(W)', 'Move(W)', 'Move(W)', 'Move(W)', 'Push(W,W)', 'Push(W,W)']+['NoOp' for _ in range(0,14)],agent2actions)

    def testResolveMoveAgent(self):
        conflictmanager = self.getConflictManager('levels/testcases/MAResolveDeadlockMoveAgent.lvl')
        totalconflicts = conflictmanager.getconflicts()
        self.conflictInPos(totalconflicts,[3])
        conflict = next(iter(totalconflicts[3]))
        self.assertEqual( type(conflict).__name__, 'DeadlockConflict')
        self.assertEqual('agent', conflict._object) 
        conflictmanager.solve_deadlock_conflict(conflict)
        agent1 = conflictmanager.agents[0]
        agent2 = conflictmanager.agents[1]
        self.assertEqual({},agent2.initial_state.boxes)
        agent1actions = [str(agent1.act()) for _ in range(0,len(agent1.solution))]
        agent2actions = [str(agent2.act()) for _ in range(0,len(agent2.solution))]
        self.assertEqual(['NoOp' for _ in range(0,10)] + ['Move(W)', 'Move(W)', 'Move(S)', 'Move(S)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Push(N,N)'],agent1actions)
        self.assertEqual(['Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(E)', 'Move(S)']+['NoOp' for _ in range(0,14)],agent2actions)	

    def testResolveMoveAgent(self):
        conflictmanager = self.getConflictManager('levels/testcases/MASharedGoalsConflict.lvl')
        totalconflicts = conflictmanager.getconflicts()
        self.conflictInPos(totalconflicts,[4])
        conflict = next(iter(totalconflicts[4]))
        self.assertEqual( type(conflict).__name__, 'SharedGoalConflict')

if __name__ == '__main__':
    unittest.main()
