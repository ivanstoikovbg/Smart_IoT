import sys
import time

if "src" not in sys.path:
    sys.path.append("src")

from speed_test import SpeedTest
import config


class TestSpeedTest:
    
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
    
    def test_speed_test_init(self):
        try:
            speed_test = SpeedTest()
            self._test_result("Speed Test Инициализация", True, "Модулът е инициализиран")
            return True
        except Exception as e:
            self._test_result("Speed Test Инициализация", False, str(e))
            return False
    
    def test_speed_test_parse_url(self):
        try:
            speed_test = SpeedTest()
            host, path, port = speed_test._parse_url("http://www.google.com")
            
            if host == "www.google.com" and path == "/" and port == 80:
                self._test_result("Speed Test URL парсване", True, 
                                "Host={}, Path={}, Port={}".format(host, path, port))
                return True
            else:
                self._test_result("Speed Test URL парсване", False, 
                                "Host={}, Path={}, Port={}".format(host, path, port))
                return False
        except Exception as e:
            self._test_result("Speed Test URL парсване", False, str(e))
            return False
    
    def test_speed_test_config(self):
        try:
            has_interval = hasattr(config, 'SPEED_TEST_INTERVAL_S')
            has_url = hasattr(config, 'SPEED_TEST_URL')
            has_timeout = hasattr(config, 'SPEED_TEST_TIMEOUT_S')
            
            if has_interval and has_url and has_timeout:
                self._test_result("Speed Test Конфигурация", True, 
                                "Всички настройки са конфигурирани")
                return True
            else:
                self._test_result("Speed Test Конфигурация", False, "Липсват настройки")
                return False
        except Exception as e:
            self._test_result("Speed Test Конфигурация", False, str(e))
            return False
    
    def run_all(self):
        print("=" * 50)
        print("ТЕСТОВЕ ЗА SPEED TEST")
        print("=" * 50)
        
        self.test_speed_test_init()
        self.test_speed_test_parse_url()
        self.test_speed_test_config()
        
        print("=" * 50)
        print("РЕЗУЛТАТИ: {} преминали, {} провалени".format(self.tests_passed, self.tests_failed))
        print("=" * 50)
        
        return self.tests_failed == 0


if __name__ == "__main__":
    tester = TestSpeedTest()
    success = tester.run_all()
    sys.exit(0 if success else 1)