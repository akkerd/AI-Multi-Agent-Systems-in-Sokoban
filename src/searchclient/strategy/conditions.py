from preprocessing import Planner, WallMap, NodeType
from state import State
from common import goal_done


def box_on_the_way(state: 'State', planner: 'Planner', wall_map: 'WallMap', **extras):
    goal_box = planner.choose_box_for_goal(state, **extras)
    chosen_boxes = set(x for goal, ((x), letter) in goal_box)
    for goal, box in goal_box:
        if not goal_done(state, goal):
            path = planner.path_cells((state.agent_row, state.agent_col), box[0])
            path += planner.path_cells(box[0], goal)
            for pos in path:
                if pos != box[0] and pos != goal:
                    b_letter = state.boxes.get(pos)
                    if b_letter is not None:
                        if wall_map.map[pos[0]][pos[1]].type_ == NodeType.Corridor:
                            return True
                        else:
                            counter = 2
                            for i_surr, j_surr in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                                surr_pos = (pos[0] + i_surr, pos[1] + j_surr)
                                if surr_pos is not goal and state.boxes.get(surr_pos) is not None\
                                        and surr_pos not in chosen_boxes:
                                    counter -= 1
                                    if counter == 0:
                                        return True
    return False


def extract_first(all_goals, goal_index, max_goals):
    current_goals = all_goals[goal_index]
    if len(current_goals) > 1:
        first_goal = current_goals[:1]
        rest_goals = current_goals[1:]
        all_goals = all_goals[:goal_index] + [first_goal] + [rest_goals] + all_goals[goal_index+1:]
        max_goals += 1
    return all_goals, goal_index, max_goals
