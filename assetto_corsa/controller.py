import time
import pyvjoy


class Controller:
    def __init__(self, id: int):
        self.id: int = id
        self.device: pyvjoy.VJoyDevice = pyvjoy.VJoyDevice(id + 1)

    def reset(self):
        self.device.set_button(3, True)
        time.sleep(0.8)
        self.device.set_button(3, False)

    def action(
        self, steering: float | None, throttle: float | None, brake: float | None
    ):
        if steering is not None:
            self.device.set_axis(pyvjoy.HID_USAGE_X, int((steering + 1) * 16383.5))

        if throttle is not None:
            self.device.set_axis(pyvjoy.HID_USAGE_Y, int(throttle * 32767))

        if brake is not None:
            self.device.set_axis(pyvjoy.HID_USAGE_Z, int(brake * 32767))
