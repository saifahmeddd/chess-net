import socket
import threading
import json
import select
import sys

my_color = None
current_turn = "white"  # Initialize with white's turn
chat_socket = None

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
                if my_color == "white":
                    print("You can make the first move!")

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
                print(f"\n[CHAT] {message['message']}")
                print("Enter 'p' to play or 'c' to chat: ", end='', flush=True)
        except Exception as e:
            print(f"\n[ERROR] Lost connection to chat server: {e}")
            break

def main():
    host = '127.0.0.1'
    game_port = 5555
    chat_port = 5556

    # Connect to game server
    game_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    game_socket.connect((host, game_port))

    # Connect to chat server
    global chat_socket
    chat_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    chat_socket.connect((host, chat_port))

    # Start listening threads
    threading.Thread(target=listen_for_updates, args=(game_socket,), daemon=True).start()
    threading.Thread(target=listen_for_chat, args=(chat_socket,), daemon=True).start()

    print("Connected to both game and chat servers!")
    print("Enter 'p' to play or 'c' to chat")

    while True:
        mode = input("Enter 'p' to play or 'c' to chat: ").strip().lower()
        
        if mode == 'p':
            if current_turn != my_color:
                print("Not your turn! Please wait.")
                continue
                
            move = input("Enter your move (e.g., e2e4): ").strip()
            if move == "":
                continue
            game_socket.send(json.dumps({"type": "move", "move": move}).encode())
            
        elif mode == 'c':
            message = input("Enter your message: ").strip()
            if message == "":
                continue
            chat_socket.send(json.dumps({
                "type": "chat",
                "message": f"{my_color.upper()}: {message}"
            }).encode())
            
        else:
            print("Invalid mode! Please enter 'p' for play or 'c' for chat.")

if __name__ == "__main__":
    main()