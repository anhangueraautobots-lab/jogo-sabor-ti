import pygame
import os
import json

# Configurações
SCREEN_WIDTH  = 400
SCREEN_HEIGHT = 300
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock  = pygame.time.Clock()
font   = pygame.font.SysFont("Arial", 20)

def record_chart(song_name):
    song_path  = os.path.join('songs', song_name)
    audio_file = os.path.join(song_path, 'som.mp3')

    if not os.path.exists(audio_file):
        print(f"Erro: {audio_file} nao encontrado!")
        return

    pygame.mixer.music.load(audio_file)
    recorded_notes = []

    print(f"Gravando: {song_name}. Prepare-se!")
    pygame.mixer.music.play()
    start_time = pygame.time.get_ticks()

    running = True
    while running:
        screen.fill((50, 50, 50))
        screen.blit(font.render(f"Gravando: {song_name}", True, (255,255,255)), (50, 50))
        screen.blit(font.render("A=Esq  S=Baixo  W=Cima  D=Dir", True, (200,200,200)), (30, 100))
        screen.blit(font.render("ESC para salvar e sair", True, (255,100,100)), (50, 200))

        current_time = pygame.time.get_ticks() - start_time

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                key_map = {pygame.K_a: 0, pygame.K_s: 1, pygame.K_w: 2, pygame.K_d: 3}
                if event.key in key_map:
                    recorded_notes.append({"time": current_time, "lane": key_map[event.key]})
                    print(f"Nota: {current_time}ms | lane {key_map[event.key]}")
                if event.key == pygame.K_ESCAPE:
                    running = False

        if not pygame.mixer.music.get_busy():
            running = False

        pygame.display.flip()
        clock.tick(60)

    output_path = os.path.join(song_path, 'data.json')
    with open(output_path, 'w') as f:
        json.dump({"notes": recorded_notes}, f, indent=2)
    print(f"Salvo em: {output_path}")

if __name__ == "__main__":
    nome = input("Nome da pasta da musica (dentro de /songs): ")
    record_chart(nome)
    pygame.quit()