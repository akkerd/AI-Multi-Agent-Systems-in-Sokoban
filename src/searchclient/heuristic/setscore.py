
def set_score(heuristic, state: 'State', dist_function) -> 'int':
    boxes_list = [(pos, letter.lower()) for pos, letter in state.boxes.items()]
    max_box_dist = state.MAX_COL * state.MAX_ROW
    dist_goals = [state.MAX_COL * state.MAX_ROW] * len(heuristic.goals_list)
    chosen = [None] * len(boxes_list)
    box_previous = (-1, -1)
    dist_between_boxes = 0

    for g_index, goal in enumerate(heuristic.goals_list, 0):
        box_dist = state.MAX_ROW * state.MAX_COL
        box_index = -1
        max_box_dist = 0
        for b_index, (pos, letter) in enumerate(boxes_list, 0):
            if (not chosen[b_index]) and (state.goals[goal] in letter):
                norm1 = dist_function(pos, goal)
                box_index = b_index if norm1 < box_dist else box_index
                box_dist = min(box_dist, norm1)
                max_box_dist = max(max_box_dist, norm1)
        if box_index > -1:
            chosen[box_index] = True
            dist_goals[g_index] = (box_dist, goal)
            box_actual = boxes_list[box_index][0]
            if g_index > 0:
                norm1b = dist_function(box_actual, box_previous)
            else:
                norm1b = 0
            dist_between_boxes += norm1b
            box_previous = box_actual

    # max(dist_between_boxes, max([d[0] for d in dist_goals]))
    return max(max_box_dist, max([d[0] if (type(d) == tuple or type(d) == list) else d for d in dist_goals]))
