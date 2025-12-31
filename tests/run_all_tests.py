import sys
import time

if "src" not in sys.path:
    sys.path.append("src")

from test_sensors import TestSensors
from test_communication import TestCommunication
from test_ota import TestOTA
from test_speed_test import TestSpeedTest


def main():
    print("\n" + "=" * 60)
    print("SMART IOT - ПЪЛЕН ТЕСТОВ СЮИТ")
    print("=" * 60 + "\n")
    
    total_passed = 0
    total_failed = 0
    all_success = True
    
    print("\n[1/4] Тестове за сензори...\n")
    sensor_tester = TestSensors()
    sensor_success = sensor_tester.run_all()
    total_passed += sensor_tester.tests_passed
    total_failed += sensor_tester.tests_failed
    if not sensor_success:
        all_success = False
    
    time.sleep(1)
    
    print("\n[2/4] Тестове за комуникация...\n")
    comm_tester = TestCommunication()
    comm_success = comm_tester.run_all()
    total_passed += comm_tester.tests_passed
    total_failed += comm_tester.tests_failed
    if not comm_success:
        all_success = False
    
    time.sleep(1)
    
    print("\n[3/4] Тестове за OTA Updater...\n")
    ota_tester = TestOTA()
    ota_success = ota_tester.run_all()
    total_passed += ota_tester.tests_passed
    total_failed += ota_tester.tests_failed
    if not ota_success:
        all_success = False
    
    time.sleep(1)
    
    print("\n[4/4] Тестове за Speed Test...\n")
    speed_tester = TestSpeedTest()
    speed_success = speed_tester.run_all()
    total_passed += speed_tester.tests_passed
    total_failed += speed_tester.tests_failed
    if not speed_success:
        all_success = False
    
    print("\n" + "=" * 60)
    print("ОБЩИ РЕЗУЛТАТИ")
    print("=" * 60)
    print("Общо преминали тестове:", total_passed)
    print("Общо провалени тестове:", total_failed)
    print("Общ успех:", "ДА" if all_success else "НЕ")
    print("=" * 60 + "\n")
    
    return all_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)