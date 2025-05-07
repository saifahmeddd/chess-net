import socket
import threading
import json

class ChatServer:
    def __init__(self, host='127.0.0.1', port=5556):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(2)
        self.clients = []
        self.lock = threading.Lock()
        print(f"Chat server started on {host}:{port}")

    def broadcast(self, message, sender=None):
        with self.lock:
            for client in self.clients:
                if client != sender:  # Don't send back to sender
                    try:
                        client.send(json.dumps(message).encode())
                    except:
                        self.clients.remove(client)

    def handle_client(self, client_socket, addr):
        try:
            while True:
                message = client_socket.recv(1024).decode()
                if not message:
                    break
                
                data = json.loads(message)
                if data["type"] == "chat":
                    self.broadcast(data, client_socket)
        except:
            pass
        finally:
            with self.lock:
                if client_socket in self.clients:
                    self.clients.remove(client_socket)
            client_socket.close()

    def start(self):
        while True:
            client_socket, addr = self.server.accept()
            with self.lock:
                self.clients.append(client_socket)
            print(f"New chat connection from {addr}")
            thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
            thread.daemon = True
            thread.start()

if __name__ == "__main__":
    chat_server = ChatServer()
    chat_server.start()
