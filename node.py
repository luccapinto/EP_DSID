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
        try:
            while True:
                data = client.recv(1024).decode()
                if not data:
                    break
                print("Received:", data)
                parts = data.strip().split()
                origin = parts[0]
                seq_no = int(parts[1])
                ttl = int(parts[2])
                operation = parts[3]
                args = parts[4:]

                # Decrement TTL and check if it should be discarded
                ttl -= 1
                if ttl <= 0:
                    print("Discarding message due to zero TTL.")
                    continue

                # Process different types of operations
                if operation == "HELLO":
                    self.process_hello(origin, client)
                elif operation.startswith("SEARCH"):
                    self.process_search(origin, seq_no, ttl, operation, args)
                elif operation == "VAL":
                    self.process_val(origin, args)
        except Exception as e:
            print("Error handling client:", e)
        finally:
            client.close()

    def process_hello(self, origin, client):
        print(f"HELLO received from {origin}")
        response = "HELLO_OK\n"
        client.sendall(response.encode())
        # Add to neighbors if not already present
        if origin not in [f"{host}:{port}" for host, port in self.neighbors]:
            self.neighbors.append(tuple(origin.split(':')))
            print(f"Added {origin} to neighbors.")

    def process_search(self, origin, seq_no, ttl, operation, args):
        mode, last_hop_port, key, hop_count = args
        hop_count = int(hop_count) + 1
        print(f"SEARCH received: mode={mode}, key={key}, hops={hop_count}")

        if mode == "FL":
            self.handle_flooding_search(origin, seq_no, ttl, key, hop_count, last_hop_port)
        elif mode == "RW":
            self.handle_random_walk_search(origin, seq_no, ttl, key, hop_count, last_hop_port)
        elif mode == "BP":
            self.handle_depth_search(origin, seq_no, ttl, key, hop_count, last_hop_port)

    def handle_flooding_search(self, origin, seq_no, ttl, key, hop_count, last_hop_port):
        if key in self.key_value_store:
            self.send_value(origin, key, self.key_value_store[key], hop_count)
        else:
            msg = f"{self.host}:{self.port} {seq_no} {ttl} SEARCH FL {self.port} {key} {hop_count}\n"
            for neighbor in self.neighbors:
                if neighbor[1] != last_hop_port:
                    self.send_message(neighbor, msg)

    def handle_random_walk_search(self, origin, seq_no, ttl, key, hop_count, last_hop_port):
        if key in self.key_value_store:
            self.send_value(origin, key, self.key_value_store[key], hop_count)
        else:
            if self.neighbors:
                chosen_neighbor = random.choice(self.neighbors)
                msg = f"{self.host}:{self.port} {seq_no} {ttl} SEARCH RW {chosen_neighbor[1]} {key} {hop_count}\n"
                self.send_message(chosen_neighbor, msg)

    def handle_depth_search(self, origin, seq_no, ttl, key, hop_count, last_hop_port):
        print(f"Handling Depth-First Search for key: {key} from {origin} with TTL {ttl}")

        if key in self.key_value_store:
            self.send_value(origin, key, self.key_value_store[key], hop_count)
            del self.active_searches[seq_no]  # Clean up after sending the value
        elif ttl > 0:
            next_hop = self.select_next_hop_for_depth_search(last_hop_port)
            if next_hop:
                msg = f"{self.host}:{self.port} {seq_no} {ttl-1} SEARCH BP {self.port} {key} {hop_count+1}\n"
                self.send_message(next_hop, msg)
            else:
                print(f"No valid next hop found for key: {key}, returning to sender.")
                self.send_return_message(origin, seq_no, "No path found", last_hop_port)
        else:
            print("TTL expired, returning to sender.")
            self.send_return_message(origin, seq_no, "TTL expired", last_hop_port)

    def select_next_hop_for_depth_search(self, last_hop_port):
        valid_neighbors = [n for n in self.neighbors if n[1] != last_hop_port]
        if valid_neighbors:
            return random.choice(valid_neighbors)
        return None

    def send_return_message(self, origin, seq_no, message, last_hop_port):
        origin_host, origin_port = origin.split(':')
        return_msg = f"{self.host}:{self.port} {seq_no} 1 RETURN {message}\n"
        self.send_message((origin_host, int(origin_port)), return_msg)

    def send_value(self, origin, key, value, hop_count):
        msg = f"{self.host}:{self.port} 1 {hop_count} VAL {key} {value}\n"
        origin_host, origin_port = origin.split(':')
        self.send_message((origin_host, int(origin_port)), msg)

    def send_message(self, neighbor, message):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((neighbor[0], neighbor[1]))
                sock.sendall(message.encode())
                print(f"Message sent to {neighbor[0]}:{neighbor[1]}: {message}")
        except Exception as e:
            print(f"Failed to send message to {neighbor[0]}:{neighbor[1]}: {e}")