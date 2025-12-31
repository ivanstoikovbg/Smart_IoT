import time
import network
import config


class WiFiManager:
    
    def __init__(self, ssid=config.WIFI_SSID, password=config.WIFI_PASSWORD):
        self._ssid = ssid
        self._password = password
        self._wifi = None
        self._connected = False
        self._last_connect_attempt = 0
        self._connect_timeout = config.WIFI_CONNECT_TIMEOUT_S
        self._bytes_sent = 0
        self._bytes_received = 0
        self._last_bytes_sent = 0
        self._last_bytes_received = 0
        
    def _get_wifi_interface(self):

        if self._wifi is None:
            self._wifi = network.WLAN(network.STA_IF)
        return self._wifi
    
    def connect(self, timeout_s=None):

        if timeout_s is None:
            timeout_s = self._connect_timeout
            
        if not self._ssid or not self._password:
            print("WiFi: SSID или паролата не са конфигурирани")
            return False
        
        wifi = self._get_wifi_interface()
        
        if not wifi.active():
            wifi.active(True)
            time.sleep(0.5)
        
        if wifi.isconnected():
            self._connected = True
            return True
        
        print("WiFi: Свързване към", self._ssid, "...")
        wifi.connect(self._ssid, self._password)
        
        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < (timeout_s * 1000):
            if wifi.isconnected():
                self._connected = True
                ip = wifi.ifconfig()[0]
                print("WiFi: Свързан! IP:", ip)
                return True
            time.sleep(0.5)
        
        self._connected = False
        print("WiFi: Неуспешно свързване (timeout)")
        return False
    
    def disconnect(self):
        wifi = self._get_wifi_interface()
        if wifi.active():
            wifi.disconnect()
            wifi.active(False)
            self._connected = False
            print("WiFi: Прекъснато")
    
    def is_connected(self):
        wifi = self._get_wifi_interface()
        if not wifi.active():
            self._connected = False
            return False
        
        self._connected = wifi.isconnected()
        return self._connected
    
    def get_status(self):
        wifi = self._get_wifi_interface()
        
        if not wifi.active():
            return False, None, None, None
        
        if not wifi.isconnected():
            self._connected = False
            return False, None, None, None
        
        self._connected = True
        ifconfig = wifi.ifconfig()
        ip = ifconfig[0] if ifconfig else None
        
        try:
            status = wifi.status()
            rssi = None
            ssid = self._ssid
        except Exception:
            rssi = None
            ssid = self._ssid
        
        return True, ip, rssi, ssid
    
    def get_ip(self):
        if self.is_connected():
            wifi = self._get_wifi_interface()
            ifconfig = wifi.ifconfig()
            return ifconfig[0] if ifconfig else None
        return None
    
    def get_traffic_stats(self):
        wifi = self._get_wifi_interface()
        if not wifi.active() or not wifi.isconnected():
            return 0, 0, 0
        
        try:
            total = self._bytes_sent + self._bytes_received
            return self._bytes_sent, self._bytes_received, total
        except Exception:
            return 0, 0, 0
    
    def update_traffic(self, bytes_sent=0, bytes_received=0):
        self._bytes_sent += bytes_sent
        self._bytes_received += bytes_received
    
    def reset_traffic_stats(self):
        self._bytes_sent = 0
        self._bytes_received = 0