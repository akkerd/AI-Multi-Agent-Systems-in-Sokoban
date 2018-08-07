from abc import ABCMeta, abstractmethod
import sys
import memory
from functools import reduce
from strategy import *
from collections import deque
from state import State
from action import ActionType, Action
from strategy import factory as strategy_factory
from action import ActionType
from heuristic.h_funct import h_multiagent_generator
class Agent(metaclass=ABCMeta):
   
    @abstractmethod
    def act(self) -> 'Action': raise NotImplementedError

class StatespaceSearchAgent(Agent):
    def __init__(self,id='0'):
        super().__init__()
        self.id = id
        self.solution = [] 
   
    def __repr__(self):
        return 'State space search agent'

    # TODO: The goal test should probably be part of the strategy. However don't want to make it incompatible.
    # with SA.
    def search(self, initial_state, goal_test_str='standard'):
        self.initial_state = initial_state
        strategy = strategy_factory(name=self.strategy_str, initial_state=initial_state,
                                    weight_value=5, heuristic_function=self.heuristic_function)
        self.strategy = strategy

        if goal_test_str == "dl_conflict_solved":
            def goal_test(state):
                for pos, goal in state.boxes.items():
                    goal = state.goals.get(pos)
                    box = state.boxes.get(pos)
                    if box is not None and (goal is None or goal != box.lower()):
                        return False
                agent_goal = state.goals.get((state.agent_row,state.agent_col))
                #print(agent_goal)
                if agent_goal is None: # or agent_goal not in "abcdefghijklmnopqrstuvwxyz":  or agent_goal is 'agent':
                    return False

                return True

        else:
            def goal_test(state):
                return state.is_subgoal_state()

        print('Starting search with strategy {}.'.format(strategy), file=sys.stderr, flush=True)
        strategy.add_to_frontier(initial_state)
        self.solution = None
        iterations = 0
        while True:
            if iterations == 1000:
                print(strategy.search_status(), file=sys.stderr, flush=True)
                iterations = 0

            if memory.get_usage() > memory.max_usage:
                print('Maximum memory usage exceeded.', file=sys.stderr, flush=True)
                self.solution = []
                return None

            if strategy.frontier_empty():
                self.solution = []
                return None

            leaf = strategy.get_and_remove_leaf()
            if goal_test(leaf):
                self.solution = deque(leaf.extract_plan())
                return

            strategy.add_to_explored(leaf)
            for child_state in leaf.get_children():
                if not strategy.is_explored(child_state) and not strategy.in_frontier(child_state):
                    strategy.add_to_frontier(child_state)

            iterations += 1

    def act(self):
        if not len(self.solution):
            #TODO: move to action
            return Action(action_type=ActionType.NoOp, agent_dir=None, box_dir=None)
        else:
           state = self.solution.popleft()
           return state.action


    def interleave_plan(self, units, start_time=-1):
        """
        :param start_time: insert noops after index given by start_time
        """
        #TODO: this is a bit overcomplicated since we only need the action
        start_state = self.solution[start_time]
        noop_states = [State(start_state) for _ in range(0, units)]
        def fix_copies(prev, new):
            new.t = prev
            new.action = Action(action_type = ActionType.NoOp,agent_dir=None, box_dir=None)
        reduce(fix_copies,noop_states,start_state)
        if len(self.solution) > start_time + 1:
            self.solution[start_time+1].parent = noop_states[-1]
        noop_states.reverse()
        for state in noop_states:
            self.solution.insert(start_time+1,state)

    def get_future_state(self,time):
        """"
        Returns the state according to plan a number of time steps from current state. If time bigger than solution length returns final state.
        """
        state = None
        if not self.solution:
            state = self.initial_state
        elif len(self.solution) > time:
            state = self.solution[time]
        else:
            state = self.solution[len(self.solution)-1]
        return state
    
    def set_search_strategy(self,strategy_str="bfs", heuristic_function=None):
        self.strategy_str = strategy_str
        self.heuristic_function = heuristic_function

    def replan(self, agent_last_state=None):
        if agent_last_state is not None:
            for row in  range(0, len(agent_last_state.goals)):
                for col in row:
                    x = 1
