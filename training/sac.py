import functools
import argparse

from stable_baselines3 import SAC
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.vec_env import (
    DummyVecEnv,
    VecMonitor,
    VecNormalize,
)

from config import config
from assetto_corsa import AssettoCorsa, Car, Track
from training.environment import AssettoCorsaEnv


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train a SAC agent on Assetto Corsa")

    car = Car()
    track = Track("ks_red_bull_ring", "layout_gp")
    ac = AssettoCorsa(car, track)

    partial = functools.partial(AssettoCorsaEnv, ac)
    env = DummyVecEnv([partial])
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
        train_freq=3,
        buffer_size=1_000_000,
        batch_size=128,
        gamma=0.992,
        ent_coef="0.03",
        learning_rate=3e-4,
        n_steps=6,
        tensorboard_log=config.OUT_PATH + "SAC/tensorboard",
        policy_kwargs={"net_arch": [256, 256, 256]},
    )

    model.learn(total_timesteps=1_000_000, progress_bar=True, callback=eval_callback)
