'''
    Author: Mathias Kaas-Olsen
    Date:   2016-02-11
'''


class Dir:
    N = S = E = W = None
    
    def __init__(self, name: 'str', d_row: 'int', d_col: 'int'):
        '''
        For internal use; do not instantiate.
        Use Dir.N, Dir.S, Dir.E, and Dir.W instead.
        '''
        self.name = name
        self.d_row = d_row
        self.d_col = d_col
    
    def __repr__(self):
        return self.name


Dir.N = Dir('N', -1,  0)
Dir.S = Dir('S',  1,  0)
Dir.E = Dir('E',  0,  1)
Dir.W = Dir('W',  0, -1)


class ActionType:
    Move = Push = Pull = None
    
    def __init__(self, name: 'str'):
        '''
        For internal use; do not instantiate.
        Use ActionType.Move, ActionType.Push, and ActionType.Pull instead.
        '''
        self.name = name
    
    def __repr__(self):
        return self.name


ActionType.Move = ActionType('Move')
ActionType.Push = ActionType('Push')
ActionType.Pull = ActionType('Pull')
ActionType.NoOp = ActionType('NoOp')


class Action:
    def __init__(self, action_type: 'ActionType', agent_dir: 'Dir', box_dir: 'Dir'):
        '''
        For internal use; do not instantiate.
        Iterate over ALL_ACTIONS instead.
        '''
        self._hash = None
        self.action_type = action_type
        self.agent_dir = agent_dir
        self.box_dir = box_dir
        if box_dir is not None:
            self._repr = '{}({},{})'.format(action_type, agent_dir, box_dir)
        elif agent_dir is not None:
            self._repr = '{}({})'.format(action_type, agent_dir)
        else:
            self._repr = str(action_type)

    def __repr__(self):
        return self._repr

    def __hash__(self):
        if self._hash is None:
            self._hash = hash(self._repr)
        return  self._hash



# Grounded actions.
ALL_ACTIONS = []
for agent_dir in (Dir.N, Dir.S, Dir.E, Dir.W):
    ALL_ACTIONS.append(Action(ActionType.Move, agent_dir, None))
    for box_dir in (Dir.N, Dir.S, Dir.E, Dir.W):
        if agent_dir.d_row + box_dir.d_row != 0 or agent_dir.d_col + box_dir.d_col != 0:
            # If not opposite directions.
            ALL_ACTIONS.append(Action(ActionType.Push, agent_dir, box_dir))
        if agent_dir is not box_dir:
            # If not same directions.
            ALL_ACTIONS.append(Action(ActionType.Pull, agent_dir, box_dir))

