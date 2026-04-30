from pathlib import Path
import json

from config import config


class Car:
    def __init__(self, name: str = "ks_porsche_911_gt3_r_2016", skin: str = ""):
        self.path = Path(config.AC_PATH) / "content" / "cars" / name

        if not self.path.exists():
            raise FileNotFoundError(
                f"Car {name} not found in Assetto Corsa installation."
            )

        with open(self.path / "ui" / "ui_car.json", "r") as f:
            car_json = json.load(f, strict=False)

        skins = [i.name for i in (self.path / "skins").iterdir() if i.is_dir()]
        if skin != "" and skin not in skins:
            raise FileNotFoundError(
                f"Skin {skin} not found for car {name}. Available skins: {', '.join(skins)}"
            )
        self.car_info = car_json
        self.skin = skin if skin in skins else skins[0]
