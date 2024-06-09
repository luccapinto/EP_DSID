import socket
import threading
import random
import sys

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
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.running = True
        self.ttl_default = 100
        self.message_seen = set()
        self.lock = threading.Lock()
        self.connections = {}  # Dicionário para manter as conexões abertas
        self.visited_nodes = set()
        print(f"Node running at {self.ip}:{self.port}")
        self.stats = {
            "flooding": 0,
            "random_walk": 0,
            "depth_first": 0,
            "flooding_hops": 0,
            "random_walk_hops": 0,
            "depth_first_hops": 0
        }
        self.initialize_neighbors()

    def load_topology(self, neighbors_file):
        if neighbors_file:
            with open(neighbors_file, 'r') as f:
                self.neighbors = [line.strip() for line in f.readlines()]
            print(f"Loaded topology from {neighbors_file}: {self.neighbors}")

    def load_key_values(self, key_value_file):
        if key_value_file:
            with open(key_value_file, 'r') as f:
                for line in f:
                    key, value = line.strip().split()
                    self.key_value_store[key] = value
            print(f"Loaded key-value pairs from {key_value_file}: {self.key_value_store}")

    def initialize_neighbors(self):
        for neighbor in self.neighbors:
            neighbor_ip, neighbor_port = neighbor.split(':')
            print(f"Tentando adicionar vizinho {neighbor_ip}:{neighbor_port}")
            message = f"{self.ip}:{self.port} 0 1 HELLO\n"
            try:
                neighbor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                neighbor_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                neighbor_socket.settimeout(5)
                neighbor_socket.connect((neighbor_ip, int(neighbor_port)))
                neighbor_socket.sendall(message.encode())
                neighbor_socket.close()
                print(f'Envio feito com sucesso: "{message.strip()}"')
                with self.lock:
                    if neighbor not in self.neighbors:
                        self.neighbors.append(neighbor)
            except socket.error as e:
                print(f"Erro ao conectar: {e}")

    def start(self):
        print(f"Node started at {self.ip}:{self.port}")
        threading.Thread(target=self.accept_connections).start()
        self.menu()

    def accept_connections(self):
        while self.running:
            try:
                client_socket, client_ip = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(client_socket,)).start()
            except socket.error as e:
                if self.running:
                    print(f"Socket error: {e}")
                break

    def handle_client(self, client_socket):
        with client_socket:
            client_socket.settimeout(None)
            try:
                while True:
                    message = client_socket.recv(1024).decode()
                    if not message:
                        break
                    self.process_message(message, client_socket)
            except socket.error as e:
                print(f"Socket error: {e}")
            except Exception as e:
                print(f"Unexpected error: {e}")

    def process_message(self, message, client_socket):
        parts = message.split()
        origin, seqno, ttl, operation = parts[:4]
        ttl = int(ttl)

        if ttl <= 0:
            print("TTL expired, discarding message")
            return

        print(f'Mensagem recebida: "{message.strip()}"')

        if operation == "HELLO":
            print(f"Received HELLO from {origin}")
            self.handle_hello(origin, client_socket)
        elif operation == "HELLO_OK":
            print(f"Received HELLO_OK from {origin}")
        elif operation == "SEARCH":
            mode, last_hop_port, key, hop_count = parts[4:]
            hop_count = int(hop_count)
            self.handle_search(origin, seqno, ttl, mode, last_hop_port, key, hop_count, client_socket)
        elif operation == "VAL":
            mode, key, value, hop_count = parts[4:]
            self.handle_val(mode, key, value, int(hop_count))

    def handle_hello(self, origin, client_socket):
        with self.lock:
            if origin not in self.neighbors:
                self.neighbors.append(origin)
                print(f"Adicionando vizinho na tabela: {origin}")
                response = f"{self.ip}:{self.port} 0 1 HELLO_OK\n"
                try:
                    client_socket.sendall(response.encode())
                    print(f"Sent HELLO_OK to {origin}")
                except socket.error as e:
                    print(f"Socket error: {e}")
            else:
                print(f"Vizinho já está na tabela: {origin}")
                return

    def send_message(self, neighbor_ip, neighbor_port, message):
        neighbor_addr = f"{neighbor_ip}:{neighbor_port}"
        print(f'Encaminhando mensagem "{message.strip()}" para {neighbor_ip}:{neighbor_port}')
        try:
            if neighbor_addr in self.connections:
                neighbor_socket = self.connections[neighbor_addr]
                if neighbor_socket.fileno() == -1:
                    raise socket.error("Socket is closed or invalid")
            else:
                neighbor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                neighbor_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                neighbor_socket.settimeout(5)
                neighbor_socket.connect((neighbor_ip, int(neighbor_port)))
                self.connections[neighbor_addr] = neighbor_socket

            neighbor_socket.sendall(message.encode())
            print(f'Envio feito com sucesso: "{message.strip()}"')
        except socket.error as e:
            print(f"Socket error while sending to {neighbor_ip}:{neighbor_port}: {e}")
            if neighbor_addr in self.connections:
                del self.connections[neighbor_addr]
            try:
                neighbor_socket.close()
            except:
                pass
        except Exception as e:
            print(f"Unexpected error while sending to {neighbor_ip}:{neighbor_port}: {e}")
            if neighbor_addr in self.connections:
                del self.connections[neighbor_addr]
            try:
                neighbor_socket.close()
            except:
                pass

    def handle_search(self, origin, seqno, ttl, mode, last_hop_port, key, hop_count, client_socket=None):
        message_id = (origin, seqno)
        if message_id in self.message_seen:
            print("Message already seen, discarding")
            return
        self.message_seen.add(message_id)

        if key in self.key_value_store:
            value = self.key_value_store[key]
            response = f"{self.ip}:{self.port} {seqno} {ttl} VAL {mode} {key} {value} {hop_count}\n"
            if client_socket:
                try:
                    client_socket.sendall(response.encode())
                except socket.error as e:
                    print(f"Socket error: {e}")
            print(f"Key found: {key}, sending value: {value}")

            origin_ip, origin_port = origin.split(':')
            return_message = f"{self.ip}:{self.port} {seqno} {ttl} VAL {mode} {key} {value} {hop_count}\n"
            self.send_message(origin_ip, origin_port, return_message)
            self.message_seen = set()
            return

        ttl -= 1
        if ttl <= 0:
            print("TTL expired, discarding message")
            return

        hop_count += 1
        if mode == "FL":  # Flooding
            for neighbor in self.neighbors:
                neighbor_ip, neighbor_port = neighbor.split(':')
                if neighbor_port != last_hop_port:
                    new_message = f"{origin} {seqno} {ttl} SEARCH {mode} {self.port} {key} {hop_count}\n"
                    self.send_message(neighbor_ip, neighbor_port, new_message)
        elif mode == "RW":  # Random Walk
            if self.neighbors:
                neighbor = random.choice(self.neighbors)
                neighbor_ip, neighbor_port = neighbor.split(':')
                new_message = f"{origin} {seqno} {ttl} SEARCH {mode} {last_hop_port} {key} {hop_count}\n"
                self.send_message(neighbor_ip, neighbor_port, new_message)
        elif mode == "BP":
            candidate_neighbors = [n for n in self.neighbors if n.split(':')[1] != last_hop_port]
            if not candidate_neighbors and self.ip == origin.split(':')[0] and self.port == int(origin.split(':')[1]):
                print(f"BP: Não foi possível localizar a chave {key}")
                return
            if candidate_neighbors:
                next_neighbor = random.choice(candidate_neighbors)
                next_ip, next_port = next_neighbor.split(':')
            else:
                next_ip, next_port = last_hop_port.split(':')

            new_message = f"{self.ip}:{self.port} {seqno} {ttl} SEARCH BP {next_port} {key} {hop_count + 1}\n"
            self.send_message(next_ip, next_port, new_message)
        else:
            print("Invalid search mode")
            return

        self.message_seen = set()

    def handle_val(self, mode, key, value, hop_count):
        print(f"Value received - Key: {key}, Value: {value}")
        if mode == "FL":
            self.stats["flooding_hops"] += hop_count
        elif mode == "RW":
            self.stats["random_walk_hops"] += hop_count
        elif mode == "BP":
            self.stats["depth_first_hops"] += hop_count

        if mode == "FL":
            client_socket = self.connections.get((key, value))
            if client_socket:
                try:
                    client_socket.sendall(response.encode())
                    client_socket.close()
                except socket.error as e:
                    print(f"Socket error: {e}")
                except Exception as e:
                    print(f"Unexpected error: {e}")
                finally:
                    self.connections.pop((key, value), None)

    def menu(self):
        commands = {
            0: self.list_neighbors,
            1: self.send_hello,
            2: self.handle_search_flooding,
            3: self.handle_search_random_walk,
            4: self.handle_search_depth_first,
            5: self.show_statistics,
            6: self.change_ttl,
            9: self.exit_program,
        }

        while True:
            print("\nEscolha o comando")
            print("[0] Listar vizinhos")
            print("[1] HELLO")
            print("[2] SEARCH (flooding)")
            print("[3] SEARCH (random walk)")
            print("[4] SEARCH (busca em profundidade)")
            print("[5] Estatisticas")
            print("[6] Alterar valor padrao de TTL")
            print("[9] Sair")

            try:
                choice = input()
                if not choice.strip():
                    continue
                choice = int(choice)
                if choice == 9:
                    break
                if choice in commands:
                    commands[choice]()
                else:
                    print("Invalid command. Please enter a valid command number.")
            except ValueError:
                print("Invalid input. Please enter a valid command number.")

    def list_neighbors(self):
        print("Neighbors:", self.neighbors)

    def send_hello(self):
        print("Choose a neighbor:")
        i = 0
        with self.lock:
            for neighbor in self.neighbors:
                neighbor_ip, neighbor_port = neighbor.split(':')
                print(f"[{i}] {neighbor_ip}:{neighbor_port}")
                i += 1
            while True:
                try:
                    number = int(input("Choose neighbor number: "))
                    if 0 <= number < len(self.neighbors):
                        break
                    else:
                        print("Invalid neighbor number. Please choose a valid number.")
                except ValueError:
                    print("Invalid input. Please enter a valid number.")

            neighbor_ip, neighbor_port = self.neighbors[number].split(':')
            message = f"{self.ip}:{self.port} 0 1 HELLO\n"
            print(f"Encaminhando mensagem \"{message.strip()}\" para {neighbor_ip}:{neighbor_port}")
            try:
                neighbor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                neighbor_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                neighbor_socket.settimeout(5)
                neighbor_socket.connect((neighbor_ip, int(neighbor_port)))
                neighbor_socket.sendall(message.encode())
                neighbor_socket.close()
                print(f'Envio feito com sucesso: "{message.strip()}"')
            except socket.error as e:
                print(f"Error sending HELLO to {neighbor_ip}:{neighbor_port}: {e}")
                print(f"Socket error: {e}")
            except Exception as e:
                print(f"Unexpected error: {e}")

    def handle_search_flooding(self):
        print("Choose a key:")
        key = input()
        origin = f"{self.ip}:{self.port}"
        seqno = random.randint(1, 1000)
        ttl = self.ttl_default
        last_hop_port = self.port
        hop_count = 0
        self.handle_search(origin, seqno, ttl, "FL", last_hop_port, key, hop_count)

    def handle_search_random_walk(self):
        print("Choose a key:")
        key = input()
        origin = f"{self.ip}:{self.port}"
        seqno = random.randint(1, 1000)
        ttl = self.ttl_default
        last_hop_port = self.port
        hop_count = 0
        self.handle_search(origin, seqno, ttl, "RW", last_hop_port, key, hop_count)

    def handle_search_depth_first(self):
        print("Choose a key:")
        key = input()
        origin = f"{self.ip}:{self.port}"
        seqno = random.randint(1, 1000)
        ttl = self.ttl_default
        last_hop_port = self.port
        hop_count = 0
        self.visited_nodes.clear()
        self.handle_search(origin, seqno, ttl, "BP", last_hop_port, key, hop_count)

    def show_statistics(self):
        print("Statistics:")
        for stat, value in self.stats.items():
            print(f"{stat}: {value}")

    def change_ttl(self):
        try:
            new_ttl = int(input("Enter new TTL value: "))
            self.ttl_default = new_ttl
            print(f"TTL value updated to {new_ttl}")
        except ValueError:
            print("Invalid TTL value.")

    def exit_program(self):
        with self.lock:
            for neighbor in self.neighbors:
                neighbor_ip, neighbor_port = neighbor.split(':')
                message = f"{self.ip}:{self.port} 0 1 BYE\n"
                try:
                    self.send_message(neighbor_ip, neighbor_port, message)
                except socket.error as e:
                    print(f"Error sending BYE to {neighbor_ip}:{neighbor_port}: {e}")
                    print(f"Socket error: {e}")

            for neighbor_socket in self.connections.values():
                neighbor_socket.close()

        print("Exiting program...")
        self.running = False
        self.server_socket.close()
        sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python node.py <address>:<port> [neighbors_file] [key_value_file]")
        sys.exit(1)

    address_port = sys.argv[1]
    address, port = address_port.split(":")
    port = int(port)
    neighbors_file = sys.argv[2] if len(sys.argv) > 2 else None
    key_value_file = sys.argv[3] if len(sys.argv) > 3 else None

    node = Node(address, port, neighbors_file, key_value_file)
    try:
        node.start()
    except KeyboardInterrupt:
        node.exit_program()
