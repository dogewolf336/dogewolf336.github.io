import pygame
import socket
import threading

# Configuration
SERVER_IP = "0.0.0.0"  # Change to your server's IP for deployment
SERVER_PORT = 5555
WIDTH, HEIGHT = 800, 600
PADDLE_WIDTH, PADDLE_HEIGHT = 10, 100
BALL_RADIUS = 10
FPS = 60

# Game State
player1_y = HEIGHT // 2 - PADDLE_HEIGHT // 2
player2_y = HEIGHT // 2 - PADDLE_HEIGHT // 2
ball_x, ball_y = WIDTH // 2, HEIGHT // 2
ball_dx, ball_dy = 5, 5

player1_score = 0
player2_score = 0

# Networking
clients = []

def handle_client(conn, addr):
    global player1_y, player2_y
    print(f"New connection from {addr}")
    clients.append(conn)

    while True:
        try:
            data = conn.recv(1024).decode("utf-8")
            if not data:
                break
            if addr == clients[0].getpeername():
                player1_y = int(data)
            else:
                player2_y = int(data)
            broadcast(data, conn)
        except:
            break

    conn.close()
    clients.remove(conn)

def broadcast(message, sender_conn):
    for client in clients:
        if client != sender_conn:
            client.send(message.encode("utf-8"))

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((SERVER_IP, SERVER_PORT))
    server.listen(2)
    print("Server is running...")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()

def start_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_IP, SERVER_PORT))

    def receive_data():
        global player2_y
        while True:
            try:
                data = client_socket.recv(1024).decode("utf-8")
                player2_y = int(data)
            except:
                break

    threading.Thread(target=receive_data).start()

    return client_socket

def game_loop(client_socket):
    global ball_x, ball_y, ball_dx, ball_dy, player1_y, player2_y

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Pong Online")

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_w] and player1_y > 0:
            player1_y -= 5
        if keys[pygame.K_s] and player1_y < HEIGHT - PADDLE_HEIGHT:
            player1_y += 5

        # Send player1's paddle position to the server
        client_socket.send(f"{player1_y}".encode("utf-8"))

        # Update ball position
        ball_x += ball_dx
        ball_y += ball_dy

        # Ball Collision with walls
        if ball_y <= 0 or ball_y >= HEIGHT - BALL_RADIUS:
            ball_dy *= -1
        if ball_x <= 0 or ball_x >= WIDTH - BALL_RADIUS:
            ball_dx *= -1

        # Draw game objects
        screen.fill((0, 0, 0))
        pygame.draw.rect(screen, (255, 255, 255), (50, player1_y, PADDLE_WIDTH, PADDLE_HEIGHT))
        pygame.draw.rect(screen, (255, 255, 255), (WIDTH - 50 - PADDLE_WIDTH, player2_y, PADDLE_WIDTH, PADDLE_HEIGHT))
        pygame.draw.circle(screen, (255, 255, 255), (ball_x, ball_y), BALL_RADIUS)
        pygame.display.flip()

        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    mode = input("Enter mode (server/client): ").strip().lower()

    if mode == "server":
        start_server()
    elif mode == "client":
        client_socket = start_client()
        game_loop(client_socket)
    else:
        print("Invalid mode. Enter 'server' or 'client'.")