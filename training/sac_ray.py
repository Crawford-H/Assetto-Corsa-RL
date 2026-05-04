from pprint import pprint
from gymnasium import VectorizeMode
import ray
from ray.tune.registry import register_env
from ray.rllib.algorithms.sac import SACConfig
from assetto_corsa import AssettoCorsa
from assetto_corsa import Car
from assetto_corsa import Track
from training.environment import AssettoCorsaEnv


TRACKS = [("ks_red_bull_ring", "layout_gp"), ("monza", ""), ("imola", "")]


def env_creator(config):
    id = config.worker_index

    car = Car()
    track_name, layout = TRACKS[id % len(TRACKS)]
    track = Track(track_name, layout)
    ac = AssettoCorsa(car, track, id=id, port=10000 + id)

    return AssettoCorsaEnv(ac)


if __name__ == "__main__":
    register_env("ac_env", env_creator)

    config = (
        SACConfig()
        .environment("ac_env")
        .env_runners(
            num_env_runners=2,
            num_envs_per_env_runner=1,
            remote_worker_envs=True,
            gym_env_vectorize_mode=VectorizeMode.ASYNC,
        )
        .training(
            gamma=0.992,
            train_batch_size=128,
            replay_buffer_config={
                "type": "EpisodeReplayBuffer",
                "capacity": 1_000_000,
            },
            initial_alpha=0.03,
            tau=0.005,
            n_step=6,
        )
        .reporting(min_sample_timesteps_per_iteration=1000)
        .debugging(log_level="INFO")
    )

    algo = config.build()
    pprint(algo.train())
    exit()

    best_reward = float("-inf")
    total_timesteps = 1_000_000
    timesteps = 0

    while timesteps < total_timesteps:
        result = algo.train()

        timesteps = result.get("timesteps_total", timesteps)
        reward_mean = result.get("episode_reward_mean", None)

        print(
            f"timsteps={timesteps} "
            f"reward_mean={reward_mean} "
            f"episodes={result.get('episodes_total')}"
        )

        if reward_mean is not None and reward_mean > best_reward:
            best_reward = reward_mean
            print(f"New best reward: {best_reward}")

    algo.stop()
    ray.shutdown()
