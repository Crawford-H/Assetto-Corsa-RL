from dataclasses import dataclass
import json
from pathlib import Path
import struct
from typing import Any
import numpy as np
from scipy.spatial import KDTree

from config import config


Vec3 = tuple[float, float, float]


@dataclass
class AiPoint:
    position: np.ndarray
    distance: float
    id: int

    speed: float
    gas: float
    brake: float
    lat_g: float
    radius: float
    left: float
    right: float
    camber: float
    direction: float
    normal: np.ndarray
    length: float
    forward: np.ndarray
    tag: float
    grade: float


class Track:
    def __init__(self, name: str, layout: str = ""):
        path = Path(config.AC_PATH) / "content" / "tracks" / name

        info_path = (
            path / "ui" / layout / "ui_track.json"
            if layout != ""
            else path / "ui" / "ui_track.json"
        )

        if not path.exists():
            raise FileNotFoundError(
                f"Track {name} not found in Asseetto Corsa installation."
            )

        if (path / "ai").exists() and layout != "":
            raise FileNotFoundError(
                f"Track {name} does not have a layout, but layout {layout} was specified."
            )

        if layout != "" and not (path / layout).exists():
            raise FileNotFoundError(f"Layout {layout} not found for track {name}.")

        with open(info_path, "r", encoding="utf-8") as f:
            self.info: dict[str, str] = json.load(f, strict=False)
        print(self.info)
        self.path: Path = path
        self.layout: str = layout
        self._ai_points: list[AiPoint] = self._parse_ai_file()
        self._ai_kd_tree: KDTree = KDTree([point.position for point in self._ai_points])
        self._corridor: np.ndarray = self._calculate_corridor()

    def get_ai_point(self, position: Vec3) -> AiPoint:
        _, index = self._ai_kd_tree.query(position)
        return self._ai_points[index]

    def relative_corridor(
        self,
        position: Vec3,
        heading: float,
        look_ahead: int = 100,
        step_size: int = 10,
    ) -> np.ndarray:
        _, index = self._ai_kd_tree.query(position)
        n = look_ahead // step_size
        idx = (index + np.arange(n) * step_size) % len(self._corridor)

        left = np.array([self._corridor[i, 0] for i in idx])
        right = np.array([self._corridor[i, 1] for i in idx])

        c = np.cos(heading)
        s = np.sin(heading)
        rotation_mat = np.array([[-c, 0, -s], [0, 1, 0], [-s, 0, c]], dtype=np.float32)

        pos = np.array(position, dtype=np.float32)
        left = (left - pos) @ rotation_mat.T
        right = (right - pos) @ rotation_mat.T

        return np.stack([left, right], axis=1)

    def _calculate_corridor(self) -> np.ndarray:
        pos = np.array([i.position for i in self._ai_points], dtype=np.float64)
        fwd = np.array([i.forward for i in self._ai_points], dtype=np.float64)
        normal = np.array([i.normal for i in self._ai_points], dtype=np.float64)

        left_width = np.array([i.left for i in self._ai_points], dtype=np.float64)
        right_width = np.array([i.right for i in self._ai_points], dtype=np.float64)

        # Compute right vector
        right_vec = np.cross(fwd, normal)

        # Compute corridor edges
        left_points = pos - right_vec * left_width[:, None]
        right_points = pos + right_vec * right_width[:, None]

        # Stack into (N, 2, 3)
        corridor = np.stack([left_points, right_points], axis=1, dtype=np.float32)

        return corridor

    def _parse_ai_file(self):
        if self.layout == "":
            path = self.path / "ai" / "fast_lane.ai"
        else:
            path = self.path / self.layout / "ai" / "fast_lane.ai"

        with open(path, "rb") as f:
            ai_points = []
            _, num_points, _, _ = struct.unpack("4i", f.read(4 * 4))

            for _ in range(num_points):
                data = struct.unpack("4fi", f.read(4 * 5))
                ai_points.append({"point": data})

            num_points_extra = struct.unpack("i", f.read(4))[0]

            for i in range(num_points_extra):
                data = struct.unpack("18f", f.read(4 * 18))
                ai_points[i]["extra"] = data

            return [
                AiPoint(
                    position=np.array(point["point"][:3], dtype=np.float32),
                    distance=point["point"][3],
                    id=point["point"][4],
                    speed=point["extra"][0],
                    gas=point["extra"][1],
                    brake=point["extra"][2],
                    lat_g=point["extra"][3],
                    radius=point["extra"][4],
                    left=point["extra"][5],
                    right=point["extra"][6],
                    camber=point["extra"][7],
                    direction=point["extra"][8],
                    normal=np.array(point["extra"][9:12], dtype=np.float32),
                    length=point["extra"][12],
                    forward=np.array(point["extra"][13:16], dtype=np.float32),
                    tag=point["extra"][16],
                    grade=point["extra"][17],
                )
                for point in ai_points
            ]
