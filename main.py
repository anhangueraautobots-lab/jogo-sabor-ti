import pygame
import os
import json
import sys
import math
import random

# ==============================================================================
# CONFIGURAÇÕES
# ==============================================================================
SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720
FPS           = 60

_CX    = SCREEN_WIDTH // 2
LANE_X = [_CX - 90, _CX - 30, _CX + 30, _CX + 90]

HIT_ZONE_Y = 600
NOTE_SPEED  = 0.4
NOTE_SIZE   = 300        

NOTE_WIDTH  = NOTE_SIZE
NOTE_HEIGHT = NOTE_SIZE

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
LANE_ARROWS = ["←", "↓", "↑", "→"]
LANE_POSE   = {0: "esquerda", 1: "baixo", 2: "cima", 3: "direita"}

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Sabor - Videogame")
clock = pygame.time.Clock()

# ==============================================================================
# FONTES
# ==============================================================================
FONT_PATH = os.path.join("src", "fonts", "upheavtt.ttf")
if not os.path.exists(FONT_PATH):
    FONT_PATH = os.path.join("fonts", "upheavtt.ttf")

def load_font(size, italic=False):
    if os.path.exists(FONT_PATH):
        f = pygame.font.Font(FONT_PATH, size)
        if italic: f.italic = True
        return f
    for name in ["Courier New", "Lucida Console", "Consolas"]:
        try: return pygame.font.SysFont(name, size, bold=True, italic=italic)
        except: pass
    return pygame.font.Font(None, size)

font_title = load_font(72, italic=True)
font_sub   = load_font(22)
font_btn   = load_font(36)
font_hud   = load_font(24)
font_med   = load_font(30)
font_big   = load_font(52)
font_arrow = load_font(38)   # ← fonte maior para setas fallback

# ==============================================================================
# VOLUME / LEADERBOARD
# ==============================================================================
volume = 0.3

LEADERBOARD_FILE = "leaderboard.json"

def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, "r") as f:
                return json.load(f)
        except: pass
    return []

def save_leaderboard(entries):
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(entries, f, indent=2)

def add_to_leaderboard(name, score, fase):
    entries = load_leaderboard()
    entries.append({"name": name, "score": score, "fase": fase})
    entries.sort(key=lambda x: x["score"], reverse=True)
    entries = entries[:10]
    save_leaderboard(entries)

# ==============================================================================
# IMAGENS
# ==============================================================================
ASSETS = os.path.join("src", "assets")
if not os.path.exists(ASSETS):
    ASSETS = "assets"

def try_load(filename, size=None):
    path = os.path.join(ASSETS, filename)
    if os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.scale(img, size) if size else img
        except: pass
    return None

def scale_fill(img, w, h):
    if img is None: return None
    iw, ih = img.get_size()
    scale = max(w/iw, h/ih)
    nw, nh = int(iw*scale), int(ih*scale)
    scaled = pygame.transform.scale(img, (nw, nh))
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.blit(scaled, ((w-nw)//2, (h-nh)//2))
    return surf

# --- CARREGAMENTO DOS CENÁRIOS E LOGO ---
raw_cenario_sabor = try_load("CenarioSabor.png")
raw_cenario_prob  = try_load("CenarioProb.png")
raw_cenario_menu  = try_load("CenarioMenu.png") # Adicionado

BG_MENU  = scale_fill(raw_cenario_menu,  SCREEN_WIDTH, SCREEN_HEIGHT) if raw_cenario_menu  else scale_fill(raw_cenario_sabor, SCREEN_WIDTH, SCREEN_HEIGHT)
BG_SABOR = scale_fill(raw_cenario_sabor, SCREEN_WIDTH, SCREEN_HEIGHT) if raw_cenario_sabor else None
BG_PROB  = scale_fill(raw_cenario_prob,  SCREEN_WIDTH, SCREEN_HEIGHT) if raw_cenario_prob  else None

LOGO = try_load("Logo.png")
if LOGO:
    lw, lh = LOGO.get_size()
    scale = min(500/lw, 180/lh)
    LOGO = pygame.transform.scale(LOGO, (int(lw*scale), int(lh*scale)))


# ==============================================================================
# PERSONAGENS — tamanho aumentado, proporcional ao cenário
# ==============================================================================
TOGURO_SIZE = (550, 430) # ← Esticado para os lados e maior
BITELO_SIZE = (380, 480) # ← Tamanho original/normal

toguro_sprites = {
    "parado":   try_load("ToguroParado.png",   TOGURO_SIZE),
    "cima":     try_load("ToguroCima.png",     TOGURO_SIZE),
    "baixo":    try_load("ToguroParado.png",   TOGURO_SIZE),
    "esquerda": try_load("ToguroEsquerda.png", TOGURO_SIZE),
    "direita":  try_load("ToguroDireita.png",  TOGURO_SIZE),
}
bitelo_sprites = {
    "parado":   try_load("BiteloParado.png",   BITELO_SIZE),
    "cima":     try_load("BiteloCima.png",     BITELO_SIZE),
    "baixo":    try_load("BiteloParado.png",   BITELO_SIZE),
    "esquerda": try_load("BiteloEsquerda.png", BITELO_SIZE),
    "direita":  try_load("BiteloDireita.png",  BITELO_SIZE),
}

# ==============================================================================
# TAMANHO PROPORCIONAL DAS SETAS (Largas e Achatadas)
# ==============================================================================
NOTE_WIDTH  = NOTE_SIZE       # Mantém a largura base (220)
NOTE_HEIGHT = int(NOTE_SIZE * 0.6) # Altura achatada para 60% da largura

# Subtraímos 4 apenas para dar aquela margenzinha que você já tinha colocado
SETA_FINAL_SIZE = (NOTE_WIDTH - 4, NOTE_HEIGHT - 4)

# Setas nas notas — sem fundo, só a imagem da seta
seta_notas = [
    try_load("SetaEsquerda.png",  SETA_FINAL_SIZE),
    try_load("SetaBaixo.png",     SETA_FINAL_SIZE),
    try_load("SetaCima.png",      SETA_FINAL_SIZE),
    try_load("SetaDireita.png",   SETA_FINAL_SIZE),
]

# Setas esqueleto (alvos fixos) — sem fundo
seta_alvos = [
    try_load("SetaEsquerdaEsqueleto.png", SETA_FINAL_SIZE),
    try_load("SetaBaixoEsqueleto.png",    SETA_FINAL_SIZE),
    try_load("SetaCimaEsqueleto.png",     SETA_FINAL_SIZE),
    try_load("SetaDireitaEsqueleto.png",  SETA_FINAL_SIZE),
]

# ==============================================================================
# MÚSICA DO MENU
# ==============================================================================
_menu_music_loaded = False
_menu_music_path   = None
_is_primeiro_menu  = True
_menu_music_playing = False

def _find_menu_music():
    """Procura a 4ª música na pasta songs/ (índice 3)."""
    if not os.path.exists("songs"):
        return None
    songs = sorted([f for f in os.listdir("songs") if os.path.isdir(os.path.join("songs", f))])
    if len(songs) >= 4:
        path = os.path.join("songs", songs[3], "som.mp3")
        return path if os.path.exists(path) else None
    # Se não tiver 4, pega a última disponível
    for s in reversed(songs):
        path = os.path.join("songs", s, "som.mp3")
        if os.path.exists(path):
            return path
    return None

def primeiro_menu():
    """Tela inicial que espera o clique do jogador."""
    cx = SCREEN_WIDTH // 2
    start_menu_music() # Toca a música baixa
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN or (event.type == pygame.KEYDOWN and event.key in [pygame.K_RETURN, pygame.K_SPACE]):
                transition_to_game_music()
                return 
        
        # LINHA CORRIGIDA AQUI: Sem nada dentro dos parênteses
        update_menu_music()
        
        draw_bg(screen, BG_MENU)
        draw_overlay(screen, 150)
        draw_title(screen, cx, 200)
        
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            hint = font_btn.render("CLIQUE PARA COMEÇAR", True, WHITE)
            screen.blit(hint, hint.get_rect(center=(cx, SCREEN_HEIGHT - 150)))

        pygame.display.flip()
        clock.tick(FPS)

def start_menu_music():
    global _menu_music_loaded, _menu_music_path, _is_primeiro_menu, _menu_music_playing
    
    # Se a música do menu já está tocando (saindo da intro), deixa ela rolar!
    if _menu_music_playing:
        return 
        
    path = _find_menu_music()
    if path is None:
        return
        
    try:
        pygame.mixer.music.load(path)
        
        if _is_primeiro_menu:
            # Primeiro menu: Toca baixo e desde o início
            pygame.mixer.music.set_volume(0.05)
            pygame.mixer.music.play(loops=-1, start=0.0)
        else:
            # Voltando de uma fase para o Menu: Toca alto e já começa do refrão
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(loops=-1, start=26.0)
            
        _menu_music_loaded  = True
        _menu_music_path    = path
        _menu_music_playing = True
    except Exception as e:
        print(f"Erro ao carregar música do menu: {e}")

def update_menu_music():
    global _is_primeiro_menu
    if not _menu_music_loaded:
        return
    pos = pygame.mixer.music.get_pos()
    
    # Loop de 25s APENAS na tela do primeiro menu (CLIQUE PARA COMEÇAR)
    if _is_primeiro_menu and pos >= 25_000:
        pygame.mixer.music.rewind()
        pygame.mixer.music.set_pos(0.0)

def transition_to_game_music():
    global _is_primeiro_menu
    if not _menu_music_loaded:
        return
    try:
        _is_primeiro_menu = False 
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.set_pos(26.0) # Pula para o refrão na intro
    except Exception as e:
        print(f"Erro na transição de música: {e}")

def stop_menu_music():
    global _menu_music_playing
    _menu_music_playing = False
    pygame.mixer.music.stop()

# ==============================================================================
# CLASSE PERSONAGEM — animação suave estilo FNF
# ==============================================================================
class Character:
    POSE_FRAMES = 15        # frames que a pose de hit fica ativa

    # Idle: usamos seno contínuo para bounce suave (sem salto brusco)
    IDLE_BOB_AMP   = 14.0    # amplitude em pixels
    IDLE_BOB_SPEED = 0.12   # velocidade angular (radianos/frame)

    def __init__(self, sprites, x, y, flip=False):
        self.sprites    = sprites
        self.x          = x
        self.y          = y
        self.flip       = flip
        self.pose       = "parado"
        self.pose_timer = 0
        self.idle_angle = 0.0   # ângulo contínuo para seno

    def set_pose(self, pose):
        self.pose       = pose
        self.pose_timer = self.POSE_FRAMES

    def update(self):
        if self.pose_timer > 0:
            self.pose_timer -= 1
            if self.pose_timer == 0:
                self.pose = "parado"
        # Avança o ângulo sempre, independente da pose
        self.idle_angle += self.IDLE_BOB_SPEED

    def _bob_y(self):
        """Retorna deslocamento vertical suave baseado em seno."""
        return int(math.sin(self.idle_angle) * self.IDLE_BOB_AMP)

    def draw(self, surface):
        sprite = self.sprites.get(self.pose) or self.sprites.get("parado")
        bob    = self._bob_y()

        if sprite:
            img  = pygame.transform.flip(sprite, self.flip, False) if self.flip else sprite
            rect = img.get_rect(midbottom=(self.x, self.y + bob))
            surface.blit(img, rect)
        else:
            color = (80, 180, 255) if not self.flip else (255, 100, 80)
            label = "TOGURO" if not self.flip else "BITELO"
            ph = pygame.Rect(0, 0, 180, 280)
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

    def _font(self): return load_font(int(self.cur_size))
    def _rect(self):
        return self._font().render(self.text, True, self.color).get_rect(center=(self.x, self.y))
    def update(self):
        t = self.hover_size if self.hovered else self.base_size
        self.cur_size += (t - self.cur_size) * 0.18
    def check_hover(self, mp): self.hovered = self._rect().collidepoint(mp)
    def is_clicked(self, mp, event):
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self._rect().collidepoint(mp)
    def draw(self, surface):
        f = self._font()
        c = self.hover_color if self.hovered else self.color
        if self.hovered:
            sh = f.render(self.text, True, BLACK)
            surface.blit(sh, sh.get_rect(center=(self.x+2, self.y+2)))
        txt = f.render(self.text, True, c)
        surface.blit(txt, txt.get_rect(center=(self.x, self.y)))

# ==============================================================================
# UTILITÁRIOS
# ==============================================================================
def draw_bg(surface, bg=None):
    if bg:
        surface.blit(bg, (0, 0))
    else:
        surface.fill(DARK_GRAY)

def draw_overlay(surface, alpha=140):
    ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    ov.set_alpha(alpha)
    ov.fill(BLACK)
    surface.blit(ov, (0, 0))

def draw_title(surface, cx, y):
    if LOGO:
        surface.blit(LOGO, LOGO.get_rect(center=(cx, y)))
    else:
        s = "Sabor - Videogame"
        for dx, dy in [(-3,0),(3,0),(0,-3),(0,3),(-3,-3),(3,-3),(-3,3),(3,3)]:
            sh = font_title.render(s, True, LANE_COLORS[0])
            surface.blit(sh, sh.get_rect(center=(cx+dx, y+dy)))
        txt = font_title.render(s, True, TITLE_CLR)
        surface.blit(txt, txt.get_rect(center=(cx, y)))
    sub = font_sub.render("Feito pela equipe Sabor T.I", True, GRAY)
    surface.blit(sub, sub.get_rect(center=(cx, y + (LOGO.get_height()//2 + 20 if LOGO else 60))))

def draw_note(surface, lane, cx, cy, size):
    """
    Desenha apenas a seta, SEM fundo colorido.
    Se a imagem existe usa ela; caso contrário desenha o símbolo da seta
    com cor da lane, sem retângulo de fundo.
    """
    if seta_notas[lane]:
        surface.blit(seta_notas[lane], seta_notas[lane].get_rect(center=(cx, cy)))
    else:
        # Fallback: apenas texto da seta, colorido, sem caixa
        t = font_arrow.render(LANE_ARROWS[lane], True, LANE_COLORS[lane])
        # Sombra sutil para legibilidade
        sh = font_arrow.render(LANE_ARROWS[lane], True, BLACK)
        surface.blit(sh, sh.get_rect(center=(cx+2, cy+2)))
        surface.blit(t,  t.get_rect(center=(cx, cy)))

def load_songs():
    if not os.path.exists("songs"):
        os.makedirs("songs")
        return []
    return sorted([f for f in os.listdir("songs") if os.path.isdir(os.path.join("songs", f))])

def get_bg_for_fase(index):
    if index < 2:
        return BG_PROB if BG_PROB else BG_SABOR
    return BG_SABOR

# ==============================================================================
# INTRO ESTILO SONIC
# ==============================================================================
def play_intro():
    if not LOGO and not BG_MENU:
        return

    phases = [
        {"dur": 30,  "type": "black"},
        {"dur": 8,   "type": "flash"},
        {"dur": 60,  "type": "zoom_logo",  "scale_start": 3.0, "scale_end": 1.0},
        {"dur": 40,  "type": "slide_logo"},
        {"dur": 50,  "type": "full_logo"},
        {"dur": 20,  "type": "flash"},
        {"dur": 30,  "type": "fade_out"},
    ]

    frame = 0
    phase_idx   = 0
    phase_frame = 0

    while phase_idx < len(phases):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN: return
            if event.type == pygame.MOUSEBUTTONDOWN: return

        p = phases[phase_idx]
        t = phase_frame / max(p["dur"] - 1, 1)

        screen.fill(BLACK)

        if p["type"] == "black":
            pass

        elif p["type"] == "flash":
            alpha = int(255 * (1 - t))
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            flash.fill(WHITE)
            flash.set_alpha(alpha)
            screen.blit(flash, (0, 0))

        elif p["type"] == "zoom_logo":
            if BG_MENU:
                screen.blit(BG_MENU, (0, 0))
                draw_overlay(screen, 160)
            if LOGO:
                sc = p["scale_start"] + (p["scale_end"] - p["scale_start"]) * t
                lw = int(LOGO.get_width() * sc)
                lh = int(LOGO.get_height() * sc)
                zoomed = pygame.transform.scale(LOGO, (lw, lh))
                zoomed.set_alpha(int(255 * t))
                screen.blit(zoomed, zoomed.get_rect(center=(_CX, SCREEN_HEIGHT // 2)))

        elif p["type"] == "slide_logo":
            if BG_MENU:
                screen.blit(BG_MENU, (0, 0))
                draw_overlay(screen, 140)
            if LOGO:
                y_start = SCREEN_HEIGHT + LOGO.get_height()
                y_end   = SCREEN_HEIGHT // 2
                y = int(y_start + (y_end - y_start) * (1 - (1-t)**2))
                screen.blit(LOGO, LOGO.get_rect(center=(_CX, y)))

        elif p["type"] == "full_logo":
            if BG_MENU:
                screen.blit(BG_MENU, (0, 0))
                draw_overlay(screen, 120)
            if LOGO:
                screen.blit(LOGO, LOGO.get_rect(center=(_CX, SCREEN_HEIGHT // 2 - 40)))
            if phase_frame > 20 and (phase_frame // 8) % 2 == 0:
                hint = font_hud.render("Pressione qualquer tecla para continuar", True, WHITE)
                screen.blit(hint, hint.get_rect(center=(_CX, SCREEN_HEIGHT - 80)))

        elif p["type"] == "fade_out":
            if BG_MENU:
                screen.blit(BG_MENU, (0, 0))
            ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            ov.fill(BLACK)
            ov.set_alpha(int(255 * t))
            screen.blit(ov, (0, 0))

        pygame.display.flip()
        clock.tick(FPS)

        phase_frame += 1
        if phase_frame >= p["dur"]:
            phase_frame = 0
            phase_idx  += 1
        frame += 1

# ==============================================================================
# BARRA DE VIDA
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

    def hit(self):  self.pos = max(0.0, self.pos - 0.04)
    def miss(self): self.pos = min(1.0, self.pos + 0.06)

    @property
    def dead(self): return self.pos >= 1.0

    def draw(self, surface):
        bar = pygame.Rect(self.x0, self.y - self.BAR_H//2, self.BAR_W, self.BAR_H)
        pygame.draw.rect(surface, (90,90,90), bar, border_radius=8)
        pygame.draw.rect(surface, WHITE, bar, border_radius=8, width=2)
        r_lbl = font_hud.render("BITELO", True, GRAY)
        p_lbl = font_hud.render("TOGURO", True, GRAY)
        surface.blit(r_lbl, r_lbl.get_rect(midright=(self.x0 - 8, self.y)))
        surface.blit(p_lbl, p_lbl.get_rect(midleft=(self.x1 + 8, self.y)))
        icon_x = int(self.x0 + self.BAR_W * self.pos)
        pygame.draw.circle(surface, WHITE,     (icon_x, self.y), 13)
        pygame.draw.circle(surface, DARK_GRAY, (icon_x, self.y), 7)

# ==============================================================================
# ROBÔ IA (Bitelo)
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
# LEADERBOARD
# ==============================================================================
def leaderboard_screen():
    cx       = SCREEN_WIDTH // 2
    btn_back = Button("Voltar", cx, 650, base_size=28, hover_size=36, hover_color=GRAY)
    entries  = load_leaderboard()

    while True:
        mp = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return
            if btn_back.is_clicked(mp, event): return
        btn_back.check_hover(mp)
        btn_back.update()
        update_menu_music()

        draw_bg(screen, BG_MENU)
        draw_overlay(screen, 150)

        title = font_big.render("LEADERBOARD", True, LANE_COLORS[3])
        screen.blit(title, title.get_rect(center=(cx, 80)))
        pygame.draw.line(screen, LANE_COLORS[3], (cx-250, 115), (cx+250, 115), 2)

        if not entries:
            t = font_btn.render("Nenhuma pontuacao ainda!", True, GRAY)
            screen.blit(t, t.get_rect(center=(cx, 350)))
        else:
            header = font_hud.render(f"{'#':<4} {'Nome':<16} {'Score':<10} {'Fase'}", True, GRAY)
            screen.blit(header, header.get_rect(center=(cx, 150)))
            for i, e in enumerate(entries[:10]):
                color = [LANE_COLORS[3], LANE_COLORS[1], LANE_COLORS[2]][min(i, 2)] if i < 3 else WHITE
                row = font_hud.render(
                    f"{i+1:<4} {e.get('name','???'):<16} {e.get('score',0):<10} {e.get('fase','?')}",
                    True, color
                )
                screen.blit(row, row.get_rect(center=(cx, 190 + i * 42)))

        btn_back.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

# ==============================================================================
# INPUT NOME
# ==============================================================================
def input_name_screen(score, fase_name):
    cx   = SCREEN_WIDTH // 2
    name = ""
    done = False

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and name.strip():
                    done = True
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                elif len(name) < 12 and event.unicode.isprintable():
                    name += event.unicode

        draw_bg(screen, BG_MENU)
        draw_overlay(screen, 160)

        t1 = font_big.render(f"Score: {score}", True, LANE_COLORS[1])
        t2 = font_btn.render("Digite seu nome:", True, WHITE)
        t3 = font_btn.render(name + "_", True, LANE_COLORS[3])
        t4 = font_hud.render("ENTER para confirmar", True, GRAY)

        screen.blit(t1, t1.get_rect(center=(cx, 250)))
        screen.blit(t2, t2.get_rect(center=(cx, 330)))
        screen.blit(t3, t3.get_rect(center=(cx, 390)))
        screen.blit(t4, t4.get_rect(center=(cx, 460)))

        pygame.display.flip()
        clock.tick(FPS)

    add_to_leaderboard(name.strip(), score, fase_name)
    return name.strip()

# ==============================================================================
# PAUSA
# ==============================================================================
def pause_menu(bg):
    cx       = SCREEN_WIDTH // 2
    btn_cont = Button("Continuar",      cx, 310, hover_color=LANE_COLORS[1])
    btn_menu = Button("Menu Principal", cx, 400, hover_color=LANE_COLORS[3])
    btn_quit = Button("Sair do Jogo",   cx, 490, hover_color=LANE_COLORS[2])

    while True:
        mp = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: return "continue"
                if event.key == pygame.K_F11: pygame.display.toggle_fullscreen()
            if btn_cont.is_clicked(mp, event):  return "continue"
            if btn_menu.is_clicked(mp, event):  return "menu"
            if btn_quit.is_clicked(mp, event):  pygame.quit(); sys.exit()

        for btn in [btn_cont, btn_menu, btn_quit]:
            btn.check_hover(mp)
            btn.update()

        screen.blit(bg, (0, 0))
        draw_overlay(screen, 170)

        title = font_big.render("PAUSADO", True, WHITE)
        screen.blit(title, title.get_rect(center=(cx, 210)))
        pygame.draw.line(screen, LANE_COLORS[0], (cx-180, 245), (cx+180, 245), 2)

        for btn in [btn_cont, btn_menu, btn_quit]:
            btn.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

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
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return "menu"
            if btn_retry.is_clicked(mp, event): return "retry"
            if btn_menu.is_clicked(mp, event):  return "menu"
        for btn in [btn_retry, btn_menu]:
            btn.check_hover(mp)
            btn.update()

        draw_bg(screen, BG_MENU)
        draw_overlay(screen, 160)

        l1 = font_big.render("Xii... Paizao,", True, LANE_COLORS[2])
        l2 = font_big.render("Sem sabor esse player Ai!!", True, LANE_COLORS[2])
        screen.blit(l1, l1.get_rect(center=(cx, 300)))
        screen.blit(l2, l2.get_rect(center=(cx, 370)))
        for btn in [btn_retry, btn_menu]:
            btn.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

# ==============================================================================
# RESULTADO
# ==============================================================================
def result_screen(score, misses, fase_name):
    input_name_screen(score, fase_name)

    cx       = SCREEN_WIDTH // 2
    btn_back = Button("Menu Principal", cx, 500, hover_color=LANE_COLORS[1])
    lb       = load_leaderboard()
    rank     = next((i+1 for i, e in enumerate(lb) if e["score"] == score), "?")

    while True:
        mp = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "quit"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return "back"
            if btn_back.is_clicked(mp, event): return "back"
        btn_back.check_hover(mp)
        btn_back.update()

        draw_bg(screen, BG_MENU)
        draw_overlay(screen, 150)
        draw_title(screen, cx, 120)

        r_txt = font_big.render("RESULTADO", True, WHITE)
        s_txt = font_btn.render(f"Score:  {score}",   True, WHITE)
        m_txt = font_btn.render(f"Misses: {misses}",  True, LANE_COLORS[2])
        k_txt = font_hud.render(f"Ranking: #{rank}",  True, LANE_COLORS[3])

        screen.blit(r_txt, r_txt.get_rect(center=(cx, 250)))
        screen.blit(s_txt, s_txt.get_rect(center=(cx, 330)))
        screen.blit(m_txt, m_txt.get_rect(center=(cx, 385)))
        screen.blit(k_txt, k_txt.get_rect(center=(cx, 435)))
        btn_back.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

# ==============================================================================
# JOGO
# ==============================================================================
def play_game(song_name, fase_index):
    global _menu_music_playing
    _menu_music_playing = False # Avisa o jogo que saímos do menu
    
    song_path = os.path.join("songs", song_name)
    json_path = os.path.join(song_path, "data.json")
    mp3_path  = os.path.join(song_path, "som.mp3")

    if not os.path.exists(json_path):
        print(f"data.json nao encontrado: {json_path}")
        return "back"
    if not os.path.exists(mp3_path):
        print(f"som.mp3 nao encontrado: {mp3_path}")
        return "back"

    # Para a música do menu e carrega a da fase com a indentação corrigida
    try:
        pygame.mixer.music.stop()
        pygame.mixer.music.load(mp3_path)
        pygame.mixer.music.set_volume(volume)
    except Exception as e:
        print(f"Erro musica: {e}")
        return "back"

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            chart = json.load(f)
    except Exception as e:
        print(f"Erro json: {e}")
        return "back"

    game_bg = get_bg_for_fase(fase_index)

    player_notes = [dict(n) for n in chart["notes"]]
    robo_notes   = [dict(n) for n in chart["notes"]]
    robo_pending = list(robo_notes)

    cx = SCREEN_WIDTH // 2
    
    # --- AJUSTE DE ALINHAMENTO ---
    # Colocamos os personagens a uma distância fixa do centro (cx)
    # Por exemplo: 380 pixels para a direita e 380 para a esquerda
    DISTANCIA_DO_CENTRO = 380
    
    toguro = Character(toguro_sprites, x=cx + DISTANCIA_DO_CENTRO, y=SCREEN_HEIGHT - 50)
    bitelo = Character(bitelo_sprites, x=cx - DISTANCIA_DO_CENTRO, y=SCREEN_HEIGHT - 50, flip=True)

    # A health bar também deve usar o 'cx' para garantir que fique centralizada
    health = HealthBar(cx, 45)
    robo_ai  = RoboAI()
    score    = 0
    misses   = 0
    feedback = []

    # Toca a música da fase sempre a partir do zero
    pygame.mixer.music.play(start=0.0)
    
    start_time = pygame.time.get_ticks() + 1000

    running = True
    while running:
        pause_snapshot = screen.copy()
        current_time   = pygame.time.get_ticks() - start_time

        for n in robo_pending[:]:
            if HIT_ZONE_Y - (n["time"] - current_time) * NOTE_SPEED >= HIT_ZONE_Y - 80:
                robo_ai.schedule(n, current_time)
                robo_pending.remove(n)
        robo_ai.update(robo_notes, current_time, bitelo)
        toguro.update()
        bitelo.update()

        draw_bg(screen, game_bg)
        if game_bg: draw_overlay(screen, 80)

        # Alvos fixos: apenas seta esqueleto, sem caixa colorida
        for i, x in enumerate(LANE_X):
            if seta_alvos[i]:
                screen.blit(seta_alvos[i], seta_alvos[i].get_rect(center=(x, HIT_ZONE_Y)))
            else:
                # Fallback: seta colorida, sem retângulo
                sh = font_arrow.render(LANE_ARROWS[i], True, BLACK)
                t  = font_arrow.render(LANE_ARROWS[i], True, LANE_COLORS[i])
                screen.blit(sh, sh.get_rect(center=(x+2, HIT_ZONE_Y+2)))
                screen.blit(t,  t.get_rect(center=(x, HIT_ZONE_Y)))

        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.mixer.music.pause()
                    result = pause_menu(pause_snapshot)
                    if result == "continue":
                        pygame.mixer.music.unpause()
                        start_time += pygame.time.get_ticks() - (start_time + current_time + 1000)
                    elif result == "menu":
                        pygame.mixer.music.stop()
                        start_menu_music()
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
                    toguro.set_pose(LANE_POSE[lane])
                    hit = False
                    for n in player_notes[:]:
                        if n["lane"] == lane:
                            note_y = HIT_ZONE_Y - (n["time"] - current_time) * NOTE_SPEED
                            if abs(note_y - HIT_ZONE_Y) < 60:
                                player_notes.remove(n)
                                score += 100
                                health.hit()
                                hit = True
                                feedback.append(["OTIMO!", LANE_X[lane], HIT_ZONE_Y-65, 45, LANE_COLORS[1]])
                                break
                    if not hit:
                        misses += 1
                        health.miss()
                        feedback.append(["MISS!", LANE_X[lane], HIT_ZONE_Y-65, 45, LANE_COLORS[2]])

        # Notas caindo
        for n in player_notes[:]:
            note_y = HIT_ZONE_Y - (n["time"] - current_time) * NOTE_SPEED
            if -NOTE_SIZE < note_y < SCREEN_HEIGHT:
                draw_note(screen, n["lane"], LANE_X[n["lane"]], int(note_y), NOTE_SIZE)
            if note_y > SCREEN_HEIGHT + 50:
                player_notes.remove(n)
                misses += 1
                health.miss()

        bitelo.draw(screen)
        toguro.draw(screen)
        health.draw(screen)

        screen.blit(font_hud.render(f"Score: {score}",   True, WHITE),         (20, SCREEN_HEIGHT-55))
        screen.blit(font_hud.render(f"Misses: {misses}", True, LANE_COLORS[2]), (20, SCREEN_HEIGHT-30))
        esc = font_hud.render("ESC=Pausa  F11=Fullscreen", True, MID_GRAY)
        screen.blit(esc, esc.get_rect(bottomright=(SCREEN_WIDTH-10, SCREEN_HEIGHT-10)))

        fase_txt = font_hud.render(f"Fase {fase_index+1}", True, GRAY)
        screen.blit(fase_txt, fase_txt.get_rect(topright=(SCREEN_WIDTH-10, 10)))

        for fb in feedback[:]:
            fb[3] -= 1
            ft = font_hud.render(fb[0], True, fb[4])
            screen.blit(ft, ft.get_rect(center=(fb[1], fb[2] - (45-fb[3]))))
            if fb[3] <= 0: feedback.remove(fb)

        if health.dead:
            pygame.mixer.music.stop()
            r = game_over_screen(song_name)
            if r == "retry":
                start_menu_music()
                return play_game(song_name, fase_index)
            start_menu_music()
            return "back"

        if not pygame.mixer.music.get_busy() and not player_notes:
            running = False

        pygame.display.flip()
        clock.tick(FPS)

    start_menu_music()
    return result_screen(score, misses, f"Fase {fase_index+1}")

# ==============================================================================
# CONFIGURAÇÕES
# ==============================================================================
def settings_menu():
    global volume
    cx       = SCREEN_WIDTH // 2
    btn_back = Button("Voltar", cx, 580, base_size=28, hover_size=36, hover_color=GRAY)
    sx, sw, sy = cx-200, 400, 370
    dragging   = False

    while True:
        mp = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return
            if btn_back.is_clicked(mp, event): return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if sx <= mp[0] <= sx+sw and sy-15 <= mp[1] <= sy+15: dragging = True
            if event.type == pygame.MOUSEBUTTONUP: dragging = False
        if dragging:
            volume = max(0.0, min(1.0, (mp[0]-sx)/sw))
            pygame.mixer.music.set_volume(0.35 * volume / 0.7 if volume > 0 else 0)
        btn_back.check_hover(mp)
        btn_back.update()
        update_menu_music()

        draw_bg(screen, BG_MENU)
        draw_overlay(screen, 150)
        draw_title(screen, cx, 120)

        lbl = font_btn.render("Volume da Musica", True, WHITE)
        screen.blit(lbl, lbl.get_rect(center=(cx, 290)))
        pygame.draw.rect(screen, MID_GRAY,       (sx, sy-6, sw, 12), border_radius=6)
        pygame.draw.rect(screen, LANE_COLORS[3], (sx, sy-6, int(sw*volume), 12), border_radius=6)
        pygame.draw.circle(screen, WHITE, (sx+int(sw*volume), sy), 14)
        pct = font_hud.render(f"{int(volume*100)}%", True, GRAY)
        screen.blit(pct, pct.get_rect(center=(cx, sy+40)))
        btn_back.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

# ==============================================================================
# SELEÇÃO DE FASES
# ==============================================================================
def song_select_menu():
    songs    = load_songs()
    cx       = SCREEN_WIDTH // 2
    btn_back = Button("Voltar", cx, 640, base_size=28, hover_size=36, hover_color=GRAY)

    if not songs:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: return "quit"
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return "back"
            update_menu_music()
            draw_bg(screen, BG_MENU)
            draw_overlay(screen, 150)
            draw_title(screen, cx, 120)
            m = font_med.render("Nenhuma musica encontrada!", True, LANE_COLORS[2])
            screen.blit(m, m.get_rect(center=(cx, 370)))
            pygame.display.flip()
            clock.tick(FPS)

    buttons = [Button(f"Fase {i+1}", cx, 250 + i*75, hover_color=LANE_COLORS[i%4]) for i, s in enumerate(songs)]

    while True:
        mp = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "quit"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return "back"
            if btn_back.is_clicked(mp, event): return "back"
            for i, btn in enumerate(buttons):
                if btn.is_clicked(mp, event):
                    # Faz a transição de música antes de entrar na fase
                    transition_to_game_music()
                    r = play_game(songs[i], i)
                    if r == "quit": return "quit"

        for btn in buttons + [btn_back]:
            btn.check_hover(mp)
            btn.update()

        update_menu_music()
        draw_bg(screen, BG_MENU)
        draw_overlay(screen, 150)
        draw_title(screen, cx, 110)
        sep = font_med.render("-- Selecione a Fase --", True, GRAY)
        screen.blit(sep, sep.get_rect(center=(cx, 200)))
        for btn in buttons + [btn_back]:
            btn.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

# ==============================================================================
# MENU PRINCIPAL
# ==============================================================================
def main_menu():
    cx         = SCREEN_WIDTH // 2
    btn_start  = Button("Comecar",       cx, 390, hover_color=LANE_COLORS[1])
    btn_lb     = Button("Leaderboard",   cx, 465, hover_color=LANE_COLORS[3])
    btn_config = Button("Configuracoes", cx, 540, hover_color=LANE_COLORS[0])
    btn_quit   = Button("Sair",          cx, 615, hover_color=LANE_COLORS[2])
    buttons    = [btn_start, btn_lb, btn_config, btn_quit]

    anim_timer = 0

    # Inicia música do menu ao entrar
    start_menu_music()

    while True:
        mp = pygame.mouse.get_pos()
        anim_timer += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:    pygame.display.toggle_fullscreen()
                if event.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()
            if btn_start.is_clicked(mp, event):
                r = song_select_menu()
                if r == "quit": pygame.quit(); sys.exit()
                # Ao voltar da seleção, retoma música do menu
                start_menu_music()
            if btn_lb.is_clicked(mp, event):     leaderboard_screen()
            if btn_config.is_clicked(mp, event): settings_menu()
            if btn_quit.is_clicked(mp, event):   pygame.quit(); sys.exit()

        for btn in buttons:
            btn.check_hover(mp)
            btn.update()

        # Mantém loop da música do menu (reinicia em 25s)
        update_menu_music()

        draw_bg(screen, BG_MENU)
        draw_overlay(screen, 130)

        float_y = int(math.sin(anim_timer * 0.03) * 6)
        draw_title(screen, cx, 200 + float_y)

        pygame.draw.line(screen, LANE_COLORS[0], (cx-220, 330), (cx+220, 330), 2)

        for btn in buttons:
            btn.draw(screen)

        ft = font_hud.render("F11=Tela cheia  |  ESC=Sair", True, MID_GRAY)
        screen.blit(ft, ft.get_rect(center=(cx, SCREEN_HEIGHT-20)))

        pygame.display.flip()
        clock.tick(FPS)

# ==============================================================================
# ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    primeiro_menu()
    play_intro()
    main_menu()
    pygame.quit()