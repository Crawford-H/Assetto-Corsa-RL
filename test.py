import matplotlib.pyplot as plt
import numpy as np
import keyboard

from assetto_corsa import AssettoCorsa
from assetto_corsa import Car
from assetto_corsa import Track


def plot_world_corridor(corridor: np.ndarray) -> None:
    """
    corridor shape: (N, 2, 3)
    corridor[:, 0] = left boundary points
    corridor[:, 1] = right boundary points
    """
    left = corridor[:, 0, :]
    right = corridor[:, 1, :]

    fig = plt.figure()
    ax = fig.add_subplot(projection="3d")

    # Left/right boundaries
    ax.scatter(left[:, 0], left[:, 1], left[:, 2], label="Left boundary")
    ax.scatter(right[:, 0], right[:, 1], right[:, 2], label="Right boundary")

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")

    min_range = corridor.min()
    max_range = corridor.max()
    ax.set_xlim(min_range, max_range)
    ax.set_ylim(min_range, max_range)
    ax.set_zlim(min_range, max_range)

    ax.set_title("3D World Corridor")
    ax.legend()

    plt.show()


class RelativeCorridorViewer:
    def __init__(self):
        plt.ion()
        self.fig, self.ax = plt.subplots()

        (self.left_line,) = self.ax.plot([], [], label="Left Boundary")
        (self.right_line,) = self.ax.plot([], [], label="Right Boundary")

        self.ax.scatter([0], [0], marker="^", label="Car")

        self.ax.set_xlabel("Local X")
        self.ax.set_ylabel("Local Z")
        self.ax.set_xlim(-30, 30)
        self.ax.set_ylim(-10, 200)
        self.ax.set_title("Relative Corridor")
        self.ax.legend()

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def update(self, rel_corridor: np.ndarray):
        left = rel_corridor[:, 0, :]
        right = rel_corridor[:, 1, :]

        self.left_line.set_data(left[:, 0], left[:, 2])
        self.right_line.set_data(right[:, 0], right[:, 2])

        self.fig.canvas.draw_idle()
        self.fig.canvas.flush_events()


def input(ac: AssettoCorsa):
    if keyboard.is_pressed("esc"):
        exit()

    if keyboard.is_pressed("r"):
        ac.controller.reset()


if __name__ == "__main__":
    track = Track("ks_red_bull_ring", "layout_gp")
    car = Car()
    ac = AssettoCorsa(car, track)
    ac.start()

    corridor_viewer = RelativeCorridorViewer()

    while True:
        input(ac)
        data = ac.telemetry_client.get()
        corridor_viewer.update(
            np.array(
                ac.track.relative_corridor(
                    data.position, data.heading, look_ahead=100, step_size=1
                )
            )
        )
