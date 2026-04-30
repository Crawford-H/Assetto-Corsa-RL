Vec3 = tuple[float, float, float]


class TelemetryData:
    def __init__(self):
        self.speed_kmh: float = 0.0
        self.steering_angle: float = 0.0
        self.gas: float = 0.0
        self.brake: float = 0.0
        self.gear: int = 0
        self.rpms: int = 0
        self.force_feedback: float = 0.0

        self.is_collision: bool = False
        self.acc_g: Vec3 = (0.0, 0.0, 0.0)
        self.position: Vec3 = (0.0, 0.0, 0.0)
        self.velocity: Vec3 = (0.0, 0.0, 0.0)
        self.angular_velocity: Vec3 = (0.0, 0.0, 0.0)
        self.heading: float = 0.0

        self.normalized_spline_pos: float = 0.0
        self.performance_meter: float = 0.0
        self.lap_time: float = 0.0
        self.best_lap: float = 0.0
        self.lap_count: int = 0
        self.lap_invalidated: bool = False
