"""
This app sends telemetry data from the game over a port to the environment
running the RL agent.

The file should be place in the a new directory in the "apps/python/" folder of
the Assetto Corsa installation directory
"""

import pickle
import sys
import os
import platform

import configparser
import acsys
import ac

if platform.architecture()[0] == "64bit":
    sysdir = "stdlib64"
else:
    sysdir = "stdlib"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Lib", sysdir))
os.environ["PATH"] = os.environ["PATH"] + ";."

from sim_info import SimInfo
import socket


app_port = 8080
target_ip = "127.0.0.1"
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
telemetry = None
info = SimInfo()


class TelemetryData:
    def __init__(self):
        if info is None:
            raise RuntimeError("Shared memory not opened")

        self.speed_kmh = ac.getCarState(0, acsys.CS.SpeedKMH)
        self.gear = ac.getCarState(0, acsys.CS.Gear)
        self.rpms = ac.getCarState(0, acsys.CS.RPM)
        self.force_feedback = ac.getCarState(0, acsys.CS.LastFF)

        self.is_collision = max(info.physics.carDamage) > 0
        self.acc_g = ac.getCarState(0, acsys.CS.AccG)
        self.position = ac.getCarState(0, acsys.CS.WorldPosition)
        self.velocity = ac.getCarState(0, acsys.CS.LocalVelocity)
        self.angular_velocity = ac.getCarState(0, acsys.CS.LocalAngularVelocity)
        self.heading = info.physics.heading

        self.normalized_spline_pos = ac.getCarState(
            0, acsys.CS.NormalizedSplinePosition
        )
        self.performance_meter = ac.getCarState(0, acsys.CS.PerformanceMeter)
        self.lap_time = ac.getCarState(0, acsys.CS.LapTime)
        self.best_lap = ac.getCarState(0, acsys.CS.BestLap)
        self.lap_count = ac.getCarState(0, acsys.CS.LapCount)
        self.lap_invalidated = info.physics.numberOfTyresOut > 3


def acMain(ac_version):
    global app_port, target_ip, sock, info

    # load configuration file
    config = configparser.ConfigParser()
    ini_path = os.path.join(os.path.dirname(__file__), "telemetry_server.ini")
    config.read(ini_path)
    app_port = config.getint("NETWORK", "PORT", fallback=8080)
    target_ip = config.get("NETWORK", "TARGET_IP", fallback="127.0.0.1")

    ac.console(
        "[TelemetryServer] Sending telemetry on port: "
        + str(app_port)
        + " Testing: {}".format(info.physics.heading)
    )

    return "Telemetry Server"


def acUpdate(deltaT):
    global sock, app_port, info

    telemetry = TelemetryData()
    # ac.console("Off track: {}, Gear: {}, Name: {}".format(telemetry.lap_invalidated, telemetry.gear, info.static.playerName))
    payload = pickle.dumps(telemetry)
    sock.sendto(payload, (target_ip, app_port))
