from node import Node
import threading
import sys

def main():
    host = '127.0.0.1'
    port = int(sys.argv[1])
    node = Node(host, port)
    if len(sys.argv) > 2:
        node.load_neighbors(sys.argv[2])
    if len(sys.argv) > 3:
        node.load_key_values(sys.argv[3])
    
    threading.Thread(target=node.listen_for_connections).start()

    while True:
        cmd = input("Enter command (list, search [method] [key], exit): ").split()
        if cmd[0] == "exit":
            break
        elif cmd[0] == "list":
            node.process_command("list_neighbors")
        elif cmd[0] == "search":
            method, key = cmd[1], cmd[2]
            node.initiate_search(method, key)

if __name__ == "__main__":
    main()
