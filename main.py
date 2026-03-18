import pygame
import os
import json

# Configurações Básicas
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
LANE_X = [200, 300, 400, 500]  # Posição X de cada uma das 4 colunas
HIT_ZONE_Y = 500              # Linha onde o player deve apertar a nota
NOTE_SPEED = 0.5              # Pixels por milissegundo

# Definição de Cores (R, G, B)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY_TARGET = (150, 150, 150) # Cor para os alvos fixos

# Cores fixas para cada uma das 4 colunas
# Lane 0: Roxo, Lane 1: Verde, Lane 2: Vermelho, Lane 3: Amarelo
LANE_COLORS = [
    (150, 50, 250),  # Roxo
    (50, 200, 50),   # Verde
    (220, 50, 50),   # Vermelho
    (250, 200, 50)   # Amarelo
]

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

def load_songs():
    if not os.path.exists('songs'):
        os.makedirs('songs')
        return []
    return [f for f in os.listdir('songs') if os.path.isdir(os.path.join('songs', f))]

def play_game(song_name):
    song_path = os.path.join('songs', song_name)
    json_path = os.path.join(song_path, 'data.json')
    
    if not os.path.exists(json_path):
        print(f"Erro: data.json não encontrado em {song_path}")
        return True

    pygame.mixer.music.load(os.path.join(song_path, 'som.mp3'))
    
    with open(json_path, 'r') as f:
        chart = json.load(f)
    
    notes = chart['notes']
    
    # DEBUG: print para saber se as notas foram carregadas
    print(f"Jogo iniciado para: {song_name}. Notas carregadas: {len(notes)}")
    
    pygame.mixer.music.play()
    
    # Atraso de 1 segundo antes que o timing comece, para dar tempo de ver as notas
    start_delay_ms = 1000
    start_time = pygame.time.get_ticks() + start_delay_ms
    
    running = True
    while running:
        screen.fill((30, 30, 30)) # Fundo escuro

        # Atualizar o tempo atual com base no atraso inicial
        current_time = pygame.time.get_ticks() - start_time
        
        # DEBUG: print do tempo atual para monitorar
        # print(f"Tempo atual: {current_time}ms") # Descomente para depurar

        # --- Desenhar as Zonas de Acerto (Alvos fixos em quadrados arredondados) ---
        target_size = 60
        target_border_radius = 10
        target_margin = 15
        
        for i, x in enumerate(LANE_X):
            rect = pygame.Rect(0, 0, target_size, target_size)
            rect.center = (x, HIT_ZONE_Y)
            # Desenhar o contorno
            pygame.draw.rect(screen, GRAY_TARGET, rect, border_radius=target_border_radius, width=3)
            # Desenhar o interior mais escuro
            pygame.draw.rect(screen, (70, 70, 70), rect, border_radius=target_border_radius)

        # --- Processar Eventos (Controles) ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                key_map = {pygame.K_a: 0, pygame.K_s: 1, pygame.K_w: 2, pygame.K_d: 3,
                           pygame.K_LEFT: 0, pygame.K_DOWN: 1, pygame.K_UP: 2, pygame.K_RIGHT: 3}
                
                if event.key in key_map:
                    lane = key_map[event.key]
                    for n in notes[:]:
                        if n['lane'] == lane:
                            note_y = HIT_ZONE_Y - (n['time'] - current_time) * NOTE_SPEED
                            if abs(note_y - HIT_ZONE_Y) < 50: # Margem de acerto
                                notes.remove(n)
                                print(f"Boa! Hit na lane {lane}")

        # --- Desenhar Notas que estão caindo (Quadrados Arredondados Coloridos) ---
        note_width = target_size
        note_height = 30 # Altura fixa para notas normais
        note_border_radius = 8
        
        for n in notes:
            note_y = HIT_ZONE_Y - (n['time'] - current_time) * NOTE_SPEED
            
            # Só desenha se estiver na tela
            if -note_height < note_y < SCREEN_HEIGHT:
                lane = n['lane']
                note_color = LANE_COLORS[lane]
                
                # Criar o retângulo da nota
                note_rect = pygame.Rect(0, 0, note_width, note_height)
                note_rect.center = (LANE_X[lane], int(note_y))
                
                # Desenhar o quadrado arredondado preenchido com a cor da lane
                pygame.draw.rect(screen, note_color, note_rect, border_radius=note_border_radius)
                
                # Opcional: Desenhar um contorno para destacar
                pygame.draw.rect(screen, BLACK, note_rect, border_radius=note_border_radius, width=2)
            
            # Remove nota se ela passar do limite inferior sem ser clicada
            if note_y > SCREEN_HEIGHT + 50:
                notes.remove(n)

        if not pygame.mixer.music.get_busy() and notes == []: # Música acabou e não há mais notas
            running = False

        pygame.display.flip()
        clock.tick(60)
    return True

def main_menu():
    songs = load_songs()
    selected = 0
    font = pygame.font.SysFont("Arial", 40, bold=True)
    
    if not songs:
        screen.fill(BLACK)
        txt = font.render("Nenhuma música encontrada! Crie uma pasta e um .json", True, WHITE)
        screen.blit(txt, (SCREEN_WIDTH//2 - 350, SCREEN_HEIGHT//2))
        pygame.display.flip()
        pygame.time.wait(3000)
        return

    while True:
        screen.fill((20, 20, 20))
        
        title = font.render("SELECIONE A MÚSICA", True, LANE_COLORS[selected])
        screen.blit(title, (SCREEN_WIDTH//2 - 200, 50))

        for i, song in enumerate(songs):
            color = LANE_COLORS[i % 4] if i == selected else WHITE
            arrow = "> " if i == selected else "  "
            txt = font.render(f"{arrow}{song}", True, color)
            screen.blit(txt, (SCREEN_WIDTH//2 - 100, 150 + i * 60))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(songs)
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(songs)
                if event.key == pygame.K_RETURN:
                    if not play_game(songs[selected]):
                        return

        pygame.display.flip()

if __name__ == "__main__":
    main_menu()
    pygame.quit()