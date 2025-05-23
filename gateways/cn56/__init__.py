from flask import redirect, url_for

from src.lib.gateway import BaseGateway
from src.lib.config import Config
from src.lib.reader import BaseReader
from src.lib.action import ActionButton, Action
from src.configs import Configs

import os
import socket
import time
import threading
import traceback

# This was made to match the actual CV56 API, but it could be simplified
class Protocol:

    def __init__(self):
        self.seq_sub_num = 0x0
    
    def initial(self):
        self.checksum = 0x0
        self.seq_num = 0x0
        self.address = 0x0
        self.n_bytes_to_write = 0
        self.n_bytes_read = self.n_bytes_to_write
    
    def add_start(self, device_address, new_seq_num):
        data = [0x2]

        if new_seq_num:
            self.seq_num = 0x80
            self.seq_sub_num = self.seq_sub_num & 7
            self.seq_num = self.seq_sub_num << 4 | self.seq_num
            self.seq_sub_num += 0x1
            self.seq_num = self.seq_num | (device_address >> 8) & 0xf
        
        data += [self.seq_num]
        self.checksum = self.seq_num
        n_bytes_to_write = 2
        self.add_data(device_address, data)

        return data
    
    def add_data(self, data_in, data_out):
        data_out += [data_in]
        self.checksum ^= data_in
        self.n_bytes_to_write += 1
    
    def add_end(self, data):
        self.add_data(self.checksum, data)
        data += [0x03]
        self.n_bytes_to_write += 1

    def encode_reader(self, device_address, cmd_code, cmd_time, cmd_data):
        self.initial()
        data = self.add_start(device_address, True)
        if cmd_code == 0x06:
            print("This is a not supported (code = 0x06)")
            exit(1)
        
        self.add_data(cmd_code, data)
        self.add_data(len(cmd_data) + 1, data)
        self.add_data(cmd_time, data)
        for d in cmd_data:
            self.add_data(d, data)
        
        self.add_end(data)

        return data

class ReaderSock(socket.socket):

    instance = None

    def __new__(cls, addr):
        if not ReaderSock.instance:
            ReaderSock.instance = super(ReaderSock, cls).__new__(cls, addr)
            ReaderSock.instance.binded = False
        return ReaderSock.instance
    
    def __init__(self, addr):
        if self.binded: return
        self.binded = True
        
        super().__init__(socket.AF_INET, socket.SOCK_DGRAM)
        self.addr = addr
        self.messages = {}
        self.locks: dict[tuple, threading.Lock] = {}

        self.bind(addr)

        threading.Thread(target=self.recv_thread, daemon=True).start()

    def recv_thread(self):
        while True:
            data, addr = self.recvfrom(1024)
            print(f"-> {addr} ({len(data)})")
            self.messages[addr] = self.messages.get(addr, []) + [data]
            if self.get_lock(addr).locked():
                self.get_lock(addr).release()

    def get_lock(self, addr):
        if addr not in self.locks:
            self.locks[addr] = threading.Lock()
            self.locks[addr].acquire()
        return self.locks[addr]
    
    def recv_from(self, addr, blocking = True):
        if not blocking and (addr not in self.locks or self.locks.get(addr).locked()):
            return None
        acquired = self.get_lock(addr).acquire(blocking=blocking, timeout=5 if blocking else -1)
        if not acquired:
            if not blocking:
                return None
            raise TimeoutError
        addr_messages = self.messages.get(addr, [])
        msg = addr_messages.pop(0)
        self.get_lock(addr).release()
        if len(addr_messages) < 1:
            self.get_lock(addr).acquire()
        return msg

class Reader(BaseReader):
    device_address: int = 0
    ip: str
    can_write: bool = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.protocol = Protocol()
        self.recv_lock = threading.Lock()
        self.is_online = False
        self.port = 2000
        self.src_port = 2000 + self.reader.id
    
    def send_data(self, data):
        try:
            self.sock.sendto(bytes(data), (self.ip, self.port))
            # print(bytes(data).hex(" "))
        except Exception as e:
            print(f"Cannot send {len(data)} bytes to {self.ip}:{self.port} ", e)
            raise e

    def receive_data(self, blocking = True):
        data = None
        try:
            data = self.sock.recv_from((self.ip, self.port), blocking)
            if blocking: # Non-blocking doesnt timeout, so we can't check if alive
                self.is_online = True
        except TimeoutError:
            print("Timeout")
            self.is_online = False
        except Exception as e:
            print(e, type(e))
            traceback.print_exc()
        return data

    def send_and_receive(self, data):
        self.recv_lock.acquire()
        try: self.send_data(data)
        except Exception as e:
            self.is_online = False
            self.recv_lock.release()
            raise e
        data = self.receive_data()
        self.recv_lock.release()
        return data

    def send_cmd(self, device_address, cmd_code, cmd_time, cmd_data):
        data = self.protocol.encode_reader(device_address, cmd_code, cmd_time, cmd_data)
        # print(data)
        recv = self.send_and_receive(data)
        # if recv:
        #     print(recv.hex(" "))
        time.sleep(0.1) # Seems like race conditions are a thing on CN56 readers
        return recv

    def keep_alive(self):
        while True:
            time.sleep(10)
            if not self.running: return
            self.do_some_magic()

    def run(self): # TCPRun
        print(f"Connecting from 172.25.50.124:{self.port} to {self.ip}:{self.port}")
        self.sock = ReaderSock(("172.25.50.124", self.port))
        self.running = True
        threading.Thread(target=self.keep_alive, daemon=True).start()
        print("Connected")

    def disconnect(self):
        # self.sock.close()
        # self.sock = None
        self.running = False

    def do_some_magic(self):
        # Activate AutoRead w/ Wiegand
        return self.send_cmd(self.device_address, 0x18, 0, [0, 7, 38, 16, 85, 170, 1, 6, 0, 2, 0, 0, 0])

    def start_led(self, color): # green: 0x02 red: 0x01
        return self.send_cmd(self.device_address, 0x24, 0, [color])

    def open_relay(self):
        return self.send_cmd(self.device_address, 0x29, 0, [0x05])

    def get_uid(self, msg):
        return msg[5:-2].hex()

    def passive_targets(self):
        return self.send_cmd(self.device_address, 0x3d, 0, [0x00, 0x02, 0x00])

    def select_target(self):
        return self.send_cmd(self.device_address, 0x3e, 0, [0x01])

    def select_application(self, aid):
        return self.send_cmd(self.device_address, 0xab, 0, [0x1] + [i for i in aid.to_bytes(3, "little")])

    def authenticate(self, crypto_type, key): # crypto_type -> 3DES: 0x0 AES: 0x2
        return self.send_cmd(self.device_address, 0xa3, 0, [0x1, crypto_type, 0x0] + key)

    def change_key(self, crypto_type, new_key, old_key): # crypto_type -> 3DES: 0x0 AES: 0x2
        return self.send_cmd(self.device_address, 0xa6, 0, [0x1, 0x0, crypto_type, 0x0] + new_key + [0] * (0x18 - len(new_key)) + old_key + [0] * (0x18 - len(old_key)))

    def create_application(self, aid):
        #                                                        V -- V  This should also be aid using [i for i in aid.to_bytes(3, "little")]
        return self.send_cmd(self.device_address, 0xa8, 0, [0x1, aid, 0x0, 0x0, 0xf, 0x3, 0x2])

    def create_data_file(self, file_id):
        return self.send_cmd(self.device_address, 0xb4, 0, [0x1, file_id, 0x0, 0x3, 0x0, 0x0, 0x80, 0x0, 0x0])

    def write_data(self, file_id, data):
        return self.send_cmd(self.device_address, 0xb9, 0, [0x1, file_id, 0x3, 0x0, 0x0, 0x0] + [i for i in len(data).to_bytes(3, "little")] + data)

    def file_setting(self, aid):
        return self.send_cmd(self.device_address, 0xc4, 0, [i for i in aid.to_bytes(3, "little")] + [0x0, 0x0, 0x0, 0x3, 0x0, 0x0, 0x0, 0x10, 0x0, 0x0, 0x0, 0x0, 0x0])

    def key_setting(self, key):
        return self.send_cmd(self.device_address, 0xc3, 0, [0x0, 0x02] + key + [0] * (0x18 - len(key)))
    
    def bip_bip(self, values):
        return self.send_cmd(self.device_address, 0x26, 0, [4] + values)
    
    def opened_door_buzzer(self):
        self.bip_bip([1, 0, 0, 0, 2])

    def get_target(self):
        i = 0
        while True:
            targets = self.passive_targets()
            target = targets[11:18].hex()

            if target:
                self.start_led(2)
                return target

            self.start_led((i%2) + 1)
            i+=1

class Gateway(BaseGateway):
    uid = "cn56-gateway"
    name = "CN56 Gateway"
    reader_class = Reader

    class Config:
        key: str = "00" * 16
    
    class Actions:        
        @ActionButton("Say Hello")
        def hello_world(gateway, reader):
            print(f"Hello {reader.name}")
            reader_instance = Gateway.get_reader_instance(reader.id)
            reader_instance.start_led(0x01)
            time.sleep(1)
            reader_instance.start_led(0x02)
            time.sleep(1)
            reader_instance.start_led(0x00)
            reader_instance.do_some_magic()
        
        @ActionButton("Write Card")
        def write_card(gateway, reader):
            if not reader.gateway_configs.get("can_write"):
                return "This reader is not writable"
            return redirect(url_for("cn56.write", reader_id=reader.id))

        @Action()
        def write_badge_to_card(gateway, reader_id, badge_uid): 
            # TODO: Verify every actions response
            reader_instance = Gateway.get_reader_instance(reader_id)
            default_key = [0] * 16

            hex_to_byte_list = lambda hex_data: [int(hex_data[i:i+2], 16) for i in range(0, len(hex_data), 2)]
            
            key = hex_to_byte_list(Configs.get_gateway_var(Gateway.uid, "key"))

            target = reader_instance.get_target()
            print("Target:", target)

            reader_instance.select_target()
            reader_instance.select_application(0)
            reader_instance.authenticate(0, default_key)
            reader_instance.change_key(2, key, default_key)
            reader_instance.authenticate(2, key)
            reader_instance.create_application(1)
            reader_instance.select_application(1)
            reader_instance.authenticate(2, default_key)
            reader_instance.change_key(2, key, default_key)
            reader_instance.authenticate(2, key)
            reader_instance.create_data_file(0)
            reader_instance.write_data(0, hex_to_byte_list(badge_uid))
            reader_instance.start_led(0)
            reader_instance.do_some_magic()

    @staticmethod
    def connect(reader: Reader):
        print("CONNECT", reader.ip)
        if not reader.ip:
            return False

        hex_to_byte_list = lambda hex_data: [int(hex_data[i:i+2], 16) for i in range(0, len(hex_data), 2)]
        
        try:
            reader.run()
            reader.start_led(0x01)
            reader.do_some_magic()
            reader.file_setting(1)
            reader.key_setting(hex_to_byte_list(Gateway.get_var("key")))
            reader.start_led(0x02)
            reader.start_led(0x00)
            reader.do_some_magic()
        except Exception as e:
            print("Cannot connect to the reader")
            print(e)
            traceback.print_exc()
            return False
        
        print("[ + ] Connected to reader")

        return True
    
    @staticmethod
    def disconnect(reader: Reader):
        print("DISCONNECT")
        if not reader.ip:
            return
        reader.disconnect()

    @staticmethod
    def job(reader: Reader, on_badge):
        if not reader.ip:
            return
        while reader.running:
            time.sleep(0.1)

            if reader.recv_lock.locked(): continue
            
            try:
                data = reader.receive_data(False)
            except Exception as e: 
                print("Cannot Read Data:", e)
                continue # No data

            if not data: continue

            print(data)
            badge_uid = reader.get_uid(data)
            print("UID:", badge_uid)

            if len(badge_uid) == 32:
                on_badge(badge_uid)

            reader.do_some_magic()
    
    @staticmethod
    def event(reader, authorized, badge_uid):
        if authorized:
            reader.open_relay()
        #     reader.bip_bip([1, 10, 0, 0, 1])
        else:
            reader.bip_bip([1, 1, 0, 0, 2])
        reader.start_led([0x01, 0x02][int(authorized)])
        time.sleep(5)
        reader.start_led(0x0)
        reader.do_some_magic()