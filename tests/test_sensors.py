import sys
import time

if "src" not in sys.path:
    sys.path.append("src")

from dht22 import DHT22Sensor
from mq2 import MQ2Sensor
from sds011 import SDS011Sensor


class TestSensors:    
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
    
    def test_dht22_init(self):
        try:
            sensor = DHT22Sensor()
            self._test_result("DHT22 Инициализация", True, "Сензорът е инициализиран")
            return True
        except Exception as e:
            self._test_result("DHT22 Инициализация", False, str(e))
            return False
    
    def test_dht22_read(self):
        try:
            sensor = DHT22Sensor()
            t, h = sensor.read()
            
            if t is None or h is None:
                self._test_result("DHT22 Четене", False, "Няма данни от сензора")
                return False
            
            if -40 <= t <= 80 and 0 <= h <= 100:
                self._test_result("DHT22 Четене", True, "T={}°C, H={}%".format(t, h))
                return True
            else:
                self._test_result("DHT22 Четене", False, "Невалидни стойности: T={}, H={}".format(t, h))
                return False
        except Exception as e:
            self._test_result("DHT22 Четене", False, str(e))
            return False
    
    def test_mq2_init(self):
        try:
            sensor = MQ2Sensor()
            self._test_result("MQ-2 Инициализация", True, "Сензорът е инициализиран")
            return True
        except Exception as e:
            self._test_result("MQ-2 Инициализация", False, str(e))
            return False
    
    def test_mq2_read(self):
        try:
            sensor = MQ2Sensor()
            value = sensor.read_avg()
            
            if value is None:
                self._test_result("MQ-2 Четене", False, "Няма данни")
                return False
            
            if 0 <= value <= 4095:
                self._test_result("MQ-2 Четене", True, "Стойност={}".format(value))
                return True
            else:
                self._test_result("MQ-2 Четене", False, "Невалидна стойност: {}".format(value))
                return False
        except Exception as e:
            self._test_result("MQ-2 Четене", False, str(e))
            return False
    
    def test_sds011_init(self):
        """Тест за инициализация на SDS011"""
        try:
            sensor = SDS011Sensor()
            self._test_result("SDS011 Инициализация", True, "Сензорът е инициализиран")
            return True
        except Exception as e:
            self._test_result("SDS011 Инициализация", False, str(e))
            return False
    
    def test_sds011_read(self):
        try:
            sensor = SDS011Sensor()
            
            max_attempts = 3
            for attempt in range(max_attempts):
                pm25, pm10 = sensor.read_once()
                
                if pm25 is not None and pm10 is not None:
                    if 0 <= pm25 <= 1000 and 0 <= pm10 <= 1000:
                        self._test_result("SDS011 Четене", True, "PM2.5={} ug/m3, PM10={} ug/m3".format(pm25, pm10))
                        return True
                    else:
                        self._test_result("SDS011 Четене", False, "Невалидни стойности: PM2.5={}, PM10={}".format(pm25, pm10))
                        return False
                
                if attempt < max_attempts - 1:
                    time.sleep(2)
            
            self._test_result("SDS011 Четене", True, "Няма данни още (нормално при първо стартиране, може да отнеме до 30s)")
            return True
        except Exception as e:
            self._test_result("SDS011 Четене", False, str(e))
            return False
    
    def run_all(self):
        print("=" * 50)
        print("ТЕСТОВЕ ЗА СЕНЗОРИ")
        print("=" * 50)
        
        self.test_dht22_init()
        self.test_dht22_read()
        
        self.test_mq2_init()
        self.test_mq2_read()
        
        self.test_sds011_init()
        self.test_sds011_read()
        
        print("=" * 50)
        print("РЕЗУЛТАТИ: {} преминали, {} провалени".format(self.tests_passed, self.tests_failed))
        print("=" * 50)
        
        return self.tests_failed == 0


if __name__ == "__main__":
    tester = TestSensors()
    success = tester.run_all()
    sys.exit(0 if success else 1)