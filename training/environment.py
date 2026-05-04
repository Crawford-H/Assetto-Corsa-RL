import time
import gymnasium as gym
from gymnasium import spaces
import numpy as np

from assetto_corsa import AssettoCorsa
from telemetry_server.TelemetryData import TelemetryData


class AssettoCorsaEnv(gym.Env):
    def __init__(self, ac: AssettoCorsa):
        super().__init__()
        self.ac: AssettoCorsa = ac
        self.corridor_n: int = 25
        self.corridor_step: int = 5
        self.action: tuple[float, ...] = (0.0, 0.0, 0.0)  # steering, throttle, brake
        self.reset_timer: float | None = None
        self.progress: float = 0.0
        self.prev_spline_pos: float = 0.0

        self.observation_space = make_obs_space_flat(self.corridor_n)
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=np.float32)

    def step(self, action):
        steering, throttle, brake = action

        steering = np.clip(self.action[0] + 0.03 * steering, -1.0, 1.0)
        throttle = np.clip(self.action[1] + 0.1 * throttle, -1.0, 1.0)
        brake = np.clip(self.action[2] + 0.1 * brake, -1.0, 1.0)
        self.action = steering, throttle, brake
        self.ac.action(*self.action)

        data = self.ac.get_data()

        if data.lap_invalidated or data.is_collision:
            reward = -0.5
            truncated, terminated = False, True
        elif data.lap_count >= 1:
            reward = 1.0
            truncated, terminated = False, True
        elif self.reset_timer is not None and time.time() - self.reset_timer > 5.0:
            reward = -0.5
            truncated, terminated = True, False
        else:
            reward = self._calc_reward(data)
            truncated, terminated = False, False

        if self.reset_timer is None and data.speed_kmh < 5.0:
            self.reset_timer = time.time()
        elif self.reset_timer is not None and data.speed_kmh > 5.0:
            self.reset_timer = None

        obs = self._get_obs(data)

        return obs, reward, terminated, truncated, {}

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        if self.ac.process is None:
            self.ac.start()
        else:
            self.ac.reset()

        data = self.ac.get_data()
        self.action = 0.0, 0.0, 0.0
        self.reset_timer = None
        self.prev_spline_pos = data.normalized_spline_pos
        self.progress = data.normalized_spline_pos - 1.0
        obs = self._get_obs(data)

        return obs, {}

    def _calc_reward(self, data: TelemetryData) -> float:
        if data.normalized_spline_pos > self.prev_spline_pos:
            diff = data.normalized_spline_pos - self.prev_spline_pos
            self.progress += diff
            self.prev_spline_pos = data.normalized_spline_pos
        elif data.normalized_spline_pos < 0.1 and self.prev_spline_pos > 0.9:
            diff = data.normalized_spline_pos - self.prev_spline_pos + 1.0
            self.progress += diff
            self.prev_spline_pos = data.normalized_spline_pos
        else:
            diff = 0.0

        point = self.ac.track.get_ai_point(data.position)
        car_pos = np.array(data.position)
        distance = np.linalg.norm(car_pos - point.position)
        racing_line_multiplier = np.exp(-(distance**2) / 5.0)

        return 1000.0 * diff * racing_line_multiplier

    def _get_obs(self, data: TelemetryData):
        corridor = self.ac.track.relative_corridor(
            data.position,
            data.heading,
            self.corridor_n * self.corridor_step,
            self.corridor_step,
        )
        norm_corridor = corridor / (self.corridor_n * self.corridor_step)

        return np.concatenate(
            [
                np.array(
                    [
                        *self.action,
                        *(np.array(data.velocity) / (5.0, 2.0, 80.0)),
                        *(np.array(data.angular_velocity) / 2.0),
                        *(np.array(data.acc_g) / 4.0),
                        data.speed_kmh / 280.0,
                        data.force_feedback / 3.0,
                    ],
                    dtype=np.float32,
                ),
                norm_corridor.flatten().astype(np.float32),
            ]
        )


def make_obs_space_flat(corridor_size):
    return spaces.Box(
        low=-np.inf, high=np.inf, shape=(14 + corridor_size * 2 * 3,), dtype=np.float32
    )
