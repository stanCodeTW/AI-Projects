import numpy as np
import math
class Reward:
    def __init__(self):
        self.previous_progress = 0
        self.previous_position = None

    def reward_function(self, params):
        
        # ----------------- Read all input parameters -----------------
        all_wheels_on_track = params['all_wheels_on_track']
        heading = params['heading']
        progress = params['progress']
        speed = params['speed']
        waypoints = params['waypoints']
        closest_waypoints = params['closest_waypoints']
        is_offtrack = params['is_offtrack']
        is_reversed = params['is_reversed']

        # ----------------- Reward calculation -----------------

        # Penalty for offtrack or reversed direction
        if is_offtrack or is_reversed or not all_wheels_on_track:
            return 1e-3
        
        # Start with a baseline reward
        reward = 1.0
        
        # Reward for making progress and being fast
        delta_progress = (progress - self.previous_progress) if progress >= self.previous_progress else (100 + progress - self.previous_progress)
        self.previous_progress = progress
        reward += (delta_progress + speed)
                
        next_waypoints = []
        for i in range(3):
            next_waypoints.append(waypoints[(closest_waypoints[1] + i) % len(waypoints)])
        next_waypoints = np.array(next_waypoints)
        # Calculate first derivatives
        dx_dt = np.gradient(next_waypoints[:, 0])
        dy_dt = np.gradient(next_waypoints[:, 1])

        # Calculate second derivatives
        d2x_dt2 = np.gradient(dx_dt)
        d2y_dt2 = np.gradient(dy_dt)

        # Calculate curvature
        # Positive curvature: Track will turn left
        # Negative curvature: Track will turn right 
        curvatures = (dx_dt * d2y_dt2 - dy_dt * d2x_dt2) / (dx_dt**2 + dy_dt**2)**(3/2)

        # Calculate the direction of the center line based on the closest waypoints
        next_point = waypoints[closest_waypoints[1]]
        prev_point = waypoints[closest_waypoints[0]]

        # Calculate the direction in radius, arctan2(dy, dx), the result is (-pi, pi) in radians
        track_direction = math.atan2(next_point[1] - prev_point[1], next_point[0] - prev_point[0])
        # Convert to degree
        track_direction = math.degrees(track_direction)

        # Calculate the difference between the track direction and the heading direction of the car
        direction_diff = track_direction - heading
        if direction_diff > 180:
            direction_diff = 360 - direction_diff
        elif direction_diff < 180:
            direction_diff = (360 + direction_diff) * -1

        # Penalty for not going straight when the track is straight
        if abs(curvatures[0]) <= 0.15 and abs(direction_diff) > 5:
            reward -= abs(direction_diff)

        # Penalty for turning to the wrong side of the track 
        if curvatures[0] > 0.15 and direction_diff > 5:
            reward *= 0.1
        
        if curvatures[0] < -0.15 and direction_diff < -5:
            reward *= 0.1
        
        return float(reward)

reward_object = Reward()

def reward_function(params):
    return reward_object.reward_function(params)