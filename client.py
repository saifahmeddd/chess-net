import socket
import threading
import json

my_color = None
current_turn = None
game_id = 1  # This should match the game ID from the server

def listen_for_updates(client_socket):
    global current_turn
    while True:
        try:
            data = client_socket.recv(1024).decode()
            if not data:
                break

            message = json.loads(data)

            if message["type"] == "wait":
                print("Waiting for opponent...")

            elif message["type"] == "init":
                global my_color
                my_color = message["color"]
                print(f"You are playing as {my_color.upper()}")
                # Connect to chat server after getting color
                connect_to_chat()

            elif message["type"] == "update":
                current_turn = message["turn"]
                print(f"Opponent moved: {message['move']}")
                print(f"Board FEN: {message['fen']}")

                if message["status"] == "check":
                    print(">> CHECK!")
                elif message["status"] == "checkmate":
                    winner = message["winner"]
                    print(f">> CHECKMATE! {winner.upper()} wins.")
                    exit()
                elif message["status"] == "stalemate":
                    print(">> STALEMATE! The game is a draw.")
                    exit()
                else:
                    print(f"Your turn: {current_turn == my_color}")

            elif message["type"] == "invalid":
                print("Invalid move! Try again.")

            elif message["type"] == "not_your_turn":
                print("Not your turn! Please wait.")

        except Exception as e:
            print(f"[ERROR] Lost connection to server: {e}")
            break

def listen_for_chat(chat_socket):
    while True:
        try:
            data = chat_socket.recv(1024).decode()
            if not data:
                break

            message = json.loads(data)
            
            if message["type"] == "chat":
                print(f"\n[{message['color'].upper()}] {message['content']}")
            elif message["type"] == "system":
                print(f"\n[SYSTEM] {message['content']}")
            
            # Print the input prompt again
            print("\nEnter move (e.g., e2e4) or type 'chat' to send a message:", end=" ")

        except Exception as e:
            print(f"[CHAT ERROR] Lost connection to chat server: {e}")
            break

def connect_to_chat():
    chat_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    chat_socket.connect(('127.0.0.1', 5556))
    
    # Send join message to chat server
    chat_socket.send(json.dumps({
        "type": "join",
        "game_id": game_id,
        "color": my_color
    }).encode())
    
    # Start chat listener thread
    threading.Thread(target=listen_for_chat, args=(chat_socket,), daemon=True).start()
    return chat_socket

def main():
    host = '127.0.0.1'
    port = 5555
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    threading.Thread(target=listen_for_updates, args=(client_socket,), daemon=True).start()

    chat_socket = None
    while True:
        user_input = input("\nEnter move (e.g., e2e4) or type 'chat' to send a message: ").strip()
        
        if user_input.lower() == "chat":
            if chat_socket is None:
                chat_socket = connect_to_chat()
            message = input("Enter your message: ").strip()
            if message:
                chat_socket.send(json.dumps({
                    "type": "chat",
                    "content": message
                }).encode())
        else:
            if user_input:
                client_socket.send(json.dumps({"type": "move", "move": user_input}).encode())


if __name__ == "__main__":
    main()