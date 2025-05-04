import socket
import threading
import json
import time

class ChatServer:
    def __init__(self, host='0.0.0.0', port=5556):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.games = {}  # {game_id: {"players": [conn1, conn2], "messages": []}}
        self.player_info = {}  # {conn: {"game_id": game_id, "color": color}}

    def broadcast_message(self, game_id, message, sender_conn):
        """Send message to all players in the game except the sender"""
        if game_id in self.games:
            for conn in self.games[game_id]["players"]:
                if conn != sender_conn:
                    try:
                        conn.send(json.dumps(message).encode())
                    except:
                        # Remove disconnected player
                        self.handle_disconnect(conn)

    def handle_client(self, conn, addr):
        """Handle individual client connections"""
        print(f"[CHAT] New connection from {addr}")
        
        try:
            while True:
                data = conn.recv(1024).decode()
                if not data:
                    break

                message = json.loads(data)
                
                if message["type"] == "join":
                    # Player joining a game
                    game_id = message["game_id"]
                    color = message["color"]
                    
                    if game_id not in self.games:
                        self.games[game_id] = {"players": [], "messages": []}
                    
                    self.games[game_id]["players"].append(conn)
                    self.player_info[conn] = {"game_id": game_id, "color": color}
                    
                    # Send chat history to the new player
                    for msg in self.games[game_id]["messages"]:
                        conn.send(json.dumps(msg).encode())
                    
                    # Notify other players
                    join_msg = {
                        "type": "system",
                        "content": f"{color} has joined the chat"
                    }
                    self.broadcast_message(game_id, join_msg, conn)
                    
                elif message["type"] == "chat":
                    # Regular chat message
                    game_id = self.player_info[conn]["game_id"]
                    color = self.player_info[conn]["color"]
                    
                    chat_msg = {
                        "type": "chat",
                        "color": color,
                        "content": message["content"],
                        "timestamp": time.time()
                    }
                    
                    # Store message in history
                    self.games[game_id]["messages"].append(chat_msg)
                    
                    # Broadcast to all players in the game
                    self.broadcast_message(game_id, chat_msg, conn)
                    
        except Exception as e:
            print(f"[CHAT ERROR] {addr} disconnected: {e}")
        finally:
            self.handle_disconnect(conn)

    def handle_disconnect(self, conn):
        """Handle client disconnection"""
        if conn in self.player_info:
            game_id = self.player_info[conn]["game_id"]
            color = self.player_info[conn]["color"]
            
            if game_id in self.games:
                # Remove player from game
                self.games[game_id]["players"].remove(conn)
                
                # Notify other players
                leave_msg = {
                    "type": "system",
                    "content": f"{color} has left the chat"
                }
                self.broadcast_message(game_id, leave_msg, conn)
                
                # Clean up empty games
                if not self.games[game_id]["players"]:
                    del self.games[game_id]
            
            del self.player_info[conn]
        
        try:
            conn.close()
        except:
            pass

    def start(self):
        """Start the chat server"""
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"[CHAT SERVER] Started on {self.host}:{self.port}")

        while True:
            conn, addr = self.server_socket.accept()
            thread = threading.Thread(target=self.handle_client, args=(conn, addr))
            thread.daemon = True
            thread.start()

def main():
    chat_server = ChatServer()
    chat_server.start()

if __name__ == "__main__":
    main()
