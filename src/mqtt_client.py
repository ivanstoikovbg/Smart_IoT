import time
import socket
import ujson
import config


class MQTTClient:

    def __init__(self, 
                 client_id=None,
                 server=None,
                 port=1883,
                 user=None,
                 password=None,
                 keepalive=60,
                 ssl=False,
                 ssl_params=None):

        self._client_id = client_id or config.DEVICE_NAME
        self._server = server or config.MQTT_BROKER_HOST
        self._port = port or config.MQTT_BROKER_PORT
        self._user = user or config.MQTT_USER if hasattr(config, 'MQTT_USER') else None
        self._password = password or config.MQTT_PASSWORD if hasattr(config, 'MQTT_PASSWORD') else None
        self._keepalive = keepalive
        self._ssl = ssl or (hasattr(config, 'MQTT_USE_SSL') and config.MQTT_USE_SSL)
        self._ssl_params = ssl_params
        
        self._sock = None
        self._connected = False
        self._last_ping = 0
        self._msg_id = 1
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
        self._reconnect_delay = 5 
        
    def _connect_socket(self):
        try:
            addr = socket.getaddrinfo(self._server, self._port)[0][-1]
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(10) 
            self._sock.connect(addr)
            
            if self._ssl:
                try:
                    import ussl
                    protocol = getattr(ussl, 'PROTOCOL_TLS_CLIENT', 0)
                    ssl_context = ussl.SSLContext(protocol)
                    
                    cert_none = getattr(ussl, 'CERT_NONE', 0)
                    try:
                        ssl_context.verify_mode = cert_none
                    except:
                        try:
                            ssl_context.__dict__['verify_mode'] = cert_none
                        except:
                            try:
                                object.__setattr__(ssl_context, 'verify_mode', cert_none)
                            except:
                                pass
                    
                    try:
                        self._sock = ssl_context.wrap_socket(self._sock, self._server)
                    except (TypeError, ValueError) as e:
                        error_msg = str(e).lower()
                        if "keyword" in error_msg or "argument" in error_msg:
                            self._sock = ssl_context.wrap_socket(self._sock)
                        else:
                            raise
                except ImportError:
                    print("MQTT: SSL не е поддържан, използване на TCP")
                    self._ssl = False
                except Exception as e:
                    print("MQTT: SSL грешка:", e)
                    if self._sock:
                        self._sock.close()
                    self._sock = None
                    return False
            
            return True
        except Exception as e:
            print("MQTT: Грешка при свързване на сокет:", e)
            if self._sock:
                try:
                    self._sock.close()
                except:
                    pass
                self._sock = None
            return False
    
    def _send_bytes(self, data):
        if not self._sock:
            return False
        try:
            self._sock.send(data)
            return True
        except Exception as e:
            print("MQTT: Грешка при изпращане:", e)
            self._connected = False
            return False
    
    def _recv_bytes(self, length):
        if not self._sock:
            return None
        try:
            return self._sock.recv(length)
        except socket.timeout:
            return None
        except Exception as e:
            print("MQTT: Грешка при получаване:", e)
            self._connected = False
            return None
    
    def _pack_string(self, s):
        s_bytes = s.encode('utf-8') if isinstance(s, str) else s
        return bytes([len(s_bytes) >> 8, len(s_bytes) & 0xFF]) + s_bytes
    
    def _unpack_string(self, data, offset):
        length = (data[offset] << 8) | data[offset + 1]
        offset += 2
        return data[offset:offset + length].decode('utf-8'), offset + length
    
    def connect(self, clean_session=True):
        if self._connected:
            return True
        
        if not self._connect_socket():
            return False
        
        protocol_name = "MQTT"
        protocol_level = 4 
        
        connect_flags = 0x02 if clean_session else 0x00
        if self._user:
            connect_flags |= 0x80
        if self._password:
            connect_flags |= 0x40
        
        variable_header = (
            self._pack_string(protocol_name) +
            bytes([protocol_level]) +
            bytes([connect_flags]) +
            bytes([self._keepalive >> 8, self._keepalive & 0xFF])
        )
        
        payload = self._pack_string(self._client_id)
        if self._user:
            payload += self._pack_string(self._user)
        if self._password:
            payload += self._pack_string(self._password)
        
        remaining_length = len(variable_header) + len(payload)
        remaining_bytes = []
        x = remaining_length
        while x > 0:
            encoded_byte = x % 128
            x = x // 128
            if x > 0:
                encoded_byte |= 0x80
            remaining_bytes.append(encoded_byte)
        if not remaining_bytes:
            remaining_bytes = [0]

        connect_packet = (
            bytes([0x10]) +  
            bytes(remaining_bytes) +
            variable_header +
            payload
        )
        
        if not self._send_bytes(connect_packet):
            return False

        try:
            response = self._recv_bytes(4)
            if not response or len(response) < 4:
                print("MQTT: Невалиден CONNACK отговор")
                return False
            
            if response[0] != 0x20:  
                print("MQTT: Очакван CONNACK, получен:", hex(response[0]))
                return False
            
            return_code = response[3]
            if return_code != 0:
                print("MQTT: CONNACK грешка:", return_code)
                return False
            
            self._connected = True
            self._reconnect_attempts = 0
            self._last_ping = time.ticks_ms()
            print("MQTT: Свързан успешно към", self._server, ":", self._port)
            return True
            
        except Exception as e:
            print("MQTT: Грешка при четене на CONNACK:", e)
            return False
    
    def disconnect(self):
        if self._connected and self._sock:
            try:
                disconnect_packet = bytes([0xE0, 0x00])  
                self._send_bytes(disconnect_packet)
            except:
                pass
        
        self._connected = False
        if self._sock:
            try:
                self._sock.close()
            except:
                pass
            self._sock = None
        print("MQTT: Прекъсната връзка")
    
    def publish(self, topic, payload, qos=0, retain=False):

        if not self._connected:
            if not self.connect():
                return False
        
        if isinstance(payload, (dict, list)):
            try:
                payload = ujson.dumps(payload)
            except Exception as e:
                print("MQTT: Грешка при JSON кодиране:", e)
                return False
        
        if isinstance(payload, str):
            payload_bytes = payload.encode('utf-8')
        else:
            payload_bytes = payload
        
        fixed_header = 0x30  
        if qos > 0:
            fixed_header |= (qos << 1)
        if retain:
            fixed_header |= 0x01
        
        variable_header = self._pack_string(topic)
        if qos > 0:
            msg_id = self._msg_id
            self._msg_id = (self._msg_id % 65535) + 1
            variable_header += bytes([msg_id >> 8, msg_id & 0xFF])
        
        remaining_length = len(variable_header) + len(payload_bytes)
        remaining_bytes = []
        x = remaining_length
        while x > 0:
            encoded_byte = x % 128
            x = x // 128
            if x > 0:
                encoded_byte |= 0x80
            remaining_bytes.append(encoded_byte)
        if not remaining_bytes:
            remaining_bytes = [0]
        
        publish_packet = (
            bytes([fixed_header]) +
            bytes(remaining_bytes) +
            variable_header +
            payload_bytes
        )
        
        if not self._send_bytes(publish_packet):
            self._connected = False
            return False
        
        if qos == 1:
            try:
                response = self._recv_bytes(4)
                if response and len(response) >= 4 and response[0] == 0x40:  
                    return True
                else:
                    print("MQTT: Неочакван отговор при QoS 1")
                    return False
            except:
                return False
        
        return True
    
    def ping(self):
        if not self._connected:
            return False
        
        ping_packet = bytes([0xC0, 0x00])  
        if not self._send_bytes(ping_packet):
            self._connected = False
            return False

        try:
            response = self._recv_bytes(2)
            if response and len(response) >= 2 and response[0] == 0xD0:  
                self._last_ping = time.ticks_ms()
                return True
            else:
                self._connected = False
                return False
        except:
            self._connected = False
            return False
    
    def check_connection(self):
        if not self._connected:
            return False
        
        current_time = time.ticks_ms()
        ping_interval_ms = (self._keepalive * 1000) // 2  
        
        if time.ticks_diff(current_time, self._last_ping) >= ping_interval_ms:
            if not self.ping():
                print("MQTT: Ping неуспешен, опит за преподключване...")
                self._connected = False
                return False
        
        return True
    
    def reconnect(self):
        self.disconnect()
        
        if self._reconnect_attempts >= self._max_reconnect_attempts:
            print("MQTT: Достигнат максимален брой опити за преподключване")
            return False
        
        self._reconnect_attempts += 1
        print("MQTT: Опит за преподключване", self._reconnect_attempts, "/", self._max_reconnect_attempts)
        time.sleep(self._reconnect_delay)
        
        return self.connect()
    
    def is_connected(self):
        return self._connected and self._sock is not None
    
    def publish_sensor_data(self, topic_prefix, device_id, sensors_data):
        
        if not self.check_connection():
            if not self.reconnect():
                return False
        
        topic = "{}/{}".format(topic_prefix, device_id)
        
        return self.publish(topic, sensors_data, qos=1, retain=False)

