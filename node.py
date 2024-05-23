import socket  # Biblioteca para criar e gerenciar conexões de rede
import threading  # Biblioteca para trabalhar com threads (execução paralela)
import random  # Biblioteca para gerar números aleatórios
import logging  # Biblioteca para registrar logs (mensagens de debug, info, etc.)
import sys  # Biblioteca para interagir com o sistema (argumentos, saída, etc.)

# Configuração do logging para exibir mensagens de debug com timestamp e nível de log
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class Node:
    def __init__(self, ip, port, neighbors_file=None, key_value_file=None):
        self.ip = ip  # IP do nó
        self.port = port  # Porta do nó
        self.neighbors = []  # Lista de vizinhos
        self.key_value_store = {}  # Dicionário para armazenar pares chave-valor
        self.load_topology(neighbors_file)  # Carrega a topologia dos vizinhos
        self.load_key_values(key_value_file)  # Carrega os pares chave-valor
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Cria um socket TCP
        self.server_socket.bind((self.ip, self.port))  # Associa o socket ao endereço e porta
        self.server_socket.listen(5)  # Coloca o socket em modo de escuta, permitindo até 5 conexões pendentes
        self.running = True  # Flag para indicar se o nó está ativo
        self.ttl_default = 100  # Valor padrão do TTL (Time To Live)
        self.message_seen = set()  # Conjunto para rastrear mensagens já vistas
        self.lock = threading.Lock()  # Lock para sincronizar o acesso a recursos compartilhados
        print(f"Node running at {self.ip}:{self.port}")
        self.stats = {
            "flooding": 0,
            "random_walk": 0,
            "depth_first": 0,
            "flooding_hops": 0,
            "random_walk_hops": 0,
            "depth_first_hops": 0
        }

    def load_topology(self, neighbors_file):
        if neighbors_file:
            with open(neighbors_file, 'r') as f:
                # Carrega os vizinhos do arquivo e armazena como tuplas (IP, porta)
                self.neighbors = [tuple(line.strip().split(':')) for line in f.readlines()]
            print(f"Loaded topology from {neighbors_file}: {self.neighbors}")

    def load_key_values(self, key_value_file):
        if key_value_file:
            with open(key_value_file, 'r') as f:
                for line in f:
                    key, value = line.strip().split()
                    self.key_value_store[key] = value  # Armazena os pares chave-valor no dicionário
            print(f"Loaded key-value pairs from {key_value_file}: {self.key_value_store}")

    def start(self):
        print(f"Node started at {self.ip}:{self.port}")
        # Inicia uma thread para aceitar conexões
        threading.Thread(target=self.accept_connections).start()
        self.menu()  # Exibe o menu de comandos

    def accept_connections(self):
        while True:
            client_socket, client_ip = self.server_socket.accept()  # Aceita uma nova conexão
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()  # Inicia uma thread para lidar com o cliente

    def handle_client(self, client_socket):
        with client_socket:
            try:
                while True:
                    message = client_socket.recv(1024).decode()  # Recebe mensagem do cliente
                    if not message:
                        break
                    self.process_message(message, client_socket)  # Processa a mensagem recebida
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
            if origin not in self.neighbors:
                self.neighbors.append(origin)  # Adiciona novo vizinho
                print(f"Adding neighbor: {origin}")
                response = f"{self.ip}:{self.port} 0 1 HELLO_OK\n"
                client_socket.sendall(response.encode())  # Envia resposta de confirmação
            else:
                print(f"Neighbor already in table: {origin}")

    def handle_search(self, origin, seqno, ttl, mode, last_hop_port, key, hop_count, client_socket):
        message_id = (origin, seqno)
        if message_id in self.message_seen:
            print("Message already seen, discarding")
            return
        self.message_seen.add(message_id)  # Marca a mensagem como vista

        if key in self.key_value_store:
            value = self.key_value_store[key]
            response = f"{self.ip}:{self.port} {seqno} {ttl} VAL {mode} {key} {value} {hop_count}\n"
            client_socket.sendall(response.encode())  # Envia valor da chave encontrada
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
                    neighbor_socket.settimeout(5)
                    neighbor_socket.connect((neighbor_ip, int(neighbor_port)))
                    neighbor_socket.sendall(new_message.encode())  # Reenvia a mensagem para os vizinhos
                    neighbor_socket.close()
                except socket.error as e:
                    print(f"Failed to forward message to {neighbor_ip}:{neighbor_port}: {e}")

    def handle_val(self, mode, key, value, hop_count):
        print(f"Value received - Key: {key}, Value: {value}")
        if mode == "FL":
            self.stats["flooding_hops"] += hop_count  # Atualiza estatísticas para flooding
        elif mode == "RW":
            self.stats["random_walk_hops"] += hop_count  # Atualiza estatísticas para random walk
        elif mode == "BP":
            self.stats["depth_first_hops"] += hop_count  # Atualiza estatísticas para depth first

    def menu(self):
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

        while True:
            print("Choose command:")
            for cmd, func in commands.items():
                print(f"[{cmd}] {func.__name__.replace('_', ' ').title()}")

            choice = int(input())  # Lê a escolha do usuário
            if choice in commands:
                commands[choice]()  # Executa o comando escolhido
            if choice == 9:
                break

    def list_neighbors(self):
        with self.lock:
            print(f"There are {len(self.neighbors)} neighbors in the table:")
            for i, neighbor in enumerate(self.neighbors):
                print(f"[{i}] {neighbor[0]} {neighbor[1]}")  # Lista os vizinhos

    def send_hello(self):
        with self.lock:
            for neighbor_ip, neighbor_port in self.neighbors:
                message = f"{self.ip}:{self.port} 0 1 HELLO\n"
                print(f"Sending HELLO to {neighbor_ip}:{neighbor_port}")
                try:
                    neighbor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    neighbor_socket.settimeout(5)
                    neighbor_socket.connect((neighbor_ip, int(neighbor_port)))
                    neighbor_socket.sendall(message.encode())  # Envia mensagem HELLO
                    neighbor_socket.close()
                except socket.error as e:
                    print(f"Error sending HELLO to {neighbor_ip}:{neighbor_port}: {e}")

    def search_flooding(self):
        self.search("FL")  # Inicia busca por flooding

    def search_random_walk(self):
        self.search("RW")  # Inicia busca por random walk

    def search_depth_first(self):
        self.search("BP")  # Inicia busca por depth first

    def search(self, mode):
        key = input("Enter key to search: ")  # Lê a chave a ser buscada
        seqno = random.randint(1, 10000)  # Gera número de sequência aleatório
        message = f"{self.ip}:{self.port} {seqno} {self.ttl_default} SEARCH {mode} {self.port} {key} 1\n"

        if mode == "FL":
            self.handle_search(self.ip, seqno, self.ttl_default, "FL", self.port, key, 1, None)
        elif mode == "RW":
            self.handle_search(self.ip, seqno, self.ttl_default, "RW", self.port, key, 1, None)
        elif mode == "BP":
            self.handle_search(self.ip, seqno, self.ttl_default, "BP", self.port, key, 1, None)

    def show_statistics(self):
        print("Statistics:")
        print(f"Total flooding messages seen: {self.stats['flooding']}")
        print(f"Total random walk messages seen: {self.stats['random_walk']}")
        print(f"Total depth first messages seen: {self.stats['depth_first']}")
        print(f"Avg hops for flooding: {self.stats['flooding_hops']/max(self.stats['flooding'], 1)}")
        print(f"Avg hops for random walk: {self.stats['random_walk_hops']/max(self.stats['random_walk'], 1)}")
        print(f"Avg hops for depth first: {self.stats['depth_first_hops']/max(self.stats['depth_first'], 1)}")

    def change_ttl(self):
        new_ttl = int(input("Enter new TTL: "))  # Lê o novo valor de TTL
        self.ttl_default = new_ttl
        print(f"Default TTL changed to {self.ttl_default}")

    def exit_program(self):
        with self.lock:
            for neighbor_ip, neighbor_port in self.neighbors:
                message = f"{self.ip}:{self.port} 0 1 BYE\n"
                try:
                    neighbor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    neighbor_socket.settimeout(5)
                    neighbor_socket.connect((neighbor_ip, int(neighbor_port)))
                    neighbor_socket.sendall(message.encode())  # Envia mensagem BYE para os vizinhos
                    neighbor_socket.close()
                except socket.error as e:
                    print(f"Error sending BYE to {neighbor_ip}:{neighbor_port}: {e}")
        print("Exiting program...")
        self.server_socket.close()
        sys.exit(0)  # Termina a execução do programa

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python node.py <address>:<port> [neighbors_file] [key_value_file]")
        sys.exit(1)  # Encerra o programa se os argumentos estiverem incorretos

    address_port = sys.argv[1]
    address, port = address_port.split(":")
    port = int(port)
    neighbors_file = sys.argv[2] if len(sys.argv) > 2 else None
    key_value_file = sys.argv[3] if len(sys.argv) > 3 else None

    node = Node(address, port, neighbors_file, key_value_file)
    try:
        node.start()  # Inicia o nó
    except KeyboardInterrupt:
        node.exit_program()  # Encerra o programa em caso de interrupção (Ctrl+C)
