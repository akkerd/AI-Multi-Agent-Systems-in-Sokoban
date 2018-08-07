import unittest

#from os import path
import subprocess
import shlex, re


class SolveLevelTestCase(unittest.TestCase):
    """
    Application tests for solving levels. 
    """
    # TODO: we could add options if we want to.
    # TODO: fix in the case where no solution is found
    def callServer(self,level='SAD1.lvl', strategy='bfs', ma=False):

        if ma:
            client = 'main.py'
        else:
            client = 'searchclient.py'
        #args = str(r'java -jar server.jar -l ' + path.join('levels',''+level) + ' -c "python '+path.join('src','searchclient',client)+ ' -s '+strategy+'"')
        args = str(r'java -jar server.jar -l ' + level
                   + ' -c "python src/searchclient -s ' + strategy + '"')
        print(''.join(args))
        argsarr = shlex.split(args)
        solution = {}
        with subprocess.Popen(argsarr, stderr=subprocess.PIPE) as proc:
           while True:
                line = str(proc.stderr.readline())
                solutionfoundregex = re.match("^.*Found solution of length (?P<length>\d+)\..*$",line)
                failregex = re.match(".*(Exception|Error).*",line)
                if solutionfoundregex:
                    solution['length'] = int(solutionfoundregex.group('length'))
                    line = str(proc.stderr.readline())
                    statisticsregex = re.match('^.*#Explored:\s*(?P<explored>\d+).*#Frontier:\s*(?P<frontier>\d+).*Time:\s*(?P<time>\d+\.?\d*)\s*s,.*Alloc:\s*(?P<alloc>\d+\.?\d*)\s*MB,\s*MaxAlloc:\s*(?P<maxalloc>\d+\.?\d*)\s*MB.*\..*$',line)  
                    if statisticsregex:
                        solution['explored'] = int(statisticsregex.group('explored'))
                        solution['frontier'] = int(statisticsregex.group('frontier'))
                        solution['time'] = float(statisticsregex.group('time'))
                        solution['alloc'] = float(statisticsregex.group('alloc'))
                        solution['maxalloc'] = float(statisticsregex.group('maxalloc'))
                        proc.stderr.close()
                        proc.kill()
                        #return [agent1.act() for _ in range(0,len(agent1.solution))]
                        return solution
                elif failregex:
                    proc.stderr.close()
                    proc.kill()
                    raise Exception('Error found')

    def setUp(self):
        unittest.TestCase.setUp(self)

    def tearDown(self):
        unittest.TestCase.tearDown(self)


class SolveSALevelTestCase(SolveLevelTestCase):
    def testSolveSAD1(self):
        solution = self.callServer(level='./levels/SAD1.lvl', strategy='bfs')
        self.assertEqual(solution['length'], 19)

    def testSolveSAsoko3_24(self):
        solution = self.callServer(level='./levels/SAsoko3_24.lvl', strategy='greedy')
        self.assertEqual(solution['length'], 440)

    def testSolveSAsimple2(self):
        solution = self.callServer(level='./levels/SAsimple2.lvl', strategy='dfs')
        self.assertEqual(solution['length'], 516)


class SolveMALevelTestCase(SolveLevelTestCase):
    def testSolveMASimple(self):
        solution = self.callServer(level='./levels/MASimple.lvl', ma=True)
        self.assertEqual(3,solution['length'])

    def testSolveMASharedGoals(self):
        """ Gives solution length 5 because each red agent is solving 
            goals that are already solved by the other red agent """
        solution = self.callServer(level='./levels/testcases/MASharedGoals.lvl', ma=True)
        self.assertEqual(1,solution['length']) 

    def testMAPushSameBoxConflict(self):
        solution = self.callServer(level='./levels/testcases/MAPushSameBoxConflict.lvl', ma=True)
        self.assertEqual(2,solution['length']) 

    def testMAMoveToSameCellConflict(self):
        solution = self.callServer(level='./levels/testcases/MAMoveToSameCellConflict.lvl', ma=True)
        self.assertEqual(15,solution['length']) 

    def testMASwapBoxesConflict(self):
        solution = self.callServer(level='./levels/testcases/MASwapBoxesConflict.lvl', ma=True)

    def testMASwapCellConflict(self):
        solution = self.callServer(level='./levels/testcases/MASwapCellConflict.lvl', ma=True)

    def testMAMoveBoxConflict(self):
        solution = self.callServer(level='./levels/testcases/MAMoveBoxConflict.lvl', ma=True)
        self.assertEqual(2,solution['length']) 

    def testMAResolveDeadlockPush(self):
        solution = self.callServer(level='./levels/testcases/MAResolveDeadlockPush.lvl', ma=True)

    def testMAFixGoalThenResolveDeadlock(self):
        solution = self.callServer(level='./levels/testcases/MAFixGoalThenResolveDeadlock.lvl', ma=True)
        self.assertEqual(17, solution['length'])

    def testMAResolveDeadlockMoveAgent(self):
        solution = self.callServer(level='./levels/testcases/MAResolveDeadlockMoveAgent.lvl', ma=True)

    def testMASimple1(self):
        solution = self.callServer(level='environment_levels/MAsimple1.lvl', ma=True)

    def testMASimple2(self):
        solution = self.callServer(level='environment_levels/MAsimple2.lvl', ma=True)

    def testMASimple3(self):
        solution = self.callServer(level='environment_levels/MAsimple3.lvl', ma=True)

    def testMASimple4(self):
        solution = self.callServer(level='environment_levels/MAsimple4.lvl', ma=True)

    def testMASimple5(self):
        solution = self.callServer(level='environment_levels/MAsimple5.lvl', ma=True)

    def testSolveMASharedGoalsConflict(self):
        solution = self.callServer(level='levels/testcases/MASharedGoalsConflict.lvl', ma=True)
        self.assertEqual(5, solution['length'])


if __name__ == '__main__':
    unittest.main()

