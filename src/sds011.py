from machine import Pin, UART
import config


class SDS011Sensor:
    def __init__(self, uart_id=config.SDS_UART_ID, rx_pin=config.SDS_RX_PIN, baud=config.SDS_BAUD):
        self._uart = UART(uart_id, baudrate=baud, rx=Pin(rx_pin), timeout=50)
        self._buf = b""

    def read_once(self):
        if self._uart.any():
            self._buf += self._uart.read()
            if len(self._buf) > 128:
                self._buf = self._buf[-128:]

        i = self._buf.find(b"\xAA\xC0")
        if i != -1 and len(self._buf) >= i + 10:
            frame = self._buf[i:i + 10]
            self._buf = self._buf[i + 10:]
            if frame[9] == 0xAB:
                pm25 = round((frame[2] + frame[3] * 256) / 10.0, 1)
                pm10 = round((frame[4] + frame[5] * 256) / 10.0, 1)
                return pm25, pm10

        return None, None
    

    print("SDS011Sensor: test")