import socket
import threading
import json
import chess

games = {}  # {game_id: {"board": Board, "players": [conn1, conn2], "spectators": [conn1, conn2, ...], "turn": "white"}}
game_id = 1

def broadcast_to_spectators(game_id, message):
    if game_id in games and "spectators" in games[game_id]:
        for spectator in games[game_id]["spectators"]:
            try:
                spectator.send(json.dumps(message).encode())
            except:
                # Remove disconnected spectators
                games[game_id]["spectators"].remove(spectator)

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

                        # Create update message
                        update_message = {
                            "type": "update",
                            "move": move,
                            "fen": board.fen(),
                            "turn": next_turn,
                            "status": status,
                            "winner": current_turn if status == "checkmate" else None
                        }

                        # Send update to both players and spectators
                        for player_conn in games[game_id]["players"]:
                            player_conn.send(json.dumps(update_message).encode())
                        
                        # Broadcast to spectators
                        broadcast_to_spectators(game_id, update_message)

                    else:
                        conn.send(json.dumps({"type": "invalid"}).encode())

                except:
                    conn.send(json.dumps({"type": "invalid"}).encode())

        except Exception as e:
            print(f"[ERROR] {addr} disconnected: {e}")
            break

    conn.close()

def handle_spectator(conn, addr, game_id):
    print(f"[SPECTATOR] {addr} joined Game {game_id}")
    
    if game_id not in games:
        conn.send(json.dumps({"type": "error", "message": "Game not found"}).encode())
        conn.close()
        return

    # Initialize spectator list if not exists
    if "spectators" not in games[game_id]:
        games[game_id]["spectators"] = []
    
    games[game_id]["spectators"].append(conn)

    # Send initial board state
    board = games[game_id]["board"]
    conn.send(json.dumps({
        "type": "update",
        "fen": board.fen(),
        "turn": games[game_id]["turn"],
        "status": "check" if board.is_check() else "normal"
    }).encode())

    while True:
        try:
            data = conn.recv(1024).decode()
            if not data:
                break
        except:
            break

    # Remove spectator when disconnected
    if game_id in games and "spectators" in games[game_id]:
        games[game_id]["spectators"].remove(conn)
    conn.close()

def wait_for_connections(server_socket):
    global game_id
    while True:
        print("[WAITING] Waiting for connections...")
        conn, addr = server_socket.accept()
        
        try:
            # Receive initial message to determine if it's a player or spectator
            data = conn.recv(1024).decode()
            message = json.loads(data)
            
            if message["type"] == "spectator":
                # Handle spectator connection
                threading.Thread(target=handle_spectator, args=(conn, addr, message["game_id"]), daemon=True).start()
            else:
                # Handle player connection
                conn1 = conn
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
                threading.Thread(target=handle_client, args=(conn1, addr, "white", game_id), daemon=True).start()
                threading.Thread(target=handle_client, args=(conn2, addr2, "black", game_id), daemon=True).start()

                print(f"[GAME {game_id}] Started between {addr} (white) and {addr2} (black)")
                game_id += 1

        except Exception as e:
            print(f"[ERROR] Failed to handle connection from {addr}: {e}")
            conn.close()

def main():
    host = '0.0.0.0'
    port = 5555
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"[STARTED] Server listening on {host}:{port}")

    wait_for_connections(server_socket)

if __name__ == "__main__":
    main()