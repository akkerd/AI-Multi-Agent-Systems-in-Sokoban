"""
    Module containing the heuristic functions, separated for ease of organization.
"""
from common import manhattan_distance
from conflictmanager import ConflictManager, DeadlockConflict, NoOpableConflict
from common import goal_done


def h_no_reward(self: 'Heuristic', state: 'State', dist_function) -> 'int':
    boxes_list = [(pos, letter.lower()) for pos, letter in state.boxes.items()]
    dist_agent = _box_agent_distances(self, state, boxes_list, dist_function)

    dist_between_boxes, chosen, dist_goals = _choose_box_for_goal(self, state, boxes_list, dist_function)

    # Now we compute the minimum distance from the agent to the closest box that was chosen to move to a goal
    min_dist_agent = min_agent(self, state, chosen, dist_agent)

    # Sum of all distances computed (agent + dist_between_boxes + distance_goals_to_boxes)
    dist = sum([goal_dist[0] for goal_dist in dist_goals])
    if dist == 0:
        return dist  # in the goal, h(n) should be zero. The distance to the agent does not matter
    else:
        return dist + dist_between_boxes + min_dist_agent - 1
        # we substract one becaue the agent is always going to be at least distance 1 to a box


def h_no_reward_no_bcluster(self: 'Heuristic', state: 'State', dist_function) -> 'int':
    boxes_list = [(pos, letter.lower()) for pos, letter in state.boxes.items()]
    dist_agent = _box_agent_distances(self, state, boxes_list, dist_function)

    dist_between_boxes, chosen, dist_goals = _choose_box_for_goal(self, state, boxes_list, dist_function)

    # Now we compute the minimum distance from the agent to the closest box that was chosen to move to a goal
    min_dist_agent = min_agent(self, state, chosen, dist_agent)

    # Sum of all distances computed (agent + dist_between_boxes + distance_goals_to_boxes)
    dist = sum([goal_dist[0] for goal_dist in dist_goals])
    if dist == 0:
        return dist  # in the goal, h(n) should be zero. The distance to the agent does not matter
    else:
        return dist + min_dist_agent - 1
        # we substract one becaue the agent is always going to be at least distance 1 to a box


def h_constant_reward(self: 'Heuristic', state: 'State', dist_function, norm='') -> 'int':

    boxes_list = [(pos, letter.lower()) for pos, letter in state.boxes.items()]
    dist_agent = _box_agent_distances(self, state, boxes_list, dist_function)

    scores = [self.score_reward for i in range(len(self.goals_list))]

    dist_between_boxes, chosen, dist_goals = _choose_box_for_goal(self, state, boxes_list, dist_function, norm)

    min_dist_agent = min_agent(self, state, chosen, dist_agent)

    # Sum of all distances computed (agent + dist_between_boxes + distance_goals_to_boxes)
    dist = sum([goal_dist[0] for goal_dist in dist_goals])
    if dist == 0:
        return dist  # in the goal, h(n) should be zero. The distance to the agent does not matter
    else:
        achieved_goals = sum([scores[i] for i in range(len(dist_goals)) if dist_goals[i][0] == 0])
        return dist + dist_between_boxes + min_dist_agent - 1 + sum(scores) - achieved_goals
        # we substract one becaue the agent is always going to be at least distance 1 to a box


def h_priority_reward(self: 'Heuristic', state: 'State', dist_function) -> 'int':

    boxes_list = [(pos, letter.lower()) for pos, letter in state.boxes.items()]
    dist_agent = _box_agent_distances(self, state, boxes_list, dist_function)

    # scores = [6 for i in range(len(self.goals_list))]

    dist_between_boxes, chosen, dist_goals = _choose_box_for_goal(self, state, boxes_list, dist_function)

    min_dist_agent = min_agent(self, state, chosen, dist_agent)

    # Sum of all distances computed (agent + dist_between_boxes + distance_goals_to_boxes)
    dist = sum([goal_dist[0] for goal_dist in dist_goals])
    if dist == 0:
        return dist  # in the goal, h(n) should be zero. The distance to the agent does not matter
    else:
        achieved_goals = sum([goal_dist[1].value for goal_dist in dist_goals if goal_dist[0] == 0])
        return dist + dist_between_boxes + min_dist_agent - 1 - achieved_goals
        # we substract one becaue the agent is always going to be at least distance 1 to a box


def _box_agent_distances(self, state, boxes_list, dist_function):
    dist_agent = []
    for pos, letter in boxes_list:
        g = state.goals.get(pos)
        if g is None or g != letter:
            norm1a = dist_function(pos, (state.agent_row, state.agent_col))
            dist_agent.append(norm1a)
        else:
            dist_agent.append(-1)
    return dist_agent


def _choose_box_for_goal(self, state, boxes_list, dist_function, norm='') -> ('int', '[]', '[]'):
    dist_goals = [state.MAX_COL * state.MAX_ROW] * len(self.goals_list)
    chosen = [None] * len(boxes_list)
    box_previous = (-1, -1)
    dist_between_boxes = 0
    for g_index, goal in enumerate(self.goals_list, 0):
        box_dist = state.MAX_ROW * state.MAX_COL
        box_index = -1
        for b_index, (pos, letter) in enumerate(boxes_list, 0):
            if (not chosen[b_index]) and (state.goals[goal] in letter):  # and (not goal_done(state, goal)):
                norm1 = dist_function(pos, goal)
                box_index = b_index if norm1 < box_dist else box_index
                box_dist = min(box_dist, norm1)
        chosen[box_index] = True
        dist_goals[g_index] = (box_dist, goal)
        box_actual = boxes_list[box_index][0]
        if g_index > 0:
            goal_previous = self.goals_list[g_index-1]
            if norm == 'bb':
                norm1b = dist_function(box_actual, box_previous)
            elif norm == 'bg':
                norm1b = dist_function(box_actual, goal_previous)
            else:
                norm1b = 0
            # todo: choosing one of the 3 norm1b changes a lot depending on the level
        else:
            norm1b = 0
        dist_between_boxes += norm1b
        box_previous = box_actual
    return dist_between_boxes, chosen, dist_goals


def min_agent(self, state, chosen, dist_agent) -> 'int':
    # Now we compute the minimum distance from the agent to the closest box that was chosen to move to a goal
    min_dist_agent = state.MAX_ROW * state.MAX_COL
    for k in range(len(chosen)):
        if chosen[k] and (dist_agent[k] > 0):
            min_dist_agent = min(min_dist_agent, dist_agent[k])
    return min_dist_agent


def h_multiagent_generator(agent,agents):
    def h_multiagent(self:'Heuristic', state: 'State', dist_function=None) -> 'int':
        h_val = 0
        time = state.g
        conflicts = ConflictManager.get_conflicts_at_time(time,state, agent, agents)
        for conflict in conflicts:
            #TODO: find meaningfull values
            if conflict is DeadlockConflict:
                h_val += 20
            elif conflict is NoOpableConflict:
                h_val += 100
            else:
                h_val += 10
        return h_val
    return h_multiagent
