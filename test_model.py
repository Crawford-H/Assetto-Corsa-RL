import functools
from stable_baselines3 import SAC
from stable_baselines3.common.vec_env import DummyVecEnv, VecFrameStack

from assetto_corsa import AssettoCorsa, Car
from assetto_corsa import Track
from training.environment import AssettoCorsaEnv

if __name__ == "__main__":
    car = Car()
    track = Track("ks_red_bull_ring", "layout_gp")
    ac = AssettoCorsa(car, track)
    partial = functools.partial(AssettoCorsaEnv, ac)
    env = DummyVecEnv([partial])
    env = VecFrameStack(env, 3)
    model = SAC.load("out/SAC/final_model.zip", env=env)

    obs = env.reset()
    while True:
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, terminated, info = env.step(action)
        print(f"Reward: {reward}")
