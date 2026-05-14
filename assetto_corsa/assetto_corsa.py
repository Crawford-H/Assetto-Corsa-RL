import atexit
import contextlib
import subprocess
import time

from assetto_corsa.car import Car
from assetto_corsa.controller import Controller
from assetto_corsa.telemetry_client import TelemetryClient
from assetto_corsa.track import Track
from config import config
from telemetry_server import TelemetryData


class AssettoCorsa:
    def __init__(
        self,
        car: Car,
        track: Track,
        id: int = 0,
        port: int = 8080,
        ip: str = "127.0.0.1",
        resolution: tuple[int, int] = (640, 480),
    ):
        self.car: Car = car
        self.track: Track = track
        self.id: int = id
        self.port: int = port
        self.ip: str = ip
        self.resolution: tuple[int, int] = resolution

        self.controller: Controller | None = None
        self.telemetry_client: TelemetryClient | None = None
        self.process: subprocess.Popen[bytes] | None = None

    def action(self, steering: float, throttle: float, brake: float) -> None:
        if self.controller is None:
            raise RuntimeError("action called before Assetto Corsa was started")
        self.controller.action(steering, throttle, brake)

    def get_data(self) -> TelemetryData:
        if self.telemetry_client is None:
            raise RuntimeError("get_data called before Assetto Corsa was started")
        return self.telemetry_client.get()

    def start(self):
        if self.process is not None:
            raise RuntimeError("Assetto Corsa is already running.")

        self.telemetry_client = TelemetryClient(self.port, self.ip)
        self.controller = Controller()
        self._load_configs()

        print(
            f"Starting AC[{self.id}] - Controller Id {self.controller.id}, Port: {self.port}, Host: {self.ip}"
        )

        with contextlib.chdir(config.AC_PATH):
            self.process = subprocess.Popen(["acs.exe"])

        _ = self.telemetry_client.get()  # wait for the first data to be received

        _ = atexit.register(self.stop)

        print(f"AC[{self.id}] successfully started")

    def stop(self):
        if self.process is None or self.telemetry_client is None:
            raise RuntimeError("Assetto Corsa is not running.")

        self.telemetry_client.stop()

        self.process.terminate()

    def reset(self):
        if self.controller is None:
            raise RuntimeError("Start has not been called")

        self.controller.reset()
        self.controller.shift_up()

    def _load_configs(self):
        # Telemetry server config
        data_template_path = (
            config.BASE_PATH + "assetto_corsa/configs/telemetry_server.ini"
        )
        data_path = config.AC_PATH + "apps/python/telemetry_server/telemetry_server.ini"

        with open(data_template_path, "r", encoding="utf-8") as f:
            data_sender_template = f.read()

        with open(data_path, "w", encoding="utf-8") as f:
            _ = f.write(
                data_sender_template.format(port=self.port, ip=self.ip, id=self.id)
            )

        # Race config
        race_template_path = config.BASE_PATH + "assetto_corsa/configs/race.ini"
        race_path = config.AC_CFG_PATH + "race.ini"
        with open(race_template_path, "r", encoding="utf-8") as f:
            race_template = f.read()

        with open(race_path, "w", encoding="utf-8") as f:
            _ = f.write(
                race_template.format(
                    car=self.car.path.name,
                    car_skin=self.car.skin,
                    track=self.track.path.name,
                    config_track=self.track.layout,
                    driver_name=str(self.port),
                )
            )

        # Video config
        video_template_path = config.BASE_PATH + "assetto_corsa/configs/video.ini"
        video_path = config.AC_CFG_PATH + "video.ini"
        with open(video_template_path, "r", encoding="utf-8") as f:
            video_template = f.read()

        with open(video_path, "w", encoding="utf-8") as f:
            _ = f.write(
                video_template.format(
                    width=self.resolution[0],
                    height=self.resolution[1],
                )
            )

        if self.controller is None:
            raise ValueError("Controller has not been instantiated")
        # Controlller config
        controller_template_path = (
            config.BASE_PATH + "assetto_corsa/configs/controls.ini"
        )
        controller_path = config.AC_CFG_PATH + "controls.ini"
        with open(controller_template_path, "r", encoding="utf-8") as f:
            controller_template = f.read()
        with open(controller_path, "w", encoding="utf-8") as f:
            controller = "".join(
                [f"CON{i} = VJoyDevice\n" for i in range(self.controller.id)]
            )
            _ = f.write(
                controller_template.format(
                    controllers=controller, joy=self.controller.id - 1
                )
            )


# def find_window_by_pid(pid, timeout=10.0):
#     hwnds = []
#
#     def callback(hwnd, _):
#         _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
#         if window_pid == pid and win32gui.IsWindowVisible(hwnd):
#             hwnds.append(hwnd)
#
#     start = time.time()
#
#     while time.time() - start < timeout:
#         hwnds.clear()
#         win32gui.EnumWindows(callback, None)
#
#         if hwnds:
#             return hwnds[0]  # usually only one main window
#
#         time.sleep(0.2)
#
#     raise RuntimeError("Window not found for PID")
