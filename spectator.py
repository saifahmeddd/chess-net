# For now, spectators can connect to the server and observe FEN updates.

import socket
import json
import chess
import sys

def display_board(fen):
    board = chess.Board(fen)
    print("\nCurrent Board Position:")
    print(board)
    print(f"FEN: {fen}\n")

def main():
    if len(sys.argv) != 3:
        print("Usage: python spectator.py <server_ip> <game_id>")
        return

    server_ip = sys.argv[1]
    game_id = int(sys.argv[2])
    port = 5555

    try:
        # Connect to server
        spectator_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        spectator_socket.connect((server_ip, port))
        
        # Send spectator request
        spectator_socket.send(json.dumps({
            "type": "spectator",
            "game_id": game_id
        }).encode())

        print(f"Connected to server as spectator for Game {game_id}")
        print("Waiting for game updates...")

        while True:
            try:
                data = spectator_socket.recv(1024).decode()
                if not data:
                    break

                message = json.loads(data)
                
                if message["type"] == "update":
                    display_board(message["fen"])
                    if message["status"] == "checkmate":
                        print(f"Game Over! {message['winner'].capitalize()} wins by checkmate!")
                        break
                    elif message["status"] == "stalemate":
                        print("Game Over! Stalemate!")
                        break
                    elif message["status"] == "check":
                        print("Check!")
                    print(f"Next to move: {message['turn'].capitalize()}")
                
                elif message["type"] == "error":
                    print(f"Error: {message['message']}")
                    break

            except json.JSONDecodeError:
                print("Invalid message received from server")
                break
            except Exception as e:
                print(f"Error: {e}")
                break

    except ConnectionRefusedError:
        print("Could not connect to server. Make sure the server is running and the IP is correct.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        spectator_socket.close()

if __name__ == "__main__":
    main()
