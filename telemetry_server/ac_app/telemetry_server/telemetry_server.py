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

from sim_info import info
import socket


app_port = 8080
target_ip = "127.0.0.1"
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
telemetry = None


class TelemetryData:
    def __init__(self):
        self.speed_kmh = ac.getCarState(0, acsys.CS.SpeedKMH)
        self.steering_angle = ac.getCarState(0, acsys.CS.Steer)
        self.gas = ac.getCarState(0, acsys.CS.Gas)
        self.brake = ac.getCarState(0, acsys.CS.Brake)
        self.gear = ac.getCarState(0, acsys.CS.Gear)
        self.rpms = ac.getCarState(0, acsys.CS.RPM)
        self.force_feedback = ac.getCarState(0, acsys.CS.LastFF)

        self.acc_g = ac.getCarState(0, acsys.CS.AccG)
        self.position = ac.getCarState(0, acsys.CS.WorldPosition)
        self.velocity = ac.getCarState(0, acsys.CS.Velocity)
        self.heading = info.physics.heading

        self.normalized_spline_pos = ac.getCarState(
            0, acsys.CS.NormalizedSplinePosition
        )
        self.performance_meter = ac.getCarState(0, acsys.CS.PerformanceMeter)
        self.lap_time = ac.getCarState(0, acsys.CS.LapTime)
        self.lap_count = ac.getCarState(0, acsys.CS.LapCount)
        self.lap_invalidated = info.physics.numberOfTyresOut > 3


def acMain(ac_version):
    global app_port, target_ip, sock

    # load configuration file
    config = configparser.ConfigParser()
    ini_path = os.path.join(os.path.dirname(__file__), "TelemetrySender.ini")
    config.read(ini_path)
    app_port = config.getint("NETWORK", "PORT", fallback=8080)
    target_ip = config.get("NETWORK", "TARGET_IP", fallback="127.0.0.1")

    # Bind to socket to send data to
    sock.bind((target_ip, app_port + 1))
    sock.setblocking(False)
    ac.console("[TelemetryServer] Sending telemetry on port: " + str(app_port))

    return "Telemetry Server"


def acUpdate(deltaT):
    global sock, app_port
    payload = pickle.dumps(TelemetryData())
    sock.sendto(payload, (target_ip, app_port))
