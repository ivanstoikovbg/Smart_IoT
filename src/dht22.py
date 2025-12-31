import time
from machine import Pin
import dht
import config


class DHT22Sensor:
    def __init__(self, pin=config.DHT22_PIN):
        self._dht = dht.DHT22(Pin(pin))

    def read(self):
        for _ in range(2):
            try:
                self._dht.measure()
                t = round(float(self._dht.temperature()), 1)
                h = round(float(self._dht.humidity()), 1)
                return t, h
            except Exception:
                time.sleep(0.2)
        return None, None