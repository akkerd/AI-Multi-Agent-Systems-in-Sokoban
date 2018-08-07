from action import ActionType, Dir
from state import State
import sys
class Conflict:
    """
    Contains information about the conflict.
    """
    #note: here we can add stuff like time. We can also
    #extend the class to deal with different types of conflicts.
    #TODO: probably we need to have another uniqunness test than this.
    def __init__(self, agent1 :'Agent',agent2 : 'Agent'):
        self.agent1 = agent1
        self.agent2 = agent2

    def __eq__(self,other):
        if self.agent1 == other.agent1 and self.agent2 == other.agent2 or\
            self.agent2 == other.agent1 and self.agent1 == other.agent2:
            return True
        else:
            return False

    def __hash__(self):
        h = sorted([hash(self.agent1),hash(self.agent2)])
        return hash(tuple(h))

class NoOpableConflict(Conflict):
    """
    Simple conflict class that is possible to solve by inserting a number of noops into agent1.
    """
    def __init__(self,agent1 : 'Agent' , agent2 : 'Agent', conflict_times):
        super().__init__(agent1, agent2)
        self.conflict_times = conflict_times

class DeadlockConflict(Conflict):
    """
    Conflict in which one agent is blocked by a box or agent and needs help
    """
    def __init__(self,agent1 : 'Agent' , agent2 : 'Agent', conflict_times, objectPos : '(int,int)',_object: 'string'):
       super().__init__(agent1, agent2)
       self.conflict_times = conflict_times
       self.objectPos = objectPos
       self._object = _object
       
class ConflictManager:
    """
    Class for finding conflicts in solutions to relaxed problems.
    The class should also start the replaning by generating
    new initial states for the agents and let them replan.
    """
    def __init__(self, agents: 'list(Agent)'):
        self.agents = agents #note: only this is used right now
    def _agent_same_cell(self,state1,state2):
        #TODO: deprecate this method, use get_occupied
        return (state1.agent_row == state2.agent_row and\
                state1.agent_col == state2.agent_col)
    @staticmethod
    def get_occupied(agent,row,col,time):
        """
        Extension of the state.is_free method that returns the agents belive of what is
        in the given cell at the given time
        :return: returns None if nothing is found, the box char or 'agent' in case of an agent.
        """
        #We assume that there are no walls.
        #TODO: We could extend agent to have the number and return that
        state = agent.get_future_state(time)

        return state.boxes.get((row,col)) if state.boxes.get((row,col)) else 'agent' if row == state.agent_row and col == state.agent_col else None

    def getconflicts(self):
        """
        Gets a list of conlficts. The lists is indexed by the time the
        conflicts happen.
        """
        #movingagents = [agent for agent in self.agents if agent.solution ]
        movingagents = self.agents
        #if len(movingagents) is 0:
        #    return []
        maxsolutionlength = max([len(agent.solution) for agent in movingagents if agent.solution is not None])
        #maxsolutionlength = max([len(agent.solution) for agent in self.agents])
        #Maybe it doesn't make sense for all conflicts to
        #store them sorted in time...
        totalconflicts = [set() for _ in range(0,maxsolutionlength)] 
        #TODO: Add typed conflicts
        for agent1 in movingagents:
            for time, _ in enumerate(agent1.solution, start=0):
                state1 = agent1.solution[time]
                totalconflicts[time].update(ConflictManager.get_conflicts_at_time(time,state1,agent1,movingagents))
                #totalconflicts[time] = ConflictManager.get_conflicts_at_time(time,agent1,self.agents)

        return totalconflicts

    #note: static since it is used in heurstic also
    @staticmethod
    def get_conflicts_at_time(time,state1,agent1,movingagents):
        '''
        Find all conflicts conflicting with agent1s plan at a specific time 
        '''
        conflicts = set()
        for agent2 in movingagents:
            if agent1 is not agent2:
                state2 = agent2.get_future_state(time)
                action = state1.action

                # Determine if action is applicable.
                #actictiope is ActionType.Move:
                #TODO: refactor so that free is maybee using the same
                #check that we cannot move into an occupied field.
                #TODO: this could definitely be made prettier.
                # extract methods
                #should we solve conflits as we find them
                row1 = state1.agent_row
                col1 = state1.agent_col

                row2 = state2.agent_row
                col2 = state2.agent_col

                occupied2 = ConflictManager.get_occupied(agent2,row1,col1,time)
                if occupied2:
                        # Check to see if stepping one time step will free the cell
                        occupied2next = ConflictManager.get_occupied(agent2,row1,col1,time+1)
                        if not occupied2next:
                                conflicts.add(NoOpableConflict(agent1,agent2,[time]))
                        #in case of a box check one step further ahead.
                        occupied2nextnext = ConflictManager.get_occupied(agent2,row1,col1,time+2)
                        if not occupied2nextnext:
                                conflicts.add(NoOpableConflict(agent1,agent2, [time,time+1]))
                        else:
                                #for now think of it as a deadlock conflict and call for help.
                                conflicts.add(DeadlockConflict(agent1, agent2, [time], (row1, col1), occupied2))

                # Check that agents don't swap places
                if ConflictManager.get_occupied(agent2, row1, col1, time + 1 ) == 'agent' and \
                        ConflictManager.get_occupied(agent1, row2, col2, time + 1) == 'agent':
                            # add NoOpableConflict conflict.
                            conflicts.add(NoOpableConflict(agent1, agent2, [time]))

                if action and action.action_type is ActionType.Push:
                        new_box_row = state1.agent_row + action.box_dir.d_row
                        new_box_col = state1.agent_col + action.box_dir.d_col
                        if not state2.is_free(new_box_row, new_box_col) or\
                                new_box_row == state2.agent_row and new_box_col == \
                                state2.agent_col:
                                conflicts.add(NoOpableConflict(agent1, agent2, [time]))
        return conflicts 

    def solve_conflicts(self, all_conflicts):  # TO DO: SOLVE THE CONFLICTS IN ORDER
        for conflicts_set_for_time in all_conflicts:
            for conflict in conflicts_set_for_time:
                conflictType = type(conflict)
                if conflictType is DeadlockConflict:
                    self.solve_deadlock_conflict(conflict)
                elif conflictType is NoOpableConflict:
                    self.solve_noopable_conflict(conflict)


    def solve_deadlock_conflict(self, conflict):
            agent1 = conflict.agent1
            agent2 = conflict.agent2
            agent1InitialState = agent1.initial_state
            #note: copy_walls such that we don't destroy previous walls
            agent2InitialState = State(agent2.initial_state,copy_walls=True)
            boxpos = conflict.objectPos
            _object = conflict._object
            #boxchar =  conflict.agent2.initial_state.boxes.get(boxpos)
            agent2InitialState.goals = {}
            agent2InitialState.boxes = {} if _object is 'agent' else {boxpos: _object}
            agent2InitialState.goals_list = []
            agent1_path = [(state.agent_row, state.agent_col) for state in agent1.solution]
            for row in range(0,agent2InitialState.MAX_ROW):
                for col in range(0,agent2InitialState.MAX_COL):
                    if not agent2InitialState.walls[row][col] and \
                            not agent1InitialState.boxes.get((row, col)) and \
                            (row,col) not in agent1_path:
                                agent2InitialState.goals[(row, col)] = _object.lower()
                                agent2InitialState.goals_list.append((row, col))
                    else:
                            if ConflictManager.get_occupied(conflict.agent1,row,col,0): #TODO: this controls where agent1 is standing still
                                agent2InitialState.walls[row][col] = True 
            #TODO: this could improved for now we inserts noops until agent2 has moved completly, also.
            agent2.search(agent2InitialState,goal_test_str='dl_conflict_solved')
            if len(agent2.solution) is not 0:
                agent1_orig_plan_length = len(agent1.solution)
                agent1.interleave_plan(units=len(agent2.solution),start_time=-1)
                agent2.interleave_plan(units=agent1_orig_plan_length,start_time=len(agent2.solution)-1)
                box_in_position = self.get_box_position(agent2.solution)
            else:
                # TODO: In this case, ask another agent to solve the level?
                # TODO: Or maybe is just trying to solve an unreachable goal
                print('Agent could not find solution', file=sys.stderr, flush=True)

    def solve_noopable_conflict(self, conflict):
        agent1 = conflict.agent1
        agent2 = conflict.agent2
        agent2.interleave_plan(units=len(agent1.solution), start_time=0)

    def get_direction_in_coords(self, agent_dir):
        return {
            Dir.N: [1, 0],
            Dir.E: [0, 1],
            Dir.S: [-1, 0],
            Dir.W: [0, -1],
        }[agent_dir]
    def get_box_position(self, agent_solution):
        sol_length = len(agent_solution)
        box_in_position = None
        if agent_solution[sol_length-1].action.action_type is ActionType.Pull:
            box_in_position = [agent_solution[sol_length-2].agent_row, agent_solution[sol_length-1].agent_col]
        elif agent_solution[sol_length-1].action.action_type is ActionType.Push:
            direction = self.get_direction_in_coords(agent_solution[sol_length-1].action.agent_dir)
            box_in_position = [agent_solution[sol_length-1].agent_row + direction[0],\
                               agent_solution[sol_length-1].agent_col + direction[1]]
        return box_in_position 
