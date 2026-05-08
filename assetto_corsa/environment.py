import time
import gymnasium as gym
from gymnasium import spaces
import numpy as np
from numpy.typing import NDArray

from .assetto_corsa import AssettoCorsa
from .track import AiPoint
from telemetry_server.TelemetryData import TelemetryData

ObsType = NDArray[np.float32]
ActType = NDArray[np.float32]


class AssettoCorsaEnv(gym.Env[ObsType, ActType]):
    def __init__(self, ac: AssettoCorsa, corridor_n: int = 100, corridor_step: int = 1):
        super().__init__()
        self.ac: AssettoCorsa = ac
        self.corridor_n: int = corridor_n
        self.corridor_step: int = corridor_step
        self.action: tuple[float, ...] = (0.0, 0.0, 0.0)  # steering, throttle, brake
        self.reset_timer: float | None = None
        self.progress: float = 0.0
        self.prev_spline_pos: float = 0.0
        self.track_length: int = int(self.ac.track.info["length"])

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
        racing_line = self.ac.track.get_ai_point(data.position)
        off_track = is_off_track(racing_line, data.position, margin=1.5)

        if off_track or data.is_collision or data.lap_invalidated:
            reward = -10
            truncated, terminated = False, True
        elif data.lap_count >= 1:
            reward = 10
            truncated, terminated = False, True
        elif self.reset_timer is not None and time.time() - self.reset_timer > 5.0:
            reward = -10
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

    def reset(self, seed=None, options=None):  # pyright: ignore[reportExplicitAny]
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
        racing_line_multiplier = np.exp(-(distance**2) / 20.0)

        return (self.track_length / 2) * diff * racing_line_multiplier

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


def is_off_track(
    racing_line: AiPoint, car_position: tuple[float, float, float], margin: float = 0.0
) -> bool:
    p = np.asarray(car_position, dtype=np.float32)
    center = np.asarray(racing_line.position)
    normal = np.asarray(racing_line.normal)
    forward = np.asarray(racing_line.forward)

    left = -racing_line.left - margin
    right = racing_line.right + margin

    right_vec = np.cross(forward, normal)
    offset = p - center
    lateral = np.dot(offset, right_vec)

    return left > lateral or right < lateral


def make_obs_space_flat(corridor_size):
    return spaces.Box(
        low=-np.inf, high=np.inf, shape=(14 + corridor_size * 2 * 3,), dtype=np.float32
    )
