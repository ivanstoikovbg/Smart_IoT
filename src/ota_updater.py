import socket
import time
import uhashlib
import uos
import config


class OTAUpdater:
    def __init__(self, base_url=config.OTA_BASE_URL, files_to_update=config.OTA_FILES_TO_UPDATE):
        self._base_url = base_url
        self._files_to_update = files_to_update
        self._last_check = 0
        self._update_info_file = "ota_versions.txt"
    
    def _get_file_hash(self, filepath):
        try:
            with open(filepath, 'rb') as f:
                sha256 = uhashlib.sha256()
                while True:
                    chunk = f.read(512)
                    if not chunk:
                        break
                    sha256.update(chunk)
                return sha256.digest().hex()
        except Exception:
            return None
    
    def _download_file(self, url, timeout_s=10):
        try:
            is_https = url.startswith("https://")
            if is_https:
                url = url[8:]
            elif url.startswith("http://"):
                url = url[7:]
            
            if "/" in url:
                host, path = url.split("/", 1)
                path = "/" + path
            else:
                host = url
                path = "/"
            
            if ":" in host:
                host, port = host.split(":")
                port = int(port)
            else:
                if is_https:
                    port = 443
                else:
                    port = 80
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout_s)
            
            sock.connect((host, port))
            
            if is_https:
                try:
                    import ussl
                    sock = ussl.wrap_socket(sock)
                except ImportError:
                    print("OTA: SSL не е поддържан, използване на HTTP")
                    return None
            
            request = "GET {} HTTP/1.1\r\nHost: {}\r\nConnection: close\r\n\r\n".format(path, host)
            sock.send(request.encode())
            
            response = b""
            headers_done = False
            
            while True:
                try:
                    chunk = sock.recv(1024)
                    if not chunk:
                        break
                    
                    if not headers_done:
                        response += chunk
                        if b"\r\n\r\n" in response:
                            header_end = response.find(b"\r\n\r\n")
                            headers = response[:header_end].decode('utf-8', 'ignore')
                            body = response[header_end + 4:]
                            
                            if "200 OK" in headers:
                                response = body
                                headers_done = True
                            else:
                                sock.close()
                                return None
                        else:
                            continue
                    else:
                        response += chunk
                        
                except socket.timeout:
                    break
                except Exception:
                    break
            
            sock.close()
            
            if headers_done:
                return response
            else:
                return None
                
        except Exception as e:
            print("OTA: Грешка при изтегляне:", e)
            return None
    
    def _get_remote_file_hash(self, filepath):
        url = "{}/{}".format(self._base_url, filepath)
        content = self._download_file(url)
        
        if content:
            sha256 = uhashlib.sha256()
            sha256.update(content)
            return sha256.digest().hex()
        return None
    
    def _update_file(self, filepath):
        try:
            local_hash = self._get_file_hash(filepath)
            remote_hash = self._get_remote_file_hash(filepath)
            
            if remote_hash is None:
                print("OTA: Не може да се изтегли", filepath)
                return False
            
            if local_hash == remote_hash:
                return False
            
            print("OTA: Обновяване на", filepath, "...")
            url = "{}/{}".format(self._base_url, filepath)
            content = self._download_file(url)
            
            if content is None:
                print("OTA: Неуспешно изтегляне на", filepath)
                return False
            
            try:
                with open(filepath, 'wb') as f:
                    f.write(content)
                print("OTA: Успешно обновен", filepath)
                return True
            except Exception as e:
                print("OTA: Грешка при запис на", filepath, ":", e)
                return False
                
        except Exception as e:
            print("OTA: Грешка при обновяване на", filepath, ":", e)
            return False
    
    def check_and_update(self, force_check=False):
        current_time = time.ticks_ms() // 1000
        
        if not force_check:
            if current_time - self._last_check < config.OTA_CHECK_INTERVAL_S:
                return 0, False
        
        self._last_check = current_time
        
        if not config.OTA_ENABLED:
            return 0, False
        
        print("OTA: Проверка за обновления...")
        
        files_updated = 0
        needs_restart = False
        
        for filepath in self._files_to_update:
            if self._update_file(filepath):
                files_updated += 1
                needs_restart = True
        
        if files_updated > 0:
            print("OTA: Обновени", files_updated, "файла")
            print("OTA: Необходим е рестарт за да се приложат промените")
        else:
            print("OTA: Няма нови обновления")
        
        return files_updated, needs_restart
    
    def get_status(self):
        current_time = time.ticks_ms() // 1000
        next_check = config.OTA_CHECK_INTERVAL_S - (current_time - self._last_check)
        if next_check < 0:
            next_check = 0
        
        return {
            'enabled': config.OTA_ENABLED,
            'last_check': self._last_check,
            'next_check_in': next_check
        }

