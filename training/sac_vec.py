import functools
from stable_baselines3 import SAC
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.vec_env import (
    DummyVecEnv,
    SubprocVecEnv,
    VecFrameStack,
    VecMonitor,
)
from stable_baselines3.common.utils import set_random_seed
import torch
import torch.nn as nn

from stable_baselines3.common.torch_layers import BaseFeaturesExtractor

from assetto_corsa import AssettoCorsa, Car, Track
from config import config
from training.environment import AssettoCorsaEnv


# class CorridorFeatureExtractor(BaseFeaturesExtractor):
#     def __init__(self, observation_space, n_corridor: int, features_dim=256):
#         super().__init__(observation_space, features_dim)
#
#         self.n_corridor = n_corridor
#         self.telemetry_size = 14
#
#         self.corridor_cnn = nn.Sequential(
#             nn.LazyConv1d(32, kernel_size=3, padding=1),
#             nn.ReLU(),
#             nn.LazyConv1d(64, kernel_size=3, padding=1),
#             nn.ReLU(),
#             nn.Flatten(),
#             nn.LazyLinear(128),
#             nn.ReLU(),
#         )
#
#         self.telemetry_net = nn.Sequential(
#             nn.LazyLinear(64),
#             nn.ReLU(),
#         )
#
#         self.final_net = nn.Sequential(nn.LazyLinear(features_dim), nn.ReLU())
#
#     def forward(self, obs):
#         telemetry = obs[:, : self.telemetry_size]
#         corridor_flat = obs[:, self.telemetry_size :]
#         corridor = corridor_flat.view(-1, self.n_corridor, 2, 3)
#         corridor = corridor.view(-1, self.n_corridor, 6)
#         corridor = corridor.permute(0, 2, 1)
#
#         telemetry_features = self.telemetry_net(telemetry)
#         corridor_features = self.corridor_cnn(corridor)
#
#         features = torch.cat([telemetry_features, corridor_features], dim=1)
#         return self.final_net(features)
#
class CorridorFeatureExtractor(BaseFeaturesExtractor):
    def __init__(self, observation_space, n_corridor: int, features_dim=256):
        super().__init__(observation_space, features_dim)

        self.n_corridor = n_corridor
        self.telemetry_size = 14
        self.single_obs_dim = self.telemetry_size + self.n_corridor * 2 * 3

        total_obs_dim = observation_space.shape[0]

        assert total_obs_dim % self.single_obs_dim == 0, (
            f"Observation size {total_obs_dim} is not divisible by "
            f"single observation size {self.single_obs_dim}"
        )

        self.n_stack = total_obs_dim // self.single_obs_dim

        self.corridor_cnn = nn.Sequential(
            nn.LazyConv1d(32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.LazyConv1d(64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Flatten(),
            nn.LazyLinear(128),
            nn.ReLU(),
        )

        self.telemetry_net = nn.Sequential(
            nn.LazyLinear(64),
            nn.ReLU(),
        )

        self.final_net = nn.Sequential(
            nn.LazyLinear(features_dim),
            nn.ReLU(),
        )

    def forward(self, obs):
        batch_size = obs.shape[0]

        # Works for both:
        # no VecFrameStack: (batch, single_obs_dim)
        # VecFrameStack:    (batch, n_stack * single_obs_dim)
        obs = obs.view(batch_size, self.n_stack, self.single_obs_dim)

        telemetry = obs[:, :, : self.telemetry_size]
        corridor_flat = obs[:, :, self.telemetry_size :]

        # Flatten stacked telemetry into one vector
        telemetry = telemetry.reshape(batch_size, self.n_stack * self.telemetry_size)

        # corridor: (batch, n_stack, n_corridor, 6)
        corridor = corridor_flat.view(batch_size, self.n_stack, self.n_corridor, 6)

        # Treat frame stack as extra channels:
        # (batch, n_stack, n_corridor, 6) -> (batch, n_stack * 6, n_corridor)
        corridor = corridor.permute(0, 1, 3, 2)
        corridor = corridor.reshape(batch_size, self.n_stack * 6, self.n_corridor)

        telemetry_features = self.telemetry_net(telemetry)
        corridor_features = self.corridor_cnn(corridor)

        features = torch.cat([telemetry_features, corridor_features], dim=1)
        return self.final_net(features)


def make_env(rank: int, port: int, car: Car, track: Track):
    def _init():

        ac = AssettoCorsa(
            car=car,
            track=track,
            port=port,
            id=rank,
        )

        env = AssettoCorsaEnv(ac)
        return env

    return _init


if __name__ == "__main__":
    car = Car()
    tracks = [
        Track("ks_red_bull_ring", "layout_national"),
        Track("spa"),
        Track("imola"),
    ]
    n_envs = 3

    env = SubprocVecEnv(
        [make_env(i, 10000 + i, car, tracks[i % len(tracks)]) for i in range(n_envs)]
    )
    env = VecMonitor(env)
    env = VecFrameStack(env, n_stack=3)

    eval_callback = EvalCallback(
        env,
        eval_freq=10000,
        best_model_save_path=config.OUT_PATH + "SAC/best_model",
        log_path=config.OUT_PATH + "SAC/eval_logs",
        n_eval_episodes=1,
    )

    # model = SAC.load(config.BASE_PATH + "out/SAC/best_model/best_model.zip", env=env)

    model = SAC(
        "MlpPolicy",
        env,
        verbose=2,
        learning_starts=600,
        train_freq=(1, "step"),
        buffer_size=1_000_000,
        batch_size=128,
        gamma=0.992,
        ent_coef=0.03,
        learning_rate=3e-4,
        n_steps=6,
        tensorboard_log=config.OUT_PATH + "SAC/tensorboard",
        policy_kwargs=dict(
            features_extractor_class=CorridorFeatureExtractor,
            features_extractor_kwargs=dict(n_corridor=100),
        ),
    )

    model.learn(total_timesteps=2_000_000, progress_bar=True, callback=eval_callback)
    model.save(config.OUT_PATH + "SAC/final_model")
