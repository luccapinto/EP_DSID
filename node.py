import socket
import threading
import random
import logging
import sys
import os
import time

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class Node:
    def __init__(self, ip, port, neighbors_file=None, key_value_file=None):
        self.ip = ip
        self.port = port
        self.neighbors = []
        self.key_value_store = {}
        self.load_topology(neighbors_file)
        self.load_key_values(key_value_file)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.ip, self.port))
        self.server_socket.listen(5)
        self.running = True
        self.ttl_default = 100
        self.message_seen = set()
        self.lock = threading.Lock()
        self.stats = {
            "flooding": 0,
            "random_walk": 0,
            "depth_first": 0,
            "flooding_hops": 0,
            "random_walk_hops": 0,
            "depth_first_hops": 0
        }
        print(f"Node running at {self.ip}:{self.port}")
        self.connect_to_neighbors()

    def load_topology(self, neighbors_file):
        if neighbors_file:
            with open(neighbors_file, 'r') as f:
                for line in f:
                    neighbor = line.strip().split(':')
                    if len(neighbor) == 2:
                        neighbor_ip, neighbor_port = neighbor
                        self.neighbors.append((neighbor_ip, int(neighbor_port)))  # Adiciona o IP e a porta como uma tupla
                print(f"Loaded topology from {neighbors_file}: {self.neighbors}")

    def load_key_values(self, key_value_file):
        if key_value_file:
            with open(key_value_file, 'r') as f:
                for line in f:
                    key, value = line.strip().split()
                    self.key_value_store[key] = value
            print(f"Loaded key-value pairs from {key_value_file}: {self.key_value_store}")

    def start(self):
        print(f"Node started at {self.ip}:{self.port}")
        threading.Thread(target=self.accept_connections).start()
        self.menu()

    def accept_connections(self):
        while self.running:
            try:
                client_socket, client_addr = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(client_socket,)).start()
                with self.lock:
                    client_ip, client_port = client_addr
                    if (client_ip, client_port) not in self.neighbors:
                        self.neighbors.append((client_ip, client_port))
                        print(f"Adding neighbor: {client_ip}:{client_port}")
            except socket.error as e:
                if self.running:
                    logging.error(f"Socket error: {e}")
                break


    def handle_client(self, client_socket):
        with client_socket:
            try:
                while True:
                    message = client_socket.recv(1024).decode()
                    if not message:
                        break
                    self.process_message(message, client_socket)
            except socket.error as e:
                logging.error(f"Socket error: {e}")
            except Exception as e:
                logging.error(f"Unexpected error: {e}")

    def process_message(self, message, client_socket):
        print(f"Processing message: {message}")
        parts = message.split()
        origin, seqno, ttl, operation = parts[:4]
        ttl = int(ttl)

        if ttl <= 0:
            print("TTL expired, discarding message")
            return

        if operation == "HELLO":
            self.handle_hello(origin, client_socket)
        elif operation == "SEARCH":
            mode, last_hop_port, key, hop_count = parts[4:]
            hop_count = int(hop_count)
            self.handle_search(origin, seqno, ttl, mode, last_hop_port, key, hop_count, client_socket)
        elif operation == "VAL":
            mode, key, value, hop_count = parts[4:]
            self.handle_val(mode, key, value, int(hop_count))

    def handle_hello(self, origin, client_socket):
        with self.lock:
            client_ip, client_port = client_socket.getpeername()
            if (client_ip, client_port) not in self.neighbors:
                self.neighbors.append((client_ip, client_port))
                print(f"Adding neighbor: {client_ip}:{client_port}")
                response = f"{self.ip}:{self.port} 0 1 HELLO_OK\n"
                client_socket.sendall(response.encode())
            else:
                return




    def handle_search(self, origin, seqno, ttl, mode, last_hop_port, key, hop_count, client_socket):
        message_id = (origin, seqno)
        if message_id in self.message_seen:
            print("Message already seen, discarding")
            return
        self.message_seen.add(message_id)

        if key in self.key_value_store:
            value = self.key_value_store[key]
            response = f"{self.ip}:{self.port} {seqno} {ttl} VAL {mode} {key} {value} {hop_count}\n"
            client_socket.sendall(response.encode())
            print(f"Key found: {key}, sending value: {value}")
            return

        ttl -= 1
        if ttl <= 0:
            print("TTL expired, discarding message")
            return

        hop_count += 1
        new_message = f"{origin} {seqno} {ttl} SEARCH {mode} {self.port} {key} {hop_count}\n"
        for neighbor_ip, neighbor_port in self.neighbors:
            if neighbor_port != last_hop_port:
                try:
                    print(f"Forwarding message to {neighbor_ip}:{neighbor_port}")
                    neighbor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    neighbor_socket.settimeout(100)
                    neighbor_socket.connect((neighbor_ip, int(neighbor_port)))
                    neighbor_socket.sendall(new_message.encode())
                    neighbor_socket.close()
                except socket.error as e:
                    print(f"Failed to forward message to {neighbor_ip}:{neighbor_port}: {e}")

    def handle_val(self, mode, key, value, hop_count):
        print(f"Value received - Key: {key}, Value: {value}")
        if mode == "FL":
            self.stats["flooding_hops"] += hop_count
        elif mode == "RW":
            self.stats["random_walk_hops"] += hop_count
        elif mode == "BP":
            self.stats["depth_first_hops"] += hop_count

    def menu(self, command_file=None):
        commands = {
            0: self.list_neighbors,
            1: self.send_hello,
            2: self.search_flooding,
            3: self.search_random_walk,
            4: self.search_depth_first,
            5: self.show_statistics,
            6: self.change_ttl,
            9: self.exit_program,
        }

        if command_file and os.path.isfile(command_file):
            with open(command_file, 'r') as file:
                choices = [int(line.strip()) for line in file if line.strip().isdigit()]
        else:
            choices = []

        for choice in choices:
            if choice in commands:
                commands[choice]()
            if choice == 9:
                break

        while True:
            print("Choose command:")
            for cmd, func in commands.items():
                print(f"[{cmd}] {func.__name__.replace('_', ' ').title()}")

            choice = int(input())
            if choice in commands:
                commands[choice]()
            if choice == 9:
                sys.exit(1)

    def list_neighbors(self):
        with self.lock:
            print(f"There are {len(self.neighbors)} neighbors in the table:")
            for i, neighbor in enumerate(self.neighbors):
                print(f"[{i}] {neighbor[0]} {neighbor[1]}")

    def send_hello(self):
        with self.lock:
            for neighbor_ip, neighbor_port in self.neighbors:
                message = f"{self.ip}:{self.port} 0 1 HELLO\n"
                print(f"Sending HELLO to {neighbor_ip}:{neighbor_port}")
                try:
                    neighbor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    neighbor_socket.settimeout(100)
                    neighbor_socket.connect((neighbor_ip, int(neighbor_port)))
                    neighbor_socket.sendall(message.encode())
                    neighbor_socket.close()
                except socket.error as e:
                    print(f"Error sending HELLO to {neighbor_ip}:{neighbor_port}: {e}")

    def search_flooding(self):
        self.search("FL")

    def search_random_walk(self):
        self.search("RW")

    def search_depth_first(self):
        self.search("BP")

    def search(self, mode):
        key = input("Enter key to search: ")
        seqno = random.randint(1, 10000)
        message = f"{self.ip}:{self.port} {seqno} {self.ttl_default} SEARCH {mode} {self.port} {key} 1\n"

        if mode == "FL":
            self.handle_search(self.ip, seqno, self.ttl_default, mode, None, key, 1, None)
        elif mode in ["RW", "BP"]:
            if self.neighbors:
                neighbor_ip, neighbor_port = random.choice(self.neighbors)
                try:
                    print(f"Forwarding {mode} search to {neighbor_ip}:{neighbor_port}")
                    neighbor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    neighbor_socket.settimeout(100)
                    neighbor_socket.connect((neighbor_ip, int(neighbor_port)))
                    neighbor_socket.sendall(message.encode())
                    neighbor_socket.close()
                    self.stats[mode.lower()] += 1
                except socket.error as e:
                    print(f"Error sending search to {neighbor_ip}:{neighbor_port}: {e}")

    def show_statistics(self):
        print("Search statistics:")
        for key, value in self.stats.items():
            print(f"{key}: {value}")

    def change_ttl(self):
        new_ttl = int(input("Enter new TTL: "))
        self.ttl_default = new_ttl
        print(f"TTL changed to {self.ttl_default}")

    def exit_program(self):
        self.running = False
        self.server_socket.close()
        print("Exiting program")

    def connect_to_neighbors(self):
        for neighbor_ip, neighbor_port in self.neighbors:
            while True:
                try:
                    print(f"Attempting to connect to neighbor {neighbor_ip}:{neighbor_port}")
                    neighbor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    neighbor_socket.settimeout(10)
                    neighbor_socket.connect((neighbor_ip, neighbor_port))  # Alterado aqui
                    neighbor_socket.close()
                    print(f"Connected to neighbor {neighbor_ip}:{neighbor_port}")
                    break
                except socket.error as e:
                    print(f"Connection failed to neighbor {neighbor_ip}:{neighbor_port}. Retrying...")
                    time.sleep(10)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python node.py <ip:port> <neighbors_file> <key_value_file> <command_file>")
        sys.exit(1)

    ip, port = sys.argv[1].split(':')
    neighbors_file = sys.argv[2]
    key_value_file = sys.argv[3]

    node = Node(ip, int(port), neighbors_file, key_value_file)
    node.start()
