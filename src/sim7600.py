import time
from machine import Pin, UART
import config


class SIM7600:
    def __init__(self, uart_id=config.SIM_UART_ID, rx_pin=config.SIM_RX_PIN, tx_pin=config.SIM_TX_PIN, baud=config.SIM_BAUD):
        self._uart = UART(uart_id, baudrate=baud, rx=Pin(rx_pin), tx=Pin(tx_pin), timeout=50)
        self._bytes_sent = 0
        self._bytes_received = 0

    def at(self, cmd, timeout_ms=400):
        if self._uart.any():
            try:
                self._uart.read()
            except Exception:
                pass

        self._uart.write((cmd + "\r\n").encode())

        t0 = time.ticks_ms()
        resp = b""
        while time.ticks_diff(time.ticks_ms(), t0) < timeout_ms:
            if self._uart.any():
                resp += self._uart.read()
                if b"OK" in resp or b"ERROR" in resp:
                    break
            time.sleep_ms(20)
        return resp

    def init(self):
        self.at("ATE0", timeout_ms=400)
        self.at("AT+CGPS=1", timeout_ms=700)

    def _parse_csq(self, resp):
        try:
            s = resp.decode("utf-8", "ignore")
            for line in s.splitlines():
                line = line.strip()
                if line.startswith("+CSQ:"):
                    return int(line.split(":")[1].split(",")[0].strip())
        except Exception:
            pass
        return None

    def status(self):
        r = self.at("AT", timeout_ms=400)
        ok = (b"OK" in r)

        present = None
        rssi = None

        if ok:
            cpin = self.at("AT+CPIN?", timeout_ms=600).upper()
            if b"SIM NOT INSERTED" in cpin or b"NOT INSERTED" in cpin:
                present = False
            elif b"+CPIN:" in cpin:
                present = True

            rssi = self._parse_csq(self.at("AT+CSQ", timeout_ms=600))

        return ok, present, rssi

    def gps_read(self):
        r = self.at("AT+CGPSINFO", timeout_ms=900)
        try:
            s = r.decode("utf-8", "ignore")
            for ln in s.splitlines():
                ln = ln.strip()
                if ln.startswith("+CGPSINFO:"):
                    data = ln.split(":", 1)[1].strip()
                    if not data or data.startswith(",,,,"):
                        return None, None

                    parts = data.split(",")
                    if len(parts) < 4:
                        return None, None

                    lat_raw, ns, lon_raw, ew = parts[0], parts[1], parts[2], parts[3]
                    if not lat_raw or not lon_raw:
                        return None, None

                    lat_deg = float(lat_raw[:2])
                    lat_min = float(lat_raw[2:])
                    lon_deg = float(lon_raw[:3])
                    lon_min = float(lon_raw[3:])

                    lat = lat_deg + lat_min / 60.0
                    lon = lon_deg + lon_min / 60.0

                    if ns == "S":
                        lat = -lat
                    if ew == "W":
                        lon = -lon

                    return round(lat, 6), round(lon, 6)
        except Exception:
            pass

        return None, None
    
    def get_traffic_stats(self):
        total = self._bytes_sent + self._bytes_received
        return self._bytes_sent, self._bytes_received, total
    
    def update_traffic(self, bytes_sent=0, bytes_received=0):
        self._bytes_sent += bytes_sent
        self._bytes_received += bytes_received
    
    def reset_traffic_stats(self):
        self._bytes_sent = 0
        self._bytes_received = 0