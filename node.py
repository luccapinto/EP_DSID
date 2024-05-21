import socket
import threading
import random

class Node:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.neighbors = []
        self.key_value_store = {}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((host, port))
        self.active_searches = {}

    def listen_for_connections(self):
        self.socket.listen()
        print(f"Listening on {self.host}:{self.port}")
        while True:
            client, addr = self.socket.accept()
            print(f"Connected to {addr}")
            threading.Thread(target=self.handle_client, args=(client,)).start()

    def handle_client(self, client):
        while True:
            data = client.recv(1024)
            if not data:
                break
            print("Received:", data.decode())
        client.close()

    def send_hello(self, neighbor):
        message = f"HELLO from {self.host}:{self.port}"
        neighbor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        neighbor_socket.connect((neighbor.host, neighbor.port))
        neighbor_socket.sendall(message.encode())
        neighbor_socket.close()

    def load_neighbors(self, neighbors_file):
        with open(neighbors_file, 'r') as file:
            for line in file:
                host, port = line.strip().split(':')
                self.neighbors.append((host, int(port)))

    def load_key_values(self, key_values_file):
        with open(key_values_file, 'r') as file:
            for line in file:
                key, value = line.strip().split(' ', 1)
                self.key_value_store[key] = value

    def initiate_search(self, method, key):
        if key in self.key_value_store:
            print(f"Key found locally! Key: {key}, Value: {self.key_value_store[key]}")
        else:
            seq_no = random.randint(1, 10000)
            if method == "flooding":
                msg = f"{self.host}:{self.port} {seq_no} 100 SEARCH FL {self.port} {key} 1"
                self.flood_message(msg)
            elif method == "random_walk":
                if self.neighbors:
                    chosen_neighbor = random.choice(self.neighbors)
                    msg = f"{self.host}:{self.port} {seq_no} 100 SEARCH RW {chosen_neighbor[1]} {key} 1"
                    self.send_message(chosen_neighbor, msg)
            elif method == "depth":
                self.depth_first_search(key, seq_no)

    def flood_message(self, message):
        for neighbor in self.neighbors:
            self.send_message(neighbor, message)

    def send_message(self, neighbor, message):
        try:
            neighbor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            neighbor_socket.connect((neighbor[0], neighbor[1]))
            neighbor_socket.sendall(message.encode())
            print(f"Message sent to {neighbor[0]}:{neighbor[1]}: {message}")
            neighbor_socket.close()
        except Exception as e:
            print(f"Failed to send message to {neighbor[0]}:{neighbor[1]}: {e}")
