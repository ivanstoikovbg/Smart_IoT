import sys
import time

if "src" not in sys.path:
    sys.path.append("src")

from ota_updater import OTAUpdater
import config


class TestOTA:
    
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
    
    def test_ota_init(self):
        try:
            ota = OTAUpdater()
            self._test_result("OTA Инициализация", True, "Модулът е инициализиран")
            return True
        except Exception as e:
            self._test_result("OTA Инициализация", False, str(e))
            return False
    
    def test_ota_get_status(self):
        try:
            ota = OTAUpdater()
            status = ota.get_status()
            
            if isinstance(status, dict) and 'enabled' in status:
                self._test_result("OTA Статус", True, 
                                "Активен={}, Следваща проверка след {} с".format(
                                    status['enabled'], status['next_check_in']))
                return True
            else:
                self._test_result("OTA Статус", False, "Невалиден формат")
                return False
        except Exception as e:
            self._test_result("OTA Статус", False, str(e))
            return False
    
    def test_ota_file_hash(self):
        try:
            ota = OTAUpdater()
            hash_value = ota._get_file_hash("main.py")
            
            if hash_value is None:
                self._test_result("OTA Hash изчисляване", False, "Не може да се изчисли hash")
                return False
            
            if isinstance(hash_value, str) and len(hash_value) == 64:
                self._test_result("OTA Hash изчисляване", True, "Hash дължина={}".format(len(hash_value)))
                return True
            else:
                self._test_result("OTA Hash изчисляване", False, "Невалиден hash формат")
                return False
        except Exception as e:
            self._test_result("OTA Hash изчисляване", False, str(e))
            return False
    
    def test_ota_config(self):
        try:
            has_enabled = hasattr(config, 'OTA_ENABLED')
            has_interval = hasattr(config, 'OTA_CHECK_INTERVAL_S')
            has_repo = hasattr(config, 'OTA_GITHUB_REPO')
            has_files = hasattr(config, 'OTA_FILES_TO_UPDATE')
            
            if has_enabled and has_interval and has_repo and has_files:
                self._test_result("OTA Конфигурация", True, 
                                "Всички настройки са конфигурирани")
                return True
            else:
                self._test_result("OTA Конфигурация", False, "Липсват настройки")
                return False
        except Exception as e:
            self._test_result("OTA Конфигурация", False, str(e))
            return False
    
    def run_all(self):
        print("=" * 50)
        print("ТЕСТОВЕ ЗА OTA UPDATER")
        print("=" * 50)
        
        self.test_ota_init()
        self.test_ota_get_status()
        self.test_ota_file_hash()
        self.test_ota_config()
        
        print("=" * 50)
        print("РЕЗУЛТАТИ: {} преминали, {} провалени".format(self.tests_passed, self.tests_failed))
        print("=" * 50)
        
        return self.tests_failed == 0


if __name__ == "__main__":
    tester = TestOTA()
    success = tester.run_all()
    sys.exit(0 if success else 1)