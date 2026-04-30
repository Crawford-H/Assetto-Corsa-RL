import pickle
from queue import Queue
from threading import Thread
import socket

from telemetry_server.TelemetryData import TelemetryData


class TelemetryClient:
    def __init__(self, port: int = 8080, ip: str = "127.0.0.1"):
        self.queue: Queue[TelemetryData] = Queue(maxsize=1)
        self.thread: Thread = Thread(target=self._listen, daemon=True)
        self.sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.running: bool = False

        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((ip, port))

    def start(self):
        self.running = True
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join(timeout=1.0)
        self.sock.close()

    def get(self) -> TelemetryData:
        return self.queue.get(block=True)

    def _listen(self):
        while self.running:
            try:
                data, _ = self.sock.recvfrom(4096)
                new_data = pickle.loads(data)
                if self.queue.full():
                    _ = self.queue.get_nowait()
                self.queue.put_nowait(new_data)
            except Exception as e:
                print(f"Error receiving telemetry data: {e}")
