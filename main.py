<<<<<<< HEAD
import pygame
import os
import json
import sys
import math
import random

# ==============================================================================
# CONFIGURAÇÕES BÁSICAS
# ==============================================================================
SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720
FPS           = 60

# 4 lanes de 55px com gap de 15px entre elas = bloco de 275px, centralizado em 1280
_LANE_START = (1280 - 275) // 2   # 502
LANE_X     = [_LANE_START + i * 70 + 27 for i in range(4)]  # [529, 599, 669, 739]
HIT_ZONE_Y = 620
NOTE_SPEED = 0.4

WHITE     = (255, 255, 255)
BLACK     = (0,   0,   0)
DARK_GRAY = (45,  45,  45)
MID_GRAY  = (70,  70,  70)
GRAY      = (140, 140, 140)
TITLE_CLR = (20,  20,  20)

LANE_COLORS = [
    (150, 50,  250),
    (50,  200, 50),
    (220, 50,  50),
    (250, 200, 50),
]

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Sabor - Videogame")
clock = pygame.time.Clock()

# ==============================================================================
# FONTES PIXELADAS
# ==============================================================================
def load_pixel_font(size, italic=False):
    for name in ["Courier New", "Lucida Console", "Consolas", "monospace"]:
        try:
            return pygame.font.SysFont(name, size, bold=True, italic=italic)
        except:
            pass
    return pygame.font.Font(None, size)

font_title = load_pixel_font(72, italic=True)
font_sub   = load_pixel_font(22, italic=False)
font_btn   = load_pixel_font(36, italic=False)
font_hud   = load_pixel_font(24, italic=False)
font_med   = load_pixel_font(30, italic=False)
font_big   = load_pixel_font(52, italic=False)

# ==============================================================================
# VOLUME
# ==============================================================================
volume = 0.7
pygame.mixer.music.set_volume(volume)

# ==============================================================================
# CARREGAMENTO DE IMAGENS
# Estrutura esperada em assets/:
#   icone.png              ← ícone do jogo (reservado)
#   PlayerParado.png
#   PlayerCima.png
#   PlayerBaixo.png
#   PlayerEsquerda.png
#   PlayerDireita.png
#   RoboParado.png
#   RoboCima.png
#   RoboBaixo.png
#   RoboEsquerda.png
#   RoboDireita.png
#   vida_icone.png         ← ícone deslizante da barra de vida
# ==============================================================================
ASSETS = "assets"

def try_load(filename, size=None):
    path = os.path.join(ASSETS, filename)
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, size) if size else img
    return None

CHAR_SIZE = (160, 220)

player_sprites = {
    "parado":   try_load("PlayerParado.png",   CHAR_SIZE),
    "cima":     try_load("PlayerCima.png",     CHAR_SIZE),
    "baixo":    try_load("PlayerBaixo.png",    CHAR_SIZE),
    "esquerda": try_load("PlayerEsquerda.png", CHAR_SIZE),
    "direita":  try_load("PlayerDireita.png",  CHAR_SIZE),
}

robo_sprites = {
    "parado":   try_load("RoboParado.png",   CHAR_SIZE),
    "cima":     try_load("RoboCima.png",     CHAR_SIZE),
    "baixo":    try_load("RoboBaixo.png",    CHAR_SIZE),
    "esquerda": try_load("RoboEsquerda.png", CHAR_SIZE),
    "direita":  try_load("RoboDireita.png",  CHAR_SIZE),
}

vida_icon = try_load("vida_icone.png", (32, 32))

# ÍCONE DO JOGO (reservado) — descomente quando tiver o arquivo:
# game_icon = try_load("icone.png", (64, 64))
# if game_icon: pygame.display.set_icon(game_icon)

# ==============================================================================
# PERSONAGEM ANIMADO
# ==============================================================================
LANE_POSE = {0: "esquerda", 1: "baixo", 2: "cima", 3: "direita"}

class Character:
    POSE_FRAMES = 20

    def __init__(self, sprites, x, y, flip=False):
        self.sprites    = sprites
        self.x          = x
        self.y          = y
        self.flip       = flip
        self.pose       = "parado"
        self.pose_timer = 0
        self.idle_timer = 0

    def set_pose(self, pose):
        self.pose       = pose
        self.pose_timer = self.POSE_FRAMES

    def update(self):
        if self.pose_timer > 0:
            self.pose_timer -= 1
            if self.pose_timer == 0:
                self.pose = "parado"
        self.idle_timer += 1

    def draw(self, surface):
        bob = int(4 * abs(math.sin(self.idle_timer * 0.05))) if self.pose == "parado" else 0
        sprite = self.sprites.get(self.pose) or self.sprites.get("parado")

        if sprite:
            img  = pygame.transform.flip(sprite, self.flip, False) if self.flip else sprite
            rect = img.get_rect(midbottom=(self.x, self.y + bob))
            surface.blit(img, rect)
        else:
            color = (80, 180, 255) if not self.flip else (255, 100, 80)
            label = "PLAYER" if not self.flip else "ROBO"
            ph = pygame.Rect(0, 0, 120, 180)
            ph.midbottom = (self.x, self.y + bob)
            pygame.draw.rect(surface, color, ph, border_radius=14)
            pygame.draw.rect(surface, WHITE, ph, border_radius=14, width=2)
            t = font_hud.render(label, True, WHITE)
            surface.blit(t, t.get_rect(center=ph.center))

# ==============================================================================
# BOTÃO ANIMADO
# ==============================================================================
class Button:
    def __init__(self, text, x, y, base_size=36, hover_size=46, color=WHITE, hover_color=None):
        self.text        = text
        self.x           = x
        self.y           = y
        self.base_size   = base_size
        self.hover_size  = hover_size
        self.color       = color
        self.hover_color = hover_color or LANE_COLORS[0]
        self.cur_size    = float(base_size)
        self.hovered     = False

    def _font(self):
        return load_pixel_font(int(self.cur_size))

    def _rect(self):
        txt = self._font().render(self.text, True, self.color)
        return txt.get_rect(center=(self.x, self.y))

    def update(self):
        target = self.hover_size if self.hovered else self.base_size
        self.cur_size += (target - self.cur_size) * 0.18

    def check_hover(self, mp):
        self.hovered = self._rect().collidepoint(mp)

    def is_clicked(self, mp, event):
        return (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self._rect().collidepoint(mp))

    def draw(self, surface):
        f     = self._font()
        color = self.hover_color if self.hovered else self.color
        if self.hovered:
            sh = f.render(self.text, True, BLACK)
            surface.blit(sh, sh.get_rect(center=(self.x+2, self.y+2)))
        txt = f.render(self.text, True, color)
        surface.blit(txt, txt.get_rect(center=(self.x, self.y)))

# ==============================================================================
# UTILITÁRIOS
# ==============================================================================
def draw_bg(surface):
    surface.fill(DARK_GRAY)

def draw_title(surface, cx, y):
    title_str = "Sabor - Videogame"
    for dx, dy in [(-3,0),(3,0),(0,-3),(0,3),(-3,-3),(3,-3),(-3,3),(3,3)]:
        sh = font_title.render(title_str, True, LANE_COLORS[0])
        surface.blit(sh, sh.get_rect(center=(cx+dx, y+dy)))
    txt = font_title.render(title_str, True, TITLE_CLR)
    surface.blit(txt, txt.get_rect(center=(cx, y)))
    sub = font_sub.render("Feito pela equipe Sabor T.I", True, GRAY)
    surface.blit(sub, sub.get_rect(center=(cx, y + 60)))

def load_songs():
    if not os.path.exists("songs"):
        os.makedirs("songs")
        return []
    return [f for f in os.listdir("songs") if os.path.isdir(os.path.join("songs", f))]

# ==============================================================================
# BARRA DE VIDA
# pos=0.0 → robô vencendo | pos=1.0 → player perdeu (game over)
# ==============================================================================
class HealthBar:
    BAR_W = 500
    BAR_H = 16

    def __init__(self, cx, y):
        self.cx  = cx
        self.y   = y
        self.pos = 0.5
        self.x0  = cx - self.BAR_W // 2
        self.x1  = cx + self.BAR_W // 2

    def hit(self):
        self.pos = max(0.0, self.pos - 0.04)

    def miss(self):
        self.pos = min(1.0, self.pos + 0.06)

    @property
    def dead(self):
        return self.pos >= 1.0

    def draw(self, surface):
        # Trilha da barra — branca com baixa opacidade simulada via cinza claro
        bar = pygame.Rect(self.x0, self.y - self.BAR_H//2, self.BAR_W, self.BAR_H)
        pygame.draw.rect(surface, (90, 90, 90), bar, border_radius=8)
        # Borda branca na trilha
        pygame.draw.rect(surface, WHITE, bar, border_radius=8, width=2)

        r_lbl = font_hud.render("ROBÔ", True, GRAY)
        p_lbl = font_hud.render("PLAYER", True, GRAY)
        surface.blit(r_lbl, r_lbl.get_rect(midright=(self.x0 - 8, self.y)))
        surface.blit(p_lbl, p_lbl.get_rect(midleft=(self.x1 + 8, self.y)))

        # Ponto deslizante branco
        icon_x = int(self.x0 + self.BAR_W * self.pos)
        if vida_icon:
            surface.blit(vida_icon, vida_icon.get_rect(center=(icon_x, self.y)))
        else:
            pygame.draw.circle(surface, WHITE, (icon_x, self.y), 13)
            pygame.draw.circle(surface, DARK_GRAY, (icon_x, self.y), 7)

# ==============================================================================
# ROBÔ IA
# ==============================================================================
class RoboAI:
    def __init__(self):
        self.pending = []

    def schedule(self, note, current_time):
        self.pending.append((note, current_time + random.randint(0, 80)))

    def update(self, notes, current_time, robo_char):
        done = []
        for item in self.pending:
            n, t = item
            if current_time >= t:
                if n in notes:
                    notes.remove(n)
                    robo_char.set_pose(LANE_POSE.get(n["lane"], "parado"))
                done.append(item)
        for item in done:
            self.pending.remove(item)

# ==============================================================================
# GAME OVER
# ==============================================================================
def game_over_screen(song_name):
    cx        = SCREEN_WIDTH // 2
    btn_retry = Button("Tentar Novamente", cx, 450, hover_color=LANE_COLORS[1])
    btn_menu  = Button("Menu Principal",  cx, 530, hover_color=LANE_COLORS[3])

    while True:
        mp = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "menu"
            if btn_retry.is_clicked(mp, event): return "retry"
            if btn_menu.is_clicked(mp, event):  return "menu"

        for btn in [btn_retry, btn_menu]:
            btn.check_hover(mp)
            btn.update()

        draw_bg(screen)

        l1 = font_big.render("Xii... Paizão,", True, LANE_COLORS[2])
        l2 = font_big.render("Sem sabor esse player Ai!!", True, LANE_COLORS[2])
        screen.blit(l1, l1.get_rect(center=(cx, 300)))
        screen.blit(l2, l2.get_rect(center=(cx, 370)))

        for btn in [btn_retry, btn_menu]:
            btn.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

# ==============================================================================
# JOGO
# ==============================================================================
def play_game(song_name):
    song_path = os.path.join("songs", song_name)
    json_path = os.path.join(song_path, "data.json")

    if not os.path.exists(json_path):
        print(f"data.json não encontrado em {song_path}")
        return "back"

    pygame.mixer.music.load(os.path.join(song_path, "som.mp3"))
    pygame.mixer.music.set_volume(volume)

    with open(json_path, "r") as f:
        chart = json.load(f)

    # Player e robô têm listas COMPLETAMENTE separadas
    player_notes = [dict(n) for n in chart["notes"]]
    robo_notes   = [dict(n) for n in chart["notes"]]
    robo_pending = list(robo_notes)

    cx = SCREEN_WIDTH // 2
    player_char = Character(player_sprites, x=SCREEN_WIDTH - 200, y=HIT_ZONE_Y - 10)
    robo_char   = Character(robo_sprites,   x=200,                y=HIT_ZONE_Y - 10, flip=True)

    health   = HealthBar(cx, 45)
    robo_ai  = RoboAI()
    score    = 0
    misses   = 0
    feedback = []

    pygame.mixer.music.play()
    start_time = pygame.time.get_ticks() + 1000

    running = True
    while running:
        draw_bg(screen)
        current_time = pygame.time.get_ticks() - start_time

        # Agenda notas pro robô (lista própria, não interfere no player)
        for n in robo_pending[:]:
            if HIT_ZONE_Y - (n["time"] - current_time) * NOTE_SPEED >= HIT_ZONE_Y - 80:
                robo_ai.schedule(n, current_time)
                robo_pending.remove(n)

        robo_ai.update(robo_notes, current_time, robo_char)
        player_char.update()
        robo_char.update()

        # Zonas de acerto
        for i, x in enumerate(LANE_X):
            rect = pygame.Rect(0, 0, 55, 55)
            rect.center = (x, HIT_ZONE_Y)
            pygame.draw.rect(screen, MID_GRAY, rect, border_radius=10)
            pygame.draw.rect(screen, LANE_COLORS[i], rect, border_radius=10, width=3)

        # Setas abaixo das zonas de acerto
        # Imagens: SetaEsquerda.png, SetaBaixo.png, SetaCima.png, SetaDireita.png
        # Coloque os arquivos em assets/ e descomente as linhas abaixo:
        # seta_imgs = [
        #     try_load("SetaEsquerda.png", (45, 45)),
        #     try_load("SetaBaixo.png",    (45, 45)),
        #     try_load("SetaCima.png",     (45, 45)),
        #     try_load("SetaDireita.png",  (45, 45)),
        # ]
        # for i, x in enumerate(LANE_X):
        #     if seta_imgs[i]:
        #         r = seta_imgs[i].get_rect(midtop=(x, HIT_ZONE_Y + 35))
        #         screen.blit(seta_imgs[i], r)
        # Placeholder visual enquanto as imagens não estiverem prontas:
        seta_chars = ["←", "↓", "↑", "→"]
        for i, x in enumerate(LANE_X):
            st = font_hud.render(seta_chars[i], True, LANE_COLORS[i])
            screen.blit(st, st.get_rect(midtop=(x, HIT_ZONE_Y + 35)))

        # Eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.mixer.music.stop()
                    return "back"
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()

                key_map = {
                    pygame.K_a: 0, pygame.K_LEFT:  0,
                    pygame.K_s: 1, pygame.K_DOWN:  1,
                    pygame.K_w: 2, pygame.K_UP:    2,
                    pygame.K_d: 3, pygame.K_RIGHT: 3,
                }
                if event.key in key_map:
                    lane = key_map[event.key]
                    player_char.set_pose(LANE_POSE[lane])
                    hit = False
                    for n in player_notes[:]:
                        if n["lane"] == lane:
                            note_y = HIT_ZONE_Y - (n["time"] - current_time) * NOTE_SPEED
                            if abs(note_y - HIT_ZONE_Y) < 55:
                                player_notes.remove(n)
                                score += 100
                                health.hit()
                                hit = True
                                feedback.append(["ÓTIMO!", LANE_X[lane], HIT_ZONE_Y-55, 45, LANE_COLORS[1]])
                                break
                    if not hit:
                        misses += 1
                        health.miss()
                        feedback.append(["MISS!", LANE_X[lane], HIT_ZONE_Y-55, 45, LANE_COLORS[2]])

        # Notas caindo (apenas as do player)
        for n in player_notes[:]:
            note_y = HIT_ZONE_Y - (n["time"] - current_time) * NOTE_SPEED
            if -28 < note_y < SCREEN_HEIGHT:
                nr = pygame.Rect(0, 0, 55, 28)
                nr.center = (LANE_X[n["lane"]], int(note_y))
                pygame.draw.rect(screen, LANE_COLORS[n["lane"]], nr, border_radius=7)
                pygame.draw.rect(screen, BLACK, nr, border_radius=7, width=2)
            if note_y > SCREEN_HEIGHT + 50:
                player_notes.remove(n)
                misses += 1
                health.miss()

        # Personagens
        robo_char.draw(screen)
        player_char.draw(screen)

        # Barra de vida
        health.draw(screen)

        # HUD
        screen.blit(font_hud.render(f"Score: {score}",   True, WHITE),           (20, SCREEN_HEIGHT-55))
        screen.blit(font_hud.render(f"Misses: {misses}", True, LANE_COLORS[2]),   (20, SCREEN_HEIGHT-30))
        esc = font_hud.render("ESC=Menu  F11=Fullscreen", True, MID_GRAY)
        screen.blit(esc, esc.get_rect(bottomright=(SCREEN_WIDTH-10, SCREEN_HEIGHT-10)))

        # Feedback
        for fb in feedback[:]:
            fb[3] -= 1
            fly = fb[2] - (45 - fb[3])
            t   = font_hud.render(fb[0], True, fb[4])
            screen.blit(t, t.get_rect(center=(fb[1], fly)))
            if fb[3] <= 0:
                feedback.remove(fb)

        # Game over
        if health.dead:
            pygame.mixer.music.stop()
            r = game_over_screen(song_name)
            return play_game(song_name) if r == "retry" else "back"

        if not pygame.mixer.music.get_busy() and not player_notes:
            running = False

        pygame.display.flip()
        clock.tick(FPS)

    return result_screen(score, misses)

# ==============================================================================
# RESULTADO
# ==============================================================================
def result_screen(score, misses):
    cx       = SCREEN_WIDTH // 2
    btn_back = Button("← Menu Principal", cx, 470, hover_color=LANE_COLORS[1])

    while True:
        mp = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "quit"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return "back"
            if btn_back.is_clicked(mp, event): return "back"

        btn_back.check_hover(mp)
        btn_back.update()
        draw_bg(screen)
        draw_title(screen, cx, 130)

        screen.blit(font_big.render("RESULTADO", True, WHITE),                   font_big.render("RESULTADO", True, WHITE).get_rect(center=(cx, 250)))
        screen.blit(font_btn.render(f"Score:  {score}",   True, WHITE),          font_btn.render(f"Score:  {score}",   True, WHITE).get_rect(center=(cx, 330)))
        screen.blit(font_btn.render(f"Misses: {misses}",  True, LANE_COLORS[2]), font_btn.render(f"Misses: {misses}",  True, LANE_COLORS[2]).get_rect(center=(cx, 390)))
        btn_back.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

# ==============================================================================
# CONFIGURAÇÕES
# ==============================================================================
def settings_menu():
    global volume
    cx       = SCREEN_WIDTH // 2
    btn_back = Button("← Voltar", cx, 560, base_size=28, hover_size=36, hover_color=GRAY)
    sx, sw, sy = cx - 200, 400, 350
    dragging = False

    while True:
        mp = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return
            if btn_back.is_clicked(mp, event): return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if sx <= mp[0] <= sx+sw and sy-15 <= mp[1] <= sy+15:
                    dragging = True
            if event.type == pygame.MOUSEBUTTONUP:
                dragging = False

        if dragging:
            volume = max(0.0, min(1.0, (mp[0]-sx)/sw))
            pygame.mixer.music.set_volume(volume)

        btn_back.check_hover(mp)
        btn_back.update()
        draw_bg(screen)
        draw_title(screen, cx, 130)

        lbl = font_btn.render("Volume da Música", True, WHITE)
        screen.blit(lbl, lbl.get_rect(center=(cx, 280)))

        pygame.draw.rect(screen, MID_GRAY,       (sx, sy-6, sw, 12), border_radius=6)
        pygame.draw.rect(screen, LANE_COLORS[3], (sx, sy-6, int(sw*volume), 12), border_radius=6)
        pygame.draw.circle(screen, WHITE, (sx+int(sw*volume), sy), 14)

        pct = font_hud.render(f"{int(volume*100)}%", True, GRAY)
        screen.blit(pct, pct.get_rect(center=(cx, sy+40)))
        btn_back.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

# ==============================================================================
# SELEÇÃO DE MÚSICAS
# ==============================================================================
def song_select_menu():
    songs    = load_songs()
    cx       = SCREEN_WIDTH // 2
    btn_back = Button("← Voltar", cx, 640, base_size=28, hover_size=36, hover_color=GRAY)

    if not songs:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: return "quit"
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return "back"
            draw_bg(screen)
            draw_title(screen, cx, 120)
            m = font_med.render("Nenhuma música encontrada!", True, LANE_COLORS[2])
            h = font_hud.render("Crie songs/<nome>/som.mp3 e data.json", True, GRAY)
            screen.blit(m, m.get_rect(center=(cx, 340)))
            screen.blit(h, h.get_rect(center=(cx, 390)))
            pygame.display.flip()
            clock.tick(FPS)

    buttons = [Button(f"Fase {i+1}", cx, 240 + i*70, hover_color=LANE_COLORS[i%4]) for i, s in enumerate(songs)]

    while True:
        mp = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "quit"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return "back"
            if btn_back.is_clicked(mp, event): return "back"
            for i, btn in enumerate(buttons):
                if btn.is_clicked(mp, event):
                    r = play_game(songs[i])
                    if r == "quit": return "quit"

        for btn in buttons + [btn_back]:
            btn.check_hover(mp)
            btn.update()

        draw_bg(screen)
        draw_title(screen, cx, 110)
        sep = font_med.render("── Selecione a Fase ──", True, GRAY)
        screen.blit(sep, sep.get_rect(center=(cx, 190)))
        for btn in buttons + [btn_back]:
            btn.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

# ==============================================================================
# MENU PRINCIPAL
# ==============================================================================
def main_menu():
    cx = SCREEN_WIDTH // 2
    btn_start  = Button("Começar",       cx, 380, hover_color=LANE_COLORS[1])
    btn_config = Button("Configurações", cx, 460, hover_color=LANE_COLORS[3])
    btn_quit   = Button("Sair",          cx, 540, hover_color=LANE_COLORS[2])
    buttons    = [btn_start, btn_config, btn_quit]

    # ÍCONE DO JOGO — descomente quando tiver assets/icone.png:
    # icon_img = try_load("icone.png", (110, 110))
    icon_img = None  # ← substitua pela linha acima quando tiver o ícone

    while True:
        mp = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
            if btn_start.is_clicked(mp, event):
                r = song_select_menu()
                if r == "quit": pygame.quit(); sys.exit()
            if btn_config.is_clicked(mp, event):
                settings_menu()
            if btn_quit.is_clicked(mp, event):
                pygame.quit(); sys.exit()

        for btn in buttons:
            btn.check_hover(mp)
            btn.update()

        draw_bg(screen)

        # Espaço do ícone (110x110 acima do título)
        icon_cx, icon_cy = cx, 130
        if icon_img:
            screen.blit(icon_img, icon_img.get_rect(center=(icon_cx, icon_cy)))
        else:
            ph = pygame.Rect(0, 0, 100, 100)
            ph.center = (icon_cx, icon_cy)
            pygame.draw.rect(screen, MID_GRAY, ph, border_radius=14, width=2)
            pt = font_hud.render("ÍCONE", True, MID_GRAY)
            screen.blit(pt, pt.get_rect(center=ph.center))

        draw_title(screen, cx, 240)
        pygame.draw.line(screen, LANE_COLORS[0], (cx-220, 320), (cx+220, 320), 2)

        for btn in buttons:
            btn.draw(screen)

        ft = font_hud.render("F11 = Tela cheia  |  ESC = Sair", True, MID_GRAY)
        screen.blit(ft, ft.get_rect(center=(cx, SCREEN_HEIGHT - 20)))

        pygame.display.flip()
        clock.tick(FPS)

# ==============================================================================
# ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    main_menu()
=======
import pygame
import os
import json
import sys
import math
import random

# ==============================================================================
# CONFIGURAÇÕES BÁSICAS
# ==============================================================================
SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720
FPS           = 60

# 4 lanes de 55px com gap de 15px entre elas = bloco de 275px, centralizado em 1280
_LANE_START = (1280 - 275) // 2   # 502
LANE_X     = [_LANE_START + i * 70 + 27 for i in range(4)]  # [529, 599, 669, 739]
HIT_ZONE_Y = 620
NOTE_SPEED = 0.4

WHITE     = (255, 255, 255)
BLACK     = (0,   0,   0)
DARK_GRAY = (45,  45,  45)
MID_GRAY  = (70,  70,  70)
GRAY      = (140, 140, 140)
TITLE_CLR = (20,  20,  20)

LANE_COLORS = [
    (150, 50,  250),
    (50,  200, 50),
    (220, 50,  50),
    (250, 200, 50),
]

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Sabor - Videogame")
clock = pygame.time.Clock()

# ==============================================================================
# FONTES PIXELADAS
# ==============================================================================
def load_pixel_font(size, italic=False):
    for name in ["Courier New", "Lucida Console", "Consolas", "monospace"]:
        try:
            return pygame.font.SysFont(name, size, bold=True, italic=italic)
        except:
            pass
    return pygame.font.Font(None, size)

font_title = load_pixel_font(72, italic=True)
font_sub   = load_pixel_font(22, italic=False)
font_btn   = load_pixel_font(36, italic=False)
font_hud   = load_pixel_font(24, italic=False)
font_med   = load_pixel_font(30, italic=False)
font_big   = load_pixel_font(52, italic=False)

# ==============================================================================
# VOLUME
# ==============================================================================
volume = 0.7
pygame.mixer.music.set_volume(volume)

# ==============================================================================
# CARREGAMENTO DE IMAGENS
# Estrutura esperada em assets/:
#   icone.png              ← ícone do jogo (reservado)
#   PlayerParado.png
#   PlayerCima.png
#   PlayerBaixo.png
#   PlayerEsquerda.png
#   PlayerDireita.png
#   RoboParado.png
#   RoboCima.png
#   RoboBaixo.png
#   RoboEsquerda.png
#   RoboDireita.png
#   vida_icone.png         ← ícone deslizante da barra de vida
# ==============================================================================
ASSETS = "assets"

def try_load(filename, size=None):
    path = os.path.join(ASSETS, filename)
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, size) if size else img
    return None

CHAR_SIZE = (160, 220)

player_sprites = {
    "parado":   try_load("PlayerParado.png",   CHAR_SIZE),
    "cima":     try_load("PlayerCima.png",     CHAR_SIZE),
    "baixo":    try_load("PlayerBaixo.png",    CHAR_SIZE),
    "esquerda": try_load("PlayerEsquerda.png", CHAR_SIZE),
    "direita":  try_load("PlayerDireita.png",  CHAR_SIZE),
}

robo_sprites = {
    "parado":   try_load("RoboParado.png",   CHAR_SIZE),
    "cima":     try_load("RoboCima.png",     CHAR_SIZE),
    "baixo":    try_load("RoboBaixo.png",    CHAR_SIZE),
    "esquerda": try_load("RoboEsquerda.png", CHAR_SIZE),
    "direita":  try_load("RoboDireita.png",  CHAR_SIZE),
}

vida_icon = try_load("vida_icone.png", (32, 32))

# ÍCONE DO JOGO (reservado) — descomente quando tiver o arquivo:
# game_icon = try_load("icone.png", (64, 64))
# if game_icon: pygame.display.set_icon(game_icon)

# ==============================================================================
# PERSONAGEM ANIMADO
# ==============================================================================
LANE_POSE = {0: "esquerda", 1: "baixo", 2: "cima", 3: "direita"}

class Character:
    POSE_FRAMES = 20

    def __init__(self, sprites, x, y, flip=False):
        self.sprites    = sprites
        self.x          = x
        self.y          = y
        self.flip       = flip
        self.pose       = "parado"
        self.pose_timer = 0
        self.idle_timer = 0

    def set_pose(self, pose):
        self.pose       = pose
        self.pose_timer = self.POSE_FRAMES

    def update(self):
        if self.pose_timer > 0:
            self.pose_timer -= 1
            if self.pose_timer == 0:
                self.pose = "parado"
        self.idle_timer += 1

    def draw(self, surface):
        bob = int(4 * abs(math.sin(self.idle_timer * 0.05))) if self.pose == "parado" else 0
        sprite = self.sprites.get(self.pose) or self.sprites.get("parado")

        if sprite:
            img  = pygame.transform.flip(sprite, self.flip, False) if self.flip else sprite
            rect = img.get_rect(midbottom=(self.x, self.y + bob))
            surface.blit(img, rect)
        else:
            color = (80, 180, 255) if not self.flip else (255, 100, 80)
            label = "PLAYER" if not self.flip else "ROBO"
            ph = pygame.Rect(0, 0, 120, 180)
            ph.midbottom = (self.x, self.y + bob)
            pygame.draw.rect(surface, color, ph, border_radius=14)
            pygame.draw.rect(surface, WHITE, ph, border_radius=14, width=2)
            t = font_hud.render(label, True, WHITE)
            surface.blit(t, t.get_rect(center=ph.center))

# ==============================================================================
# BOTÃO ANIMADO
# ==============================================================================
class Button:
    def __init__(self, text, x, y, base_size=36, hover_size=46, color=WHITE, hover_color=None):
        self.text        = text
        self.x           = x
        self.y           = y
        self.base_size   = base_size
        self.hover_size  = hover_size
        self.color       = color
        self.hover_color = hover_color or LANE_COLORS[0]
        self.cur_size    = float(base_size)
        self.hovered     = False

    def _font(self):
        return load_pixel_font(int(self.cur_size))

    def _rect(self):
        txt = self._font().render(self.text, True, self.color)
        return txt.get_rect(center=(self.x, self.y))

    def update(self):
        target = self.hover_size if self.hovered else self.base_size
        self.cur_size += (target - self.cur_size) * 0.18

    def check_hover(self, mp):
        self.hovered = self._rect().collidepoint(mp)

    def is_clicked(self, mp, event):
        return (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self._rect().collidepoint(mp))

    def draw(self, surface):
        f     = self._font()
        color = self.hover_color if self.hovered else self.color
        if self.hovered:
            sh = f.render(self.text, True, BLACK)
            surface.blit(sh, sh.get_rect(center=(self.x+2, self.y+2)))
        txt = f.render(self.text, True, color)
        surface.blit(txt, txt.get_rect(center=(self.x, self.y)))

# ==============================================================================
# UTILITÁRIOS
# ==============================================================================
def draw_bg(surface):
    surface.fill(DARK_GRAY)

def draw_title(surface, cx, y):
    title_str = "Sabor - Videogame"
    for dx, dy in [(-3,0),(3,0),(0,-3),(0,3),(-3,-3),(3,-3),(-3,3),(3,3)]:
        sh = font_title.render(title_str, True, LANE_COLORS[0])
        surface.blit(sh, sh.get_rect(center=(cx+dx, y+dy)))
    txt = font_title.render(title_str, True, TITLE_CLR)
    surface.blit(txt, txt.get_rect(center=(cx, y)))
    sub = font_sub.render("Feito pela equipe Sabor T.I", True, GRAY)
    surface.blit(sub, sub.get_rect(center=(cx, y + 60)))

def load_songs():
    if not os.path.exists("songs"):
        os.makedirs("songs")
        return []
    return [f for f in os.listdir("songs") if os.path.isdir(os.path.join("songs", f))]

# ==============================================================================
# BARRA DE VIDA
# pos=0.0 → robô vencendo | pos=1.0 → player perdeu (game over)
# ==============================================================================
class HealthBar:
    BAR_W = 500
    BAR_H = 16

    def __init__(self, cx, y):
        self.cx  = cx
        self.y   = y
        self.pos = 0.5
        self.x0  = cx - self.BAR_W // 2
        self.x1  = cx + self.BAR_W // 2

    def hit(self):
        self.pos = max(0.0, self.pos - 0.04)

    def miss(self):
        self.pos = min(1.0, self.pos + 0.06)

    @property
    def dead(self):
        return self.pos >= 1.0

    def draw(self, surface):
        # Trilha da barra — branca com baixa opacidade simulada via cinza claro
        bar = pygame.Rect(self.x0, self.y - self.BAR_H//2, self.BAR_W, self.BAR_H)
        pygame.draw.rect(surface, (90, 90, 90), bar, border_radius=8)
        # Borda branca na trilha
        pygame.draw.rect(surface, WHITE, bar, border_radius=8, width=2)

        r_lbl = font_hud.render("ROBÔ", True, GRAY)
        p_lbl = font_hud.render("PLAYER", True, GRAY)
        surface.blit(r_lbl, r_lbl.get_rect(midright=(self.x0 - 8, self.y)))
        surface.blit(p_lbl, p_lbl.get_rect(midleft=(self.x1 + 8, self.y)))

        # Ponto deslizante branco
        icon_x = int(self.x0 + self.BAR_W * self.pos)
        if vida_icon:
            surface.blit(vida_icon, vida_icon.get_rect(center=(icon_x, self.y)))
        else:
            pygame.draw.circle(surface, WHITE, (icon_x, self.y), 13)
            pygame.draw.circle(surface, DARK_GRAY, (icon_x, self.y), 7)

# ==============================================================================
# ROBÔ IA
# ==============================================================================
class RoboAI:
    def __init__(self):
        self.pending = []

    def schedule(self, note, current_time):
        self.pending.append((note, current_time + random.randint(0, 80)))

    def update(self, notes, current_time, robo_char):
        done = []
        for item in self.pending:
            n, t = item
            if current_time >= t:
                if n in notes:
                    notes.remove(n)
                    robo_char.set_pose(LANE_POSE.get(n["lane"], "parado"))
                done.append(item)
        for item in done:
            self.pending.remove(item)

# ==============================================================================
# GAME OVER
# ==============================================================================
def game_over_screen(song_name):
    cx        = SCREEN_WIDTH // 2
    btn_retry = Button("Tentar Novamente", cx, 450, hover_color=LANE_COLORS[1])
    btn_menu  = Button("Menu Principal",  cx, 530, hover_color=LANE_COLORS[3])

    while True:
        mp = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "menu"
            if btn_retry.is_clicked(mp, event): return "retry"
            if btn_menu.is_clicked(mp, event):  return "menu"

        for btn in [btn_retry, btn_menu]:
            btn.check_hover(mp)
            btn.update()

        draw_bg(screen)

        l1 = font_big.render("Xii... Paizão,", True, LANE_COLORS[2])
        l2 = font_big.render("Sem sabor esse player Ai!!", True, LANE_COLORS[2])
        screen.blit(l1, l1.get_rect(center=(cx, 300)))
        screen.blit(l2, l2.get_rect(center=(cx, 370)))

        for btn in [btn_retry, btn_menu]:
            btn.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

# ==============================================================================
# JOGO
# ==============================================================================
def play_game(song_name):
    song_path = os.path.join("songs", song_name)
    json_path = os.path.join(song_path, "data.json")

    if not os.path.exists(json_path):
        print(f"data.json não encontrado em {song_path}")
        return "back"

    pygame.mixer.music.load(os.path.join(song_path, "som.mp3"))
    pygame.mixer.music.set_volume(volume)

    with open(json_path, "r") as f:
        chart = json.load(f)

    # Player e robô têm listas COMPLETAMENTE separadas
    player_notes = [dict(n) for n in chart["notes"]]
    robo_notes   = [dict(n) for n in chart["notes"]]
    robo_pending = list(robo_notes)

    cx = SCREEN_WIDTH // 2
    player_char = Character(player_sprites, x=SCREEN_WIDTH - 200, y=HIT_ZONE_Y - 10)
    robo_char   = Character(robo_sprites,   x=200,                y=HIT_ZONE_Y - 10, flip=True)

    health   = HealthBar(cx, 45)
    robo_ai  = RoboAI()
    score    = 0
    misses   = 0
    feedback = []

    pygame.mixer.music.play()
    start_time = pygame.time.get_ticks() + 1000

    running = True
    while running:
        draw_bg(screen)
        current_time = pygame.time.get_ticks() - start_time

        # Agenda notas pro robô (lista própria, não interfere no player)
        for n in robo_pending[:]:
            if HIT_ZONE_Y - (n["time"] - current_time) * NOTE_SPEED >= HIT_ZONE_Y - 80:
                robo_ai.schedule(n, current_time)
                robo_pending.remove(n)

        robo_ai.update(robo_notes, current_time, robo_char)
        player_char.update()
        robo_char.update()

        # Zonas de acerto
        for i, x in enumerate(LANE_X):
            rect = pygame.Rect(0, 0, 55, 55)
            rect.center = (x, HIT_ZONE_Y)
            pygame.draw.rect(screen, MID_GRAY, rect, border_radius=10)
            pygame.draw.rect(screen, LANE_COLORS[i], rect, border_radius=10, width=3)

        # Setas abaixo das zonas de acerto
        # Imagens: SetaEsquerda.png, SetaBaixo.png, SetaCima.png, SetaDireita.png
        # Coloque os arquivos em assets/ e descomente as linhas abaixo:
        # seta_imgs = [
        #     try_load("SetaEsquerda.png", (45, 45)),
        #     try_load("SetaBaixo.png",    (45, 45)),
        #     try_load("SetaCima.png",     (45, 45)),
        #     try_load("SetaDireita.png",  (45, 45)),
        # ]
        # for i, x in enumerate(LANE_X):
        #     if seta_imgs[i]:
        #         r = seta_imgs[i].get_rect(midtop=(x, HIT_ZONE_Y + 35))
        #         screen.blit(seta_imgs[i], r)
        # Placeholder visual enquanto as imagens não estiverem prontas:
        seta_chars = ["←", "↓", "↑", "→"]
        for i, x in enumerate(LANE_X):
            st = font_hud.render(seta_chars[i], True, LANE_COLORS[i])
            screen.blit(st, st.get_rect(midtop=(x, HIT_ZONE_Y + 35)))

        # Eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.mixer.music.stop()
                    return "back"
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()

                key_map = {
                    pygame.K_a: 0, pygame.K_LEFT:  0,
                    pygame.K_s: 1, pygame.K_DOWN:  1,
                    pygame.K_w: 2, pygame.K_UP:    2,
                    pygame.K_d: 3, pygame.K_RIGHT: 3,
                }
                if event.key in key_map:
                    lane = key_map[event.key]
                    player_char.set_pose(LANE_POSE[lane])
                    hit = False
                    for n in player_notes[:]:
                        if n["lane"] == lane:
                            note_y = HIT_ZONE_Y - (n["time"] - current_time) * NOTE_SPEED
                            if abs(note_y - HIT_ZONE_Y) < 55:
                                player_notes.remove(n)
                                score += 100
                                health.hit()
                                hit = True
                                feedback.append(["ÓTIMO!", LANE_X[lane], HIT_ZONE_Y-55, 45, LANE_COLORS[1]])
                                break
                    if not hit:
                        misses += 1
                        health.miss()
                        feedback.append(["MISS!", LANE_X[lane], HIT_ZONE_Y-55, 45, LANE_COLORS[2]])

        # Notas caindo (apenas as do player)
        for n in player_notes[:]:
            note_y = HIT_ZONE_Y - (n["time"] - current_time) * NOTE_SPEED
            if -28 < note_y < SCREEN_HEIGHT:
                nr = pygame.Rect(0, 0, 55, 28)
                nr.center = (LANE_X[n["lane"]], int(note_y))
                pygame.draw.rect(screen, LANE_COLORS[n["lane"]], nr, border_radius=7)
                pygame.draw.rect(screen, BLACK, nr, border_radius=7, width=2)
            if note_y > SCREEN_HEIGHT + 50:
                player_notes.remove(n)
                misses += 1
                health.miss()

        # Personagens
        robo_char.draw(screen)
        player_char.draw(screen)

        # Barra de vida
        health.draw(screen)

        # HUD
        screen.blit(font_hud.render(f"Score: {score}",   True, WHITE),           (20, SCREEN_HEIGHT-55))
        screen.blit(font_hud.render(f"Misses: {misses}", True, LANE_COLORS[2]),   (20, SCREEN_HEIGHT-30))
        esc = font_hud.render("ESC=Menu  F11=Fullscreen", True, MID_GRAY)
        screen.blit(esc, esc.get_rect(bottomright=(SCREEN_WIDTH-10, SCREEN_HEIGHT-10)))

        # Feedback
        for fb in feedback[:]:
            fb[3] -= 1
            fly = fb[2] - (45 - fb[3])
            t   = font_hud.render(fb[0], True, fb[4])
            screen.blit(t, t.get_rect(center=(fb[1], fly)))
            if fb[3] <= 0:
                feedback.remove(fb)

        # Game over
        if health.dead:
            pygame.mixer.music.stop()
            r = game_over_screen(song_name)
            return play_game(song_name) if r == "retry" else "back"

        if not pygame.mixer.music.get_busy() and not player_notes:
            running = False

        pygame.display.flip()
        clock.tick(FPS)

    return result_screen(score, misses)

# ==============================================================================
# RESULTADO
# ==============================================================================
def result_screen(score, misses):
    cx       = SCREEN_WIDTH // 2
    btn_back = Button("← Menu Principal", cx, 470, hover_color=LANE_COLORS[1])

    while True:
        mp = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "quit"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return "back"
            if btn_back.is_clicked(mp, event): return "back"

        btn_back.check_hover(mp)
        btn_back.update()
        draw_bg(screen)
        draw_title(screen, cx, 130)

        screen.blit(font_big.render("RESULTADO", True, WHITE),                   font_big.render("RESULTADO", True, WHITE).get_rect(center=(cx, 250)))
        screen.blit(font_btn.render(f"Score:  {score}",   True, WHITE),          font_btn.render(f"Score:  {score}",   True, WHITE).get_rect(center=(cx, 330)))
        screen.blit(font_btn.render(f"Misses: {misses}",  True, LANE_COLORS[2]), font_btn.render(f"Misses: {misses}",  True, LANE_COLORS[2]).get_rect(center=(cx, 390)))
        btn_back.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

# ==============================================================================
# CONFIGURAÇÕES
# ==============================================================================
def settings_menu():
    global volume
    cx       = SCREEN_WIDTH // 2
    btn_back = Button("← Voltar", cx, 560, base_size=28, hover_size=36, hover_color=GRAY)
    sx, sw, sy = cx - 200, 400, 350
    dragging = False

    while True:
        mp = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return
            if btn_back.is_clicked(mp, event): return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if sx <= mp[0] <= sx+sw and sy-15 <= mp[1] <= sy+15:
                    dragging = True
            if event.type == pygame.MOUSEBUTTONUP:
                dragging = False

        if dragging:
            volume = max(0.0, min(1.0, (mp[0]-sx)/sw))
            pygame.mixer.music.set_volume(volume)

        btn_back.check_hover(mp)
        btn_back.update()
        draw_bg(screen)
        draw_title(screen, cx, 130)

        lbl = font_btn.render("Volume da Música", True, WHITE)
        screen.blit(lbl, lbl.get_rect(center=(cx, 280)))

        pygame.draw.rect(screen, MID_GRAY,       (sx, sy-6, sw, 12), border_radius=6)
        pygame.draw.rect(screen, LANE_COLORS[3], (sx, sy-6, int(sw*volume), 12), border_radius=6)
        pygame.draw.circle(screen, WHITE, (sx+int(sw*volume), sy), 14)

        pct = font_hud.render(f"{int(volume*100)}%", True, GRAY)
        screen.blit(pct, pct.get_rect(center=(cx, sy+40)))
        btn_back.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

# ==============================================================================
# SELEÇÃO DE MÚSICAS
# ==============================================================================
def song_select_menu():
    songs    = load_songs()
    cx       = SCREEN_WIDTH // 2
    btn_back = Button("← Voltar", cx, 640, base_size=28, hover_size=36, hover_color=GRAY)

    if not songs:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: return "quit"
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return "back"
            draw_bg(screen)
            draw_title(screen, cx, 120)
            m = font_med.render("Nenhuma música encontrada!", True, LANE_COLORS[2])
            h = font_hud.render("Crie songs/<nome>/som.mp3 e data.json", True, GRAY)
            screen.blit(m, m.get_rect(center=(cx, 340)))
            screen.blit(h, h.get_rect(center=(cx, 390)))
            pygame.display.flip()
            clock.tick(FPS)

    buttons = [Button(f"Fase {i+1}", cx, 240 + i*70, hover_color=LANE_COLORS[i%4]) for i, s in enumerate(songs)]

    while True:
        mp = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "quit"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return "back"
            if btn_back.is_clicked(mp, event): return "back"
            for i, btn in enumerate(buttons):
                if btn.is_clicked(mp, event):
                    r = play_game(songs[i])
                    if r == "quit": return "quit"

        for btn in buttons + [btn_back]:
            btn.check_hover(mp)
            btn.update()

        draw_bg(screen)
        draw_title(screen, cx, 110)
        sep = font_med.render("── Selecione a Fase ──", True, GRAY)
        screen.blit(sep, sep.get_rect(center=(cx, 190)))
        for btn in buttons + [btn_back]:
            btn.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

# ==============================================================================
# MENU PRINCIPAL
# ==============================================================================
def main_menu():
    cx = SCREEN_WIDTH // 2
    btn_start  = Button("Começar",       cx, 380, hover_color=LANE_COLORS[1])
    btn_config = Button("Configurações", cx, 460, hover_color=LANE_COLORS[3])
    btn_quit   = Button("Sair",          cx, 540, hover_color=LANE_COLORS[2])
    buttons    = [btn_start, btn_config, btn_quit]

    # ÍCONE DO JOGO — descomente quando tiver assets/icone.png:
    # icon_img = try_load("icone.png", (110, 110))
    icon_img = None  # ← substitua pela linha acima quando tiver o ícone

    while True:
        mp = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
            if btn_start.is_clicked(mp, event):
                r = song_select_menu()
                if r == "quit": pygame.quit(); sys.exit()
            if btn_config.is_clicked(mp, event):
                settings_menu()
            if btn_quit.is_clicked(mp, event):
                pygame.quit(); sys.exit()

        for btn in buttons:
            btn.check_hover(mp)
            btn.update()

        draw_bg(screen)

        # Espaço do ícone (110x110 acima do título)
        icon_cx, icon_cy = cx, 130
        if icon_img:
            screen.blit(icon_img, icon_img.get_rect(center=(icon_cx, icon_cy)))
        else:
            ph = pygame.Rect(0, 0, 100, 100)
            ph.center = (icon_cx, icon_cy)
            pygame.draw.rect(screen, MID_GRAY, ph, border_radius=14, width=2)
            pt = font_hud.render("ÍCONE", True, MID_GRAY)
            screen.blit(pt, pt.get_rect(center=ph.center))

        draw_title(screen, cx, 240)
        pygame.draw.line(screen, LANE_COLORS[0], (cx-220, 320), (cx+220, 320), 2)

        for btn in buttons:
            btn.draw(screen)

        ft = font_hud.render("F11 = Tela cheia  |  ESC = Sair", True, MID_GRAY)
        screen.blit(ft, ft.get_rect(center=(cx, SCREEN_HEIGHT - 20)))

        pygame.display.flip()
        clock.tick(FPS)

# ==============================================================================
# ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    main_menu()
>>>>>>> 8aa4804283862fd36dca8f5da8b60ba8281c7c83
    pygame.quit()