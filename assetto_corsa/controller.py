import time
import pyvjoy


class Controller:
    def __init__(self):
        id, devices = get_device()
        self.id: int = id
        self.n_devices: int = devices
        self.device: pyvjoy.VJoyDevice = pyvjoy.VJoyDevice(id)

    def reset(self):
        self.device.set_button(3, True)
        time.sleep(0.1)
        self.device.set_button(3, False)
        self.action(steering=0.0, throttle=1.0, brake=1.0)
        time.sleep(0.1)
        self.action(steering=0.0, throttle=0.0, brake=0.0)

    def shift_up(self):
        self.device.set_button(1, True)
        time.sleep(0.1)
        self.device.set_button(1, False)

    def shift_down(self):
        self.device.set_button(2, True)
        time.sleep(0.1)
        self.device.set_button(2, False)

    def action(
        self, steering: float | None, throttle: float | None, brake: float | None
    ):
        if steering is not None:
            self.device.set_axis(pyvjoy.HID_USAGE_X, int((steering + 1) * 16383.5))

        if throttle is not None:
            self.device.set_axis(pyvjoy.HID_USAGE_Y, int(throttle * 32767))

        if brake is not None:
            self.device.set_axis(pyvjoy.HID_USAGE_Z, int(brake * 32767))


def get_device() -> tuple[int, int]:
    id = None
    total_devices = 0

    for i in range(1, 17):
        match pyvjoy._sdk.GetVJDStatus(i):
            case pyvjoy.VJD_STAT_FREE:
                if id is None:
                    id = i
                total_devices += 1
            case pyvjoy.VJD_STAT_BUSY:
                total_devices += 1

    if id is None:
        raise RuntimeError("No VJoy Devices available")

    return id, total_devices
