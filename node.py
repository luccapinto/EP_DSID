import socket
import threading
import random
import sys
from typing import List, Dict, Optional, Tuple, Set
import statistics

class Node:
    def __init__(self, ip: str, port: int, neighbors_file: Optional[str] = None, key_value_file: Optional[str] = None):
        self.ip = ip
        self.port = port
        self.neighbors: List[str] = []
        self.key_value_store: Dict[str, str] = {}
        self.load_file(neighbors_file, self.neighbors)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.ip, self.port))
        self.server_socket.listen(5)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.running = True
        self.ttl_default = 100
        self.message_seen: Set[Tuple[str, str]] = set()
        self.lock = threading.Lock()
        self.connections: Dict[str, socket.socket] = {}
        self.visited_nodes: Set[str] = set()
        self.seqno = 1  # Inicializa o número de sequência
        print(f"Servidor criado: {self.ip}:{self.port}\n")
        self.stats = self.initialize_stats()

        self.initialize_neighbors()
        self.load_file(key_value_file, self.key_value_store, is_key_value=True)

    def initialize_stats(self) -> Dict[str, int or List[int]]:
        return {
            "Total de mensagens de flooding vistas": 0,
            "Total de mensagens de random walk vistas": 0,
            "Total de mensagens de busca em profundidade vistas": 0,
            "flooding_hops": [],
            "random_walk_hops": [],
            "depth_first_hops": []
        }

    def load_file(self, filename: Optional[str], storage: List[str] or Dict[str, str], is_key_value: bool = False):
        if filename:
            with open(filename, 'r') as f:
                for line in f:
                    if is_key_value:
                        key, value = line.strip().split()
                        storage[key] = value
                        print(f"Adicionando par ({key}, {value}) na tabela local")
                    else:
                        storage.append(line.strip())

    def initialize_neighbors(self):
        for neighbor in self.neighbors:
            print(f"Tentando adicionar vizinho {neighbor}")
            self.send_hello_message(neighbor)

    def send_hello_message(self, neighbor: str):
        neighbor_ip, neighbor_port = neighbor.split(':')
        message = f"{self.ip}:{self.port} {self.seqno} 1 HELLO\n"
        self.seqno += 1
        try:
            self.send_message(neighbor_ip, int(neighbor_port), message)
        except socket.error:
            print(f"\tErro ao conectar com {neighbor_ip}:{neighbor_port}")

    def start(self):
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

    def handle_client(self, client_socket: socket.socket):
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

    def process_message(self, message: str, client_socket: socket.socket):
        parts = message.split()
        origin, seqno, ttl, operation = parts[:4]
        ttl = int(ttl)

        if ttl <= 0:
            print("TTL igual a zero, descartando mensagem")
            return

        print(f'Mensagem recebida: "{message.strip()}"')

        if operation == "HELLO":
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
        elif operation == "BYE":
            self.handle_bye(origin)

    def handle_hello(self, origin: str, client_socket: socket.socket):
        with self.lock:
            if origin not in self.neighbors:
                self.neighbors.append(origin)
                print(f"Adicionando vizinho na tabela: {origin}")
                response = f"{self.ip}:{self.port} {self.seqno} 1 HELLO_OK\n"
                self.seqno += 1
                self.send_response(client_socket, response)
            else:
                print(f"Vizinho já está na tabela: {origin}")

    def handle_bye(self, origin: str):
        with self.lock:
            if origin in self.neighbors:
                self.neighbors.remove(origin)
                print(f"Removendo vizinho da tabela: {origin}")

    def send_response(self, client_socket: Optional[socket.socket], response: str):
        if client_socket:
            try:
                client_socket.sendall(response.encode())
                print(f"Sent {response.strip()}")
            except socket.error as e:
                print(f"Socket error: {e}")
        else:
            print("Client socket is None, cannot send response")

    def send_message(self, neighbor_ip: str, neighbor_port: int, message: str):
        neighbor_addr = f"{neighbor_ip}:{neighbor_port}"
        print(f'Encaminhando mensagem "{message.strip()}" para {neighbor_addr}')
        try:
            neighbor_socket = self.connections.get(neighbor_addr)
            if neighbor_socket is None or neighbor_socket.fileno() == -1:
                neighbor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                neighbor_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                neighbor_socket.settimeout(5)
                neighbor_socket.connect((neighbor_ip, neighbor_port))
                self.connections[neighbor_addr] = neighbor_socket

            neighbor_socket.sendall(message.encode())
            print(f'\tEnvio feito com sucesso: "{message.strip()}"')
        except socket.error as e:
            print(f"Socket error while sending to {neighbor_addr}: {e}")
            self.connections.pop(neighbor_addr, None)
            try:
                neighbor_socket.close()
            except:
                pass
        except Exception as e:
            print(f"Unexpected error while sending to {neighbor_addr}: {e}")
            self.connections.pop(neighbor_addr, None)
            try:
                neighbor_socket.close()
            except:
                pass

    def handle_search(self, origin: str, seqno: str, ttl: int, mode: str, last_hop_port: str, key: str, hop_count: int, client_socket: Optional[socket.socket] = None):
        message_id = (origin, seqno)
        if message_id in self.message_seen:
            print("Message already seen, discarding")
            return
        self.message_seen.add(message_id)

        if key in self.key_value_store:
            value = self.key_value_store[key]
            response = f"{self.ip}:{self.port} {seqno} {ttl} VAL {mode} {key} {value} {hop_count}\n"
            self.send_response(client_socket, response)
            self.send_message(origin.split(':')[0], int(origin.split(':')[1]), response)
            return

        ttl -= 1
        if ttl <= 0:
            print("TTL expired, discarding message")
            return

        hop_count += 1
        if mode == "FL":
            self.flood_search(origin, seqno, ttl, key, hop_count, last_hop_port)
        elif mode == "RW":
            self.random_walk_search(origin, seqno, ttl, key, hop_count, last_hop_port)
        elif mode == "BP":
            self.depth_first_search(origin, seqno, ttl, key, hop_count, last_hop_port)
        else:
            print("Invalid search mode")
            return

    def flood_search(self, origin: str, seqno: str, ttl: int, key: str, hop_count: int, last_hop_port: str):
        for neighbor in self.neighbors:
            neighbor_ip, neighbor_port = neighbor.split(':')
            if neighbor_port != last_hop_port:
                new_message = f"{origin} {seqno} {ttl} SEARCH FL {self.port} {key} {hop_count}\n"
                self.send_message(neighbor_ip, int(neighbor_port), new_message)

    def random_walk_search(self, origin: str, seqno: str, ttl: int, key: str, hop_count: int, last_hop_port: str):
        if self.neighbors:
            neighbor = random.choice(self.neighbors)
            neighbor_ip, neighbor_port = neighbor.split(':')
            new_message = f"{origin} {seqno} {ttl} SEARCH RW {last_hop_port} {key} {hop_count}\n"
            self.send_message(neighbor_ip, int(neighbor_port), new_message)

    def depth_first_search(self, origin: str, seqno: str, ttl: int, key: str, hop_count: int, last_hop_port: str):
        candidate_neighbors = [n for n in self.neighbors if n.split(':')[1] != last_hop_port]
        if not candidate_neighbors:
            print(f"BP: Não foi possível localizar a chave {key}")
            return

        next_neighbor = random.choice(candidate_neighbors)
        next_ip, next_port = next_neighbor.split(':')
        new_message = f"{origin} {seqno} {ttl} SEARCH BP {next_port} {key} {hop_count + 1}\n"
        self.send_message(next_ip, int(next_port), new_message)

    def handle_val(self, mode: str, key: str, value: str, hop_count: int):
        print(f"\tValor encontrado!\n \t\tchave: {key}, valor: {value}")
        if mode == "FL":
            self.stats["flooding_hops"].append(hop_count)
            self.stats["Total de mensagens de flooding vistas"] += 1
        elif mode == "RW":
            self.stats["random_walk_hops"].append(hop_count)
            self.stats["Total de mensagens de random walk vistas"] += 1
        elif mode == "BP":
            self.stats["depth_first_hops"].append(hop_count)
            self.stats["Total de mensagens de busca em profundidade vistas"] += 1

    def calculate_mean_std(self, data: List[int]) -> Tuple[float, float]:
        if data:
            mean = statistics.mean(data)
            stddev = statistics.stdev(data) if len(data) > 1 else 0.0
        else:
            mean = stddev = 0.0
        return mean, stddev

    def show_statistics(self):
        print("Estatisticas:")
        stats_to_print = {
            "Total de mensagens de flooding vistas": self.stats["Total de mensagens de flooding vistas"],
            "Total de mensagens de random walk vistas": self.stats["Total de mensagens de random walk vistas"],
            "Total de mensagens de busca em profundidade vistas": self.stats["Total de mensagens de busca em profundidade vistas"],
        }
        flooding_mean, flooding_std = self.calculate_mean_std(self.stats["flooding_hops"])
        random_walk_mean, random_walk_std = self.calculate_mean_std(self.stats["random_walk_hops"])
        depth_first_mean, depth_first_std = self.calculate_mean_std(self.stats["depth_first_hops"])

        print(f"\tTotal de mensagens de flooding vistas: {stats_to_print['Total de mensagens de flooding vistas']}")
        print(f"\tTotal de mensagens de random walk vistas: {stats_to_print['Total de mensagens de random walk vistas']}")
        print(f"\tTotal de mensagens de busca em profundidade vistas: {stats_to_print['Total de mensagens de busca em profundidade vistas']}")
        print(f"\tMedia de saltos ate encontrar destino por flooding: {flooding_mean:.1f} (dp {flooding_std:.2f})")
        print(f"\tMedia de saltos ate encontrar destino por random walk: {random_walk_mean:.1f} (dp {random_walk_std:.2f})")
        print(f"\tMedia de saltos ate encontrar destino por busca em profundidade: {depth_first_mean:.1f} (dp {depth_first_std:.2f})")

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
            print("""
Escolha o comando:
\t[0] Listar vizinhos
\t[1] HELLO
\t[2] SEARCH (flooding)
\t[3] SEARCH (random walk)
\t[4] SEARCH (busca em profundidade)
\t[5] Estatisticas
\t[6] Alterar valor padrao de TTL
\t[9] Sair
""")


            try:
                choice = int(input())
                if choice in commands:
                    commands[choice]()
                else:
                    print("Comando invalido. Por favor insira um comando valido")
            except ValueError:
                print("Entrada invalida. Escolha um numero valido")

    def list_neighbors(self):
        print(f"Há {len(self.neighbors)} vizinhos na tabela:")
        for index, neighbor in enumerate(self.neighbors):
            neighbor_ip, neighbor_port = neighbor.split(':')
            print(f"\t[{index}] {neighbor_ip} {neighbor_port}")

    def send_hello(self):
        print("Escolha o vizinho:")
        self.list_neighbors()
        try:
            number = int(input())
            if 0 <= number < len(self.neighbors):
                neighbor_ip, neighbor_port = self.neighbors[number].split(':')
                message = f"{self.ip}:{self.port} {self.seqno} 1 HELLO\n"
                self.seqno += 1  # Incrementa o número de sequência
                self.send_message(neighbor_ip, int(neighbor_port), message)
            else:
                print("Vizinho invalido. Escolha um numero valido")
        except ValueError:
            print("Entrada invalida. Escolha um numero valido")

    def handle_search_flooding(self):
        key = input("Digite a chave a ser buscada\n")
        if key in self.key_value_store:
            print(f"Valor na tabela local!\n chave: {key}, valor: {self.key_value_store[key]}")
            return

        origin = f"{self.ip}:{self.port}"
        seqno = self.seqno
        self.seqno += 1  # Incrementa o número de sequência
        ttl = self.ttl_default
        last_hop_port = self.port
        hop_count = 0
        self.handle_search(origin, str(seqno), ttl, "FL", last_hop_port, key, hop_count)

    def handle_search_random_walk(self):
        key = input("Digite a chave a ser buscada\n")
        if key in self.key_value_store:
            print(f"Valor na tabela local!\n chave: {key}, valor: {self.key_value_store[key]}")
            return

        origin = f"{self.ip}:{self.port}"
        seqno = self.seqno
        self.seqno += 1  # Incrementa o número de sequência
        ttl = self.ttl_default
        last_hop_port = self.port
        hop_count = 0
        self.handle_search(origin, str(seqno), ttl, "RW", last_hop_port, key, hop_count)

    def handle_search_depth_first(self):
        key = input("Digite a chave a ser buscada\n")
        if key in self.key_value_store:
            print(f"Valor na tabela local!\n chave: {key}, valor: {self.key_value_store[key]}")
            return

        origin = f"{self.ip}:{self.port}"
        seqno = self.seqno
        self.seqno += 1  # Incrementa o número de sequência
        ttl = self.ttl_default
        last_hop_port = self.port
        hop_count = 0
        self.visited_nodes.clear()
        self.handle_search(origin, str(seqno), ttl, "BP", last_hop_port, key, hop_count)

    def show_statistics(self):
        print("Estatisticas:")
        print(f"\tTotal de mensagens de flooding vistas: {self.stats['Total de mensagens de flooding vistas']}")
        print(f"\tTotal de mensagens de random walk vistas: {self.stats['Total de mensagens de random walk vistas']}")
        print(f"\tTotal de mensagens de busca em profundidade vistas: {self.stats['Total de mensagens de busca em profundidade vistas']}")

        flooding_mean, flooding_std = self.calculate_mean_std(self.stats["flooding_hops"])
        random_walk_mean, random_walk_std = self.calculate_mean_std(self.stats["random_walk_hops"])
        depth_first_mean, depth_first_std = self.calculate_mean_std(self.stats["depth_first_hops"])

        print(f"\tMedia de saltos ate encontrar destino por flooding: {flooding_mean:.1f} (dp {flooding_std:.2f})")
        print(f"\tMedia de saltos ate encontrar destino por random walk: {random_walk_mean:.1f} (dp {random_walk_std:.2f})")
        print(f"\tMedia de saltos ate encontrar destino por busca em profundidade: {depth_first_mean:.1f} (dp {depth_first_std:.2f})")

    def change_ttl(self):
        try:
            new_ttl = int(input("Digite novo valor de TTL\n"))
            self.ttl_default = new_ttl
        except ValueError:
            print("Valor de TTL invalido")

    def exit_program(self):
        with self.lock:
            print("Saindo...")
            for neighbor in self.neighbors:
                neighbor_ip, neighbor_port = neighbor.split(':')
                message = f"{self.ip}:{self.port} {self.seqno} 1 BYE\n"
                self.seqno += 1
                try:
                    self.send_message(neighbor_ip, int(neighbor_port), message)
                except socket.error as e:
                    print(f"Error sending BYE to {neighbor_ip}:{neighbor_port}: {e}")
            for neighbor_socket in self.connections.values():
                neighbor_socket.close()

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
