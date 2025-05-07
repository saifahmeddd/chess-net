import socket
import threading
import json
import chess

games = {}  # {game_id: {"board": Board, "players": [conn1, conn2], "turn": "white"}}
game_id = 1

def handle_client(conn, addr, player_color, game_id):
    print(f"[CONNECTED] {addr} as {player_color} in Game {game_id}")
    conn.send(json.dumps({"type": "init", "color": player_color}).encode())

    board = games[game_id]["board"]

    while True:
        try:
            data = conn.recv(1024).decode()
            if not data:
                break

            message = json.loads(data)

            if message["type"] == "move":
                move = message["move"]
                current_turn = games[game_id]["turn"]

                # Reject if it's not this player's turn
                if current_turn != player_color:
                    conn.send(json.dumps({"type": "not_your_turn"}).encode())
                    continue

                # Validate move
                try:
                    chess_move = chess.Move.from_uci(move)
                    if chess_move in board.legal_moves:
                        board.push(chess_move)

                        status = "normal"
                        if board.is_checkmate():
                            status = "checkmate"
                        elif board.is_stalemate():
                            status = "stalemate"
                        elif board.is_check():
                            status = "check"

                        # Switch turn only if game not over
                        if status not in ["checkmate", "stalemate"]:
                            next_turn = "black" if current_turn == "white" else "white"
                            games[game_id]["turn"] = next_turn
                        else:
                            next_turn = None  # No next turn, game ended

                        # Send update to both players
                        for player_conn in games[game_id]["players"]:
                            player_conn.send(json.dumps({
                                "type": "update",
                                "move": move,
                                "fen": board.fen(),
                                "turn": next_turn,
                                "status": status,
                                "winner": current_turn if status == "checkmate" else None
                            }).encode())

                    else:
                        conn.send(json.dumps({"type": "invalid"}).encode())

                except:
                    conn.send(json.dumps({"type": "invalid"}).encode())

        except Exception as e:
            print(f"[ERROR] {addr} disconnected: {e}")
            break

    conn.close()


def wait_for_players(server_socket):
    global game_id
    while True:
        print("[WAITING] Waiting for two players...")
        conn1, addr1 = server_socket.accept()
        conn1.send(json.dumps({"type": "wait"}).encode())

        conn2, addr2 = server_socket.accept()

        # Create new game
        board = chess.Board()
        games[game_id] = {
            "board": board,
            "players": [conn1, conn2],
            "turn": "white"
        }

        # Start threads for both players
        threading.Thread(target=handle_client, args=(conn1, addr1, "white", game_id), daemon=True).start()
        threading.Thread(target=handle_client, args=(conn2, addr2, "black", game_id), daemon=True).start()

        print(f"[GAME {game_id}] Started between {addr1} (white) and {addr2} (black)")
        game_id += 1


def main():
    host = '0.0.0.0'
    port = 5555
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"[STARTED] Server listening on {host}:{port}")

    wait_for_players(server_socket)


if __name__ == "__main__":
    main()