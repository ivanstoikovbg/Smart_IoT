import sys
import time

if "src" not in sys.path:
    sys.path.append("src")

from sim7600 import SIM7600
from wifi_manager import WiFiManager


class TestCommunication:
    
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []
    
    def _test_result(self, test_name, passed, message=""):
        if passed:
            self.tests_passed += 1
            status = "ПРОМИНАЛ"
            print("✓", test_name, "-", status, message)
        else:
            self.tests_failed += 1
            status = "ПРОВАЛЕН"
            print("✗", test_name, "-", status, message)
        self.test_results.append((test_name, passed, message))
    
    def test_sim7600_init(self):
        try:
            sim = SIM7600()
            self._test_result("SIM7600 Инициализация", True, "Модулът е инициализиран")
            return True
        except Exception as e:
            self._test_result("SIM7600 Инициализация", False, str(e))
            return False
    
    def test_sim7600_status(self):
        try:
            sim = SIM7600()
            sim.init()
            time.sleep(1)
            
            ok, present, rssi = sim.status()
            
            self._test_result("SIM7600 Статус", True, 
                            "UART={}, SIM={}, RSSI={}".format("OK" if ok else "NO", 
                                                              "YES" if present else "NO", 
                                                              rssi))
            return True
        except Exception as e:
            self._test_result("SIM7600 Статус", False, str(e))
            return False
    
    def test_sim7600_traffic_stats(self):
        try:
            sim = SIM7600()
            sent, received, total = sim.get_traffic_stats()
            
            if isinstance(sent, int) and isinstance(received, int) and isinstance(total, int):
                self._test_result("SIM7600 Трафик статистика", True, 
                                "Изпратено={}, Получено={}, Общо={}".format(sent, received, total))
                return True
            else:
                self._test_result("SIM7600 Трафик статистика", False, "Невалидни типове")
                return False
        except Exception as e:
            self._test_result("SIM7600 Трафик статистика", False, str(e))
            return False
    
    def test_wifi_manager_init(self):
        try:
            wifi = WiFiManager()
            self._test_result("WiFi Manager Инициализация", True, "Модулът е инициализиран")
            return True
        except Exception as e:
            self._test_result("WiFi Manager Инициализация", False, str(e))
            return False
    
    def test_wifi_manager_get_status(self):
        try:
            wifi = WiFiManager()
            connected, ip, rssi, ssid = wifi.get_status()
            
            self._test_result("WiFi Manager Статус", True, 
                            "Свързан={}, IP={}".format(connected, ip))
            return True
        except Exception as e:
            self._test_result("WiFi Manager Статус", False, str(e))
            return False
    
    def test_wifi_manager_traffic_stats(self):
        try:
            wifi = WiFiManager()
            sent, received, total = wifi.get_traffic_stats()
            
            if isinstance(sent, int) and isinstance(received, int) and isinstance(total, int):
                self._test_result("WiFi Manager Трафик статистика", True, 
                                "Изпратено={}, Получено={}, Общо={}".format(sent, received, total))
                return True
            else:
                self._test_result("WiFi Manager Трафик статистика", False, "Невалидни типове")
                return False
        except Exception as e:
            self._test_result("WiFi Manager Трафик статистика", False, str(e))
            return False
    
    def run_all(self):
        print("=" * 50)
        print("ТЕСТОВЕ ЗА КОМУНИКАЦИЯ")
        print("=" * 50)
        
        self.test_sim7600_init()
        self.test_sim7600_status()
        self.test_sim7600_traffic_stats()
        
        self.test_wifi_manager_init()
        self.test_wifi_manager_get_status()
        self.test_wifi_manager_traffic_stats()
        
        print("=" * 50)
        print("РЕЗУЛТАТИ: {} преминали, {} провалени".format(self.tests_passed, self.tests_failed))
        print("=" * 50)
        
        return self.tests_failed == 0


if __name__ == "__main__":
    tester = TestCommunication()
    success = tester.run_all()
    sys.exit(0 if success else 1)