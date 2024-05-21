from node import Node
import threading
import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <port> [neighbors_file] [key_values_file]")
        return

    host = '127.0.0.1'
    port = int(sys.argv[1])
    node = Node(host, port)

    if len(sys.argv) > 2:
        try:
            node.load_neighbors(sys.argv[2])
        except Exception as e:
            print(f"Failed to load neighbors: {e}")
            return

    if len(sys.argv) > 3:
        try:
            node.load_key_values(sys.argv[3])
        except Exception as e:
            print(f"Failed to load key-value pairs: {e}")
            return
    
    thread = threading.Thread(target=node.listen_for_connections)
    thread.start()

    try:
        while True:
            cmd = input("Enter command (list, search [method] [key], exit): ").split()
            if cmd[0] == "exit":
                break
            elif cmd[0] == "list":
                node.process_command("list_neighbors")
            elif cmd[0] == "search" and len(cmd) > 2:
                method, key = cmd[1], cmd[2]
                node.initiate_search(method, key)
    finally:
        # Attempt to cleanly shut down the node
        node.socket.close()
        thread.join()
        print("Node shutdown completed.")

if __name__ == "__main__":
    main()
