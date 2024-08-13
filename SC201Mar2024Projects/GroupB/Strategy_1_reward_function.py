def reward_function(params):
    '''
    Example of rewarding the agent to slow down at the corners and speed up at straight lines
    '''
    # Corner type speed params
    hairpin = 2.5
    classic = 3
    decr_radius = 1.5

    # Coner positions
    wp_hairpin = [69, 70, 71, 72, 73, 74, 75,
                  101, 102, 103, 104, 105, 106, 107, 108, 109]

    wp_classic = [20, 21, 22, 23, 24, 25,
                  43, 44, 45, 46, 47,
                  56, 57, 58, 59,
                  87, 88, 89, 90,
                  172, 173, 174, 175, 176, 177,
                  189, 191]

    wp_decr_radius = [134, 135, 136, 137, 138, 139,
                      148, 149, 150, 151, 152, 153, 154]

    # Read input parameters
    is_offtrack = params['is_offtrack']
    wp = params['closest_waypoints'][1]
    speed = params['speed']

    # Get reward based on different road type
    if not is_offtrack:
        if wp in wp_hairpin:
            if speed <= hairpin:
                reward = 10
            else:
                reward = -((5 - speed) ** 2)
        elif wp in wp_classic:
            if speed <= classic:
                reward = 10
            else:
                reward = -((5 - speed) ** 2)
        elif wp in wp_decr_radius:
            if speed <= decr_radius:
                reward = 10
            else:
                reward = -((5 - speed) ** 2)
        else:
            reward = speed
    else:
        reward = -speed
    return float(reward)