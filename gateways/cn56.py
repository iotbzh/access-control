from src.lib.gateway import BaseGateway
from src.lib.config import Config
from src.lib.reader import BaseReader

import os
import socket
import time

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

# TODO: Add keep alive, it seems to stop working after something

class Reader(BaseReader):
    device_address: int = 0
    ip: str

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.protocol = Protocol()
    
    def send_data(self, device_address, data): # device_address is unused in the lib idk why
        self.sock.sendto(bytes(data), (self.ip, 2000))
        print(bytes(data).hex(" "))

    def receive_data(self, device_address): 
        data, _ = self.sock.recvfrom(1024)
        return data

    def send_and_receive(self, device_address, data):
        self.send_data(device_address, data)
        return self.receive_data(device_address)

    def send_cmd(self, device_address, cmd_code, cmd_time, cmd_data):
        data = self.protocol.encode_reader(device_address, cmd_code, cmd_time, cmd_data)
        print(data)
        recv = self.send_and_receive(device_address, data)
        print(recv.hex(" "))
        return recv

    def run(self): # TCPRun
        print(self.ip)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("172.25.50.124", 2000))

    def do_some_magic(self):
        # Activate AutoRead w/ Wiegand
        return self.send_cmd(self.device_address, 0x18, 0, [0, 7, 38, 16, 85, 170, 1, 6, 0, 2, 0, 0, 0])

    def start_led(self, color): # green: 0x02 red: 0x01
        return self.send_cmd(self.device_address, 0x24, 0, [color])

    def get_uid(self, msg):
        return msg[5:-2].hex()

class Gateway(BaseGateway):
    name = "CN56 Gateway"
    uid = "cn56-gateway"
    reader_class = Reader

    configs = [
        Config("Key", str, "00" * 16), # Make it more secure...
    ]

    @staticmethod
    def connect(reader: Reader):
        if not reader.ip:
            return
        reader.run()
        reader.do_some_magic()

    @staticmethod
    def job(reader: Reader, on_badge):
        if not reader.ip:
            return
        while True:
            data = reader.receive_data(0)
            print(data)

            badge_uid = reader.get_uid(data)
            print("UID:", badge_uid)
            on_badge(badge_uid)

            reader.do_some_magic() # idk why but i need to do some magic each time
    
    @staticmethod
    def action(reader, authorized, badge_uid):
        reader.start_led([0x01, 0x02][int(authorized)])
        time.sleep(5)
        reader.start_led(0x0)
        reader.do_some_magic()