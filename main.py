import sys
import time

if "src" not in sys.path:
    sys.path.append("src")

import config
from dht22 import DHT22Sensor
from mq2 import MQ2Sensor
from sds011 import SDS011Sensor
from sim7600 import SIM7600
from wifi_manager import WiFiManager
from speed_test import SpeedTest
from ota_updater import OTAUpdater


def main():
    dht22 = DHT22Sensor()
    mq2 = MQ2Sensor()
    sds = SDS011Sensor()
    sim = SIM7600()
    wifi = WiFiManager()
    speed_test = SpeedTest()
    ota_updater = OTAUpdater()

    print("Устройство:", config.DEVICE_NAME)
    print("Стартиране на станцията...")
    
    # Изпълняване на тестове при стартиране (ако е конфигурирано)
    if config.TEST_ENABLED and config.TEST_RUN_ON_STARTUP:
        print("Изпълняване на тестове...")
        try:
            sys.path.append("tests")
            from run_all_tests import main as run_tests
            tests_success = run_tests()
            if not tests_success:
                print("ВНИМАНИЕ: Някои тестове са провалени!")
            time.sleep(2)
        except Exception as e:
            print("Грешка при изпълняване на тестове:", e)

    sim.init()

    lat = None
    lon = None
    last_gps = 0
    sim_failure_count = 0
    using_wifi = False
    using_sim = True 
    last_comm_check = 0
    last_speed_test = 0
    last_ota_check = 0
    sim_ok = False
    sim_present = False
    sim_rssi = None
    internet_speed_kbps = None
    internet_upload_kbps = None
    internet_ping_ms = None
    
    print("SIM: Използване на SIM като основна комуникация") 

    while True:
        uptime = time.ticks_ms() // 1000

        t, h = dht22.read()
        mq = mq2.read_avg()
        pm25, pm10 = sds.read_once()

        wifi_connected, wifi_ip, wifi_rssi, wifi_ssid = wifi.get_status()
        
        sim_ok, sim_present, sim_rssi = sim.status()
        sim_available = sim_ok and sim_present
        
        if uptime - last_comm_check >= config.WIFI_CHECK_INTERVAL_S:
            last_comm_check = uptime
            
            if using_sim and not using_wifi:
                if not sim_available:
                    sim_failure_count += 1
                    print("SIM: Проблем детектиран (брой:", sim_failure_count, ")")
                    
                    if sim_failure_count >= config.SIM_FAILURE_THRESHOLD:
                        print("SIM: Превключване към WiFi резервен режим...")
                        if wifi.connect():
                            wifi_connected, wifi_ip, wifi_rssi, wifi_ssid = wifi.get_status()
                            if wifi_connected:
                                using_wifi = True
                                using_sim = False  
                                sim_failure_count = 0
                                print("WiFi: Активиран като резервен режим")
                            else:
                                print("WiFi: Неуспешно свързване, ще продължим да опитваме")
                        else:
                            print("WiFi: Неуспешно свързване, ще продължим да опитваме")
                else:
                    if sim_failure_count > 0:
                        sim_failure_count = 0
                        print("SIM: Статусът е възстановен")
            elif using_wifi:
                if sim_available:
                    print("SIM: Работи отново, превключване обратно от WiFi към SIM...")
                    wifi.disconnect()
                    using_wifi = False
                    using_sim = True
                    sim_failure_count = 0
                    print("SIM: Превключен обратно към основен режим")
                else:
                    if not wifi_connected:
                        print("WiFi: Връзката е прекъсната, преподключване...")
                        if wifi.connect():
                            wifi_connected, wifi_ip, wifi_rssi, wifi_ssid = wifi.get_status()
                            if wifi_connected:
                                print("WiFi: Преподключен успешно")

        if uptime - last_gps >= config.GPS_READ_EVERY_S:
            last_gps = uptime
            new_lat, new_lon = sim.gps_read()
            if new_lat is not None and new_lon is not None:
                lat, lon = new_lat, new_lon
        
        if uptime - last_ota_check >= config.OTA_CHECK_INTERVAL_S:
            last_ota_check = uptime
            if (using_wifi and wifi_connected) or (using_sim and sim_available):
                files_updated, needs_restart = ota_updater.check_and_update()
                if needs_restart:
                    print("OTA: Рестартиране за прилагане на обновленията...")
                    time.sleep(2)
                    import machine
                    machine.reset()
        
        if uptime - last_speed_test >= config.SPEED_TEST_INTERVAL_S:
            last_speed_test = uptime
            if using_wifi and wifi_connected:
                print("Тест на скорост: Тестване на WiFi връзка...")
                result = speed_test.quick_test(include_upload=True)
                internet_speed_kbps = result['download_kbps']
                internet_upload_kbps = result['upload_kbps']
                internet_ping_ms = result['ping_ms']
                bytes_received = result['bytes_received']
                bytes_sent = result.get('bytes_sent', 0)
                if internet_speed_kbps:
                    upload_str = "{} Kbps".format(internet_upload_kbps) if internet_upload_kbps else "Н/Д"
                    print("Тест на скорост: Изтегляне:", internet_speed_kbps, "Kbps | Качване:", upload_str, "| Ping:", internet_ping_ms, "ms")
                    if hasattr(wifi, 'update_traffic'):
                        wifi.update_traffic(bytes_sent=bytes_sent, bytes_received=bytes_received)
                else:
                    print("Тест на скорост: Неуспешен")
            elif using_sim and sim_available:
                print("Тест на скорост: Тестване на SIM връзка...")
                result = speed_test.quick_test(include_upload=True)
                internet_speed_kbps = result['download_kbps']
                internet_upload_kbps = result['upload_kbps']
                internet_ping_ms = result['ping_ms']
                bytes_received = result['bytes_received']
                bytes_sent = result.get('bytes_sent', 0)
                if internet_speed_kbps:
                    upload_str = "{} Kbps".format(internet_upload_kbps) if internet_upload_kbps else "Н/Д"
                    print("Тест на скорост: Изтегляне:", internet_speed_kbps, "Kbps | Качване:", upload_str, "| Ping:", internet_ping_ms, "ms")
                    if hasattr(sim, 'update_traffic'):
                        sim.update_traffic(bytes_sent=bytes_sent, bytes_received=bytes_received)
                else:
                    print("Тест на скорост: Неуспешен")
        
        try:
            if using_wifi:
                if hasattr(wifi, 'get_traffic_stats'):
                    bytes_sent, bytes_received, total_bytes = wifi.get_traffic_stats()
                else:
                    bytes_sent, bytes_received, total_bytes = 0, 0, 0
            elif using_sim:
                if hasattr(sim, 'get_traffic_stats'):
                    bytes_sent, bytes_received, total_bytes = sim.get_traffic_stats()
                else:
                    bytes_sent, bytes_received, total_bytes = 0, 0, 0
            else:
                bytes_sent, bytes_received, total_bytes = 0, 0, 0
        except Exception as e:
            print("Грешка при статистика за трафик:", e)
            bytes_sent, bytes_received, total_bytes = 0, 0, 0

        print("=" * 45)
        print("IoT Станция:", config.DEVICE_NAME, "| Работно време:", uptime, "с")

        if t is None or h is None:
            print("DHT22: НЯМА ДАННИ")
        else:
            print("DHT22:", t, "°C |", h, "%")

        print("MQ-2: сурово =", mq)

        if pm25 is None or pm10 is None:
            print("SDS011: изчакване на данни...")
        else:
            print("SDS011: PM2.5 =", pm25, "ug/m3 | PM10 =", pm10, "ug/m3")

        print(
            "SIM7600: UART =",
            ("ОК" if sim_ok else "НЕ"),
            "| SIM =",
            ("ДА" if sim_present else "НЕ"),
            "| RSSI =",
            sim_rssi
        )

        if lat is None or lon is None:
            print("GPS: все още няма фикс")
        else:
            print("GPS:", lat, ",", lon)
        
        if using_sim:
            wifi_status = "Наличен" if wifi_connected else "Недостъпен"
            print("КОМУНИКАЦИЯ: SIM ОСНОВЕН | WiFi:", wifi_status, "(резервен)")
        elif using_wifi:
            if wifi_connected:
                sim_status = "НЕРАБОТИ" if not (sim_ok and sim_present) else "ОК"
                print("КОМУНИКАЦИЯ: WiFi РЕЗЕРВЕН | IP:", wifi_ip if wifi_ip else "Н/Д", "| SIM:", sim_status, "(основен недостъпен)")
            else:
                print("КОМУНИКАЦИЯ: WiFi СВЪРЗВАНЕ...")
        else:
            print("КОМУНИКАЦИЯ: Няма налична връзка")
        
        if internet_speed_kbps is not None:
            download_str = "{:.2f} Kbps".format(internet_speed_kbps)
            upload_str = "{:.2f} Kbps".format(internet_upload_kbps) if internet_upload_kbps else "Н/Д"
            ping_str = "{} ms".format(internet_ping_ms) if internet_ping_ms else "Н/Д"
            print("СКОРОСТ: Изтегляне:", download_str, "| Качване:", upload_str, "| Ping:", ping_str)
        else:
            print("СКОРОСТ: Все още не е тествана")
        
        if total_bytes > 0:
            if total_bytes < 1024:
                traffic_str = "{} B".format(total_bytes)
            elif total_bytes < 1024 * 1024:
                traffic_str = "{:.2f} KB".format(total_bytes / 1024.0)
            else:
                traffic_str = "{:.2f} MB".format(total_bytes / (1024.0 * 1024.0))
            
            sent_str = "{} B".format(bytes_sent) if bytes_sent < 1024 else "{:.2f} KB".format(bytes_sent / 1024.0)
            recv_str = "{} B".format(bytes_received) if bytes_received < 1024 else "{:.2f} KB".format(bytes_received / 1024.0)
            print("ТРАФИК: Изпратено:", sent_str, "| Получено:", recv_str, "| Общо:", traffic_str)
        else:
            print("ТРАФИК: Няма данни")
        
        if config.OTA_ENABLED:
            ota_status = ota_updater.get_status()
            next_check_str = "{} с".format(ota_status['next_check_in']) if ota_status['next_check_in'] > 0 else "сега"
            print("OTA: Активен | Следваща проверка след:", next_check_str)
        else:
            print("OTA: Деактивиран")

        time.sleep(config.MAIN_PERIOD_S)


if __name__ == "__main__":
    main()