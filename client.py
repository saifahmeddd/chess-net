import socket
import threading
import json

my_color = None
current_turn = None

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


def main():
    host = '127.0.0.1'
    port = 5555
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    threading.Thread(target=listen_for_updates, args=(client_socket,), daemon=True).start()

    while True:
        move = input("Enter your move (e.g., e2e4): ").strip()
        if move == "":
            continue
        client_socket.send(json.dumps({"type": "move", "move": move}).encode())


if __name__ == "__main__":
    main()