import numpy as np
import math


class Reward:
    def __init__(self):
        self.previous_progress = 0
        self.previous_position = None

    def reward_function(self, params):

        # ----------------- Read all input parameters -----------------
        all_wheels_on_track = params["all_wheels_on_track"]
        x = params["x"]
        y = params["y"]
        distance_from_center = params["distance_from_center"]
        is_left_of_center = params["is_left_of_center"]
        heading = params["heading"]
        progress = params["progress"]
        steps = params["steps"]
        speed = params["speed"]
        steering_angle = params["steering_angle"]
        track_width = params["track_width"]
        waypoints = params["waypoints"]
        closest_waypoints = params["closest_waypoints"]
        is_offtrack = params["is_offtrack"]
        is_reversed = params["is_reversed"]

        # ----------------- Reward calculation -----------------

        # Penalty for offtrack or reversed direction
        if is_offtrack or is_reversed:
            return 1e-3

        # Start with a baseline reward
        reward = 1.0

        # Reward for moving in the correct direction
        current_position = [x, y]
        if self.previous_position:
            moving_vector = [
                x - self.previous_position[0],
                y - self.previous_position[1],
            ]
            reward += moving_vector[0] ** 2 + moving_vector[1] ** 2
        else:
            reward += speed
        self.previous_position = current_position

        next_waypoints = []
        for i in range(3):
            next_waypoints.append(
                waypoints[(closest_waypoints[1] + i) % len(waypoints)]
            )
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
        curvatures = (dx_dt * d2y_dt2 - dy_dt * d2x_dt2) / (
            dx_dt**2 + dy_dt**2
        ) ** (3 / 2)

        # Calculate the direction of the center line based on the closest waypoints
        # look ahead a little bit when not in curve
        def next_point(look_ahead=0):
            return waypoints[closest_waypoints[1] + look_ahead]

        prev_point = waypoints[closest_waypoints[0]]

        def track_direction(look_ahead=0):
            # Convert to degree
            return math.degrees(
                # Calculate the direction in radius, arctan2(dy, dx), the result is (-pi, pi) in radians
                math.atan2(
                    next_point(look_ahead)[1] - prev_point[1],
                    next_point(look_ahead)[0] - prev_point[0],
                )
            )

        # Calculate the difference between the track direction and the heading direction of the car
        def direction_diff(look_ahead=0):
            result = abs(track_direction(look_ahead) - heading)
            if result > 180:
                result = 360 - result
            return result

        # Encourage using of track edge when entering a curve
        # value: 0 ~ 1
        curve_edge_reward = (2 * distance_from_center) / track_width
        if (
            abs(curvatures[0]) < 0.1
            and abs(steering_angle) < 2.5
            and abs(direction_diff(2)) < 5
        ):
            reward += speed
        if curvatures[0] > 0.15 and steering_angle >= 5:
            reward += speed
            reward += curve_edge_reward
            if direction_diff(0) < 2.5:
                reward *= 1.2
        if curvatures[0] < -0.15 and steering_angle <= -5:
            reward += speed
            reward += curve_edge_reward
            if direction_diff(0) < 2.5:
                reward *= 1.2

        return float(reward)


reward_object = Reward()


def reward_function(params):
    return reward_object.reward_function(params)
