import functools
from stable_baselines3 import SAC
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv, VecMonitor
from stable_baselines3.common.utils import set_random_seed
import torch
import torch.nn as nn

from stable_baselines3.common.torch_layers import BaseFeaturesExtractor

from assetto_corsa import AssettoCorsa, Car, Track
from config import config
from training.environment import AssettoCorsaEnv


class CorridorFeatureExtractor(BaseFeaturesExtractor):
    def __init__(self, observation_space, n_corridor: int, features_dim=256):
        super().__init__(observation_space, features_dim)

        self.n_corridor = n_corridor
        self.telemetry_size = 14

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

        self.final_net = nn.Sequential(nn.LazyLinear(features_dim), nn.ReLU())

    def forward(self, obs):
        telemetry = obs[:, : self.telemetry_size]
        corridor_flat = obs[:, self.telemetry_size :]
        corridor = corridor_flat.view(-1, self.n_corridor, 2, 3)
        corridor = corridor.view(-1, self.n_corridor, 6)
        corridor = corridor.permute(0, 2, 1)

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
    # track = Track("ks_red_bull_ring", "layout_gp")
    tracks = [Track("ks_red_bull_ring", "layout_gp"), Track("monza"), Track("imola")]
    n_envs = 3

    env = SubprocVecEnv(
        [make_env(i, 10000 + i, car, tracks[i % n_envs]) for i in range(n_envs)]
    )
    env = VecMonitor(env)

    eval_callback = EvalCallback(
        env,
        eval_freq=10000,
        best_model_save_path=config.OUT_PATH + "SAC/best_model",
        log_path=config.OUT_PATH + "SAC/eval_logs",
        n_eval_episodes=1,
    )

    model = SAC(
        "MlpPolicy",
        env,
        verbose=2,
        learning_starts=600,
        train_freq=1,
        buffer_size=1_000_000,
        batch_size=128,
        gamma=0.992,
        ent_coef=0.03,
        learning_rate=3e-4,
        n_steps=6,
        tensorboard_log=config.OUT_PATH + "SAC/tensorboard",
        policy_kwargs=dict(
            features_extractor_class=CorridorFeatureExtractor,
            features_extractor_kwargs=dict(n_corridor=25),
        ),
        device="cpu",
    )

    model.learn(total_timesteps=1_000_000, progress_bar=True, callback=eval_callback)
