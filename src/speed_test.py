import socket
import time
import config


class SpeedTest:
    
    def __init__(self, test_url=config.SPEED_TEST_URL, timeout_s=config.SPEED_TEST_TIMEOUT_S):
        self._test_url = test_url
        self._timeout_s = timeout_s
    
    def _parse_url(self, url):
        if url.startswith("http://"):
            url = url[7:]
        elif url.startswith("https://"):
            url = url[8:]
        
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
            port = 80
        
        return host, path, port
    
    def test_download_speed(self):
        try:
            host, path, port = self._parse_url(self._test_url)
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self._timeout_s)
            
            start_time = time.ticks_ms()
            sock.connect((host, port))
            
            request = "GET {} HTTP/1.1\r\nHost: {}\r\nConnection: close\r\n\r\n".format(path, host)
            sock.send(request.encode())
            
            bytes_received = 0
            chunk_size = 1024
            
            while True:
                try:
                    chunk = sock.recv(chunk_size)
                    if not chunk:
                        break
                    bytes_received += len(chunk)
                except socket.timeout:
                    break
                except Exception:
                    break
            
            end_time = time.ticks_ms()
            duration_ms = time.ticks_diff(end_time, start_time)
            sock.close()
            
            if bytes_received > 0 and duration_ms > 0:
                # Изчисляване на скоростта в Kbps
                speed_kbps = (bytes_received * 8) / (duration_ms / 1000.0) / 1024.0
                return round(speed_kbps, 2), bytes_received, duration_ms
            else:
                return None, 0, 0
                
        except Exception as e:
            return None, 0, 0
    
    def test_upload_speed(self, data_size_kb=10):
        try:
            host, path, port = self._parse_url(self._test_url)
            
            test_data = b"X" * (data_size_kb * 1024)
            bytes_sent = len(test_data)
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self._timeout_s)
            
            start_time = time.ticks_ms()
            sock.connect((host, port))
            
            content_length = len(test_data)
            request = "POST {} HTTP/1.1\r\nHost: {}\r\nContent-Length: {}\r\nConnection: close\r\n\r\n".format(
                path, host, content_length
            )
            sock.send(request.encode())
            sock.send(test_data)
            
            try:
                response = sock.recv(1024)
            except:
                pass
            
            end_time = time.ticks_ms()
            duration_ms = time.ticks_diff(end_time, start_time)
            sock.close()
            
            if bytes_sent > 0 and duration_ms > 0:
                # Изчисляване на скоростта в Kbps
                speed_kbps = (bytes_sent * 8) / (duration_ms / 1000.0) / 1024.0
                return round(speed_kbps, 2), bytes_sent, duration_ms
            else:
                return None, 0, 0
                
        except Exception as e:
            return None, 0, 0
    
    def test_ping(self, host=None):
        try:
            if host is None:
                host, _, port = self._parse_url(self._test_url)
            else:
                _, _, port = self._parse_url(self._test_url)
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self._timeout_s)
            
            start_time = time.ticks_ms()
            sock.connect((host, port))
            end_time = time.ticks_ms()
            
            latency = time.ticks_diff(end_time, start_time)
            sock.close()
            
            return latency
            
        except Exception:
            return None
    
    def quick_test(self, include_upload=True):
        result = {
            'ping_ms': None,
            'download_kbps': None,
            'upload_kbps': None,
            'bytes_received': 0,
            'bytes_sent': 0,
            'duration_ms': 0
        }
        
        ping = self.test_ping()
        result['ping_ms'] = ping
        
        speed, bytes_received, duration = self.test_download_speed()
        result['download_kbps'] = speed
        result['bytes_received'] = bytes_received
        result['duration_ms'] = duration
        
        if include_upload:
            upload_speed, bytes_sent, upload_duration = self.test_upload_speed(data_size_kb=5)
            result['upload_kbps'] = upload_speed
            result['bytes_sent'] = bytes_sent
        
        return result