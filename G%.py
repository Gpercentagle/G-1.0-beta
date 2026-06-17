import pygame
import sys
import math
import random
from collections import deque
import datetime
import webbrowser 

# --- Настройки ---
WIDTH, HEIGHT = 800, 480
FPS = 60
FONT_SIZE = 18
LINE_SPACING = 4
PADDING = 10
MAX_LINES = 500
CURSOR_BLINK_MS = 500
PROMPT = "> "
WELCOME_LINE = "welcome G% Version beta 0.2"
SUPPORT_BTN_RECT = pygame.Rect(WIDTH - 120, 10, 110, 35)

# --- Инициализация ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pygame Terminal — Horror v2.0")
clock = pygame.time.Clock()

# Шрифт (fallback)
try:
    font = pygame.font.SysFont('consolas', FONT_SIZE)
    if font is None:
        raise Exception()
except:
    font = pygame.font.Font(None, FONT_SIZE)
line_height = font.get_linesize() + LINE_SPACING

# --- ТЕМЫ ---
theme_dark = {
    'bg': (12, 12, 12),
    'text': (220, 220, 220),
    'prompt': (120, 200, 120),
    'shape_colors': {
        'circle': (200, 80, 80),
        'square': (80, 200, 80),
        'triangle': (80, 80, 200),
        'angle_line': (255, 255, 255),
        'selected_border': (255, 255, 0) # Новый цвет для выделения
    }
}

theme_light = {
    'bg': (235, 235, 235),
    'text': (20, 20, 20),
    'prompt': (0, 140, 0),
    'shape_colors': {
        'circle': (200, 40, 40),
        'square': (40, 160, 40),
        'triangle': (40, 40, 160),
        'angle_line': (20, 20, 20),
        'selected_border': (200, 160, 0) # Новый цвет для выделения
    }
}

theme = theme_dark

# логи / ввод / состояние
lines = deque(maxlen=MAX_LINES)
lines.append(WELCOME_LINE)

current = ""
history = []
history_index = None

shapes = [] # фигуры хранятся и отрисовываются
variables = {}

browser_mode = False
notepad_mode = False
notepad_lines = []

# --- РЕЖИМ РЕДАКТИРОВАНИЯ ---
edit_mode = False              # <-- НОВОЕ: Включен ли режим редактирования
selected_shape_index = None    # <-- НОВОЕ: Индекс выбранной фигуры в списке shapes
mouse_offset = (0, 0)          # <-- НОВОЕ: Смещение мыши для плавного перетаскивания

# --- Курсор ---
show_cursor = True
last_cursor_toggle = pygame.time.get_ticks()

CLEAR_ALIASES = {"clear", "clr", "очистить", "очисть"}
CLEAR_ALL_ALIASES = {"clear all", "clearall", "clear_all", "очистить все", "очиститьвсе"}

def normalize_cmd(s: str) -> str:
    return s.strip().lower() if s else ""

def add_line(text: str):
    lines.append(text)

# --- Рисование страшного лица (вариативное, возвращает поверхность) ---
def draw_horror_face_surface(size, seed=None, scale=1.0, angry_level=0.5, invert=False):
    """Создаёт поверхность с 'лицом' для horror-эффекта."""
    if seed is not None:
        random.seed(seed)
    w, h = size
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    # фон небольших шумах
    for _ in range(int(w*h*0.001)):
        x = random.randint(0, w-1)
        y = random.randint(0, h-1)
        a = random.randint(10, 60)
        surf.set_at((x,y), (random.randint(0,30), random.randint(0,30), random.randint(0,30), a))
    # лицо
    face_w = int(min(w, h) * 0.6 * scale)
    face_h = int(face_w * (1.0 + 0.15*random.random()))
    face_rect = pygame.Rect(0,0,face_w,face_h)
    face_rect.center = (w//2 + random.randint(-10,10), h//2 + random.randint(-10,10))
    base_col = (230, 225, 215) if not invert else (25,25,25)
    pygame.draw.ellipse(surf, base_col + (255,), face_rect)
    # глаза
    eye_w = max(4, int(face_w * (0.12 + 0.06*random.random())))
    eye_h = max(4, int(face_h * (0.18 + 0.08*random.random())))
    lx = face_rect.centerx - int(face_w * (0.22 + 0.02*random.random()))
    rx = face_rect.centerx + int(face_w * (0.22 + 0.02*random.random()))
    ey = face_rect.centery - int(face_h * (0.18 + 0.05*random.random()))
    eye_col = (10,10,10) if not invert else (240,240,240)
    pygame.draw.ellipse(surf, eye_col + (255,), (lx-eye_w//2, ey-eye_h//2, eye_w, eye_h))
    pygame.draw.ellipse(surf, eye_col + (255,), (rx-eye_w//2, ey-eye_h//2, eye_w, eye_h))
    # рот - часто зловеще расширенный в зависимости от angry_level
    mouth_w = int(face_w * (0.45 + 0.4*angry_level))
    mouth_h = int(face_h * (0.12 + 0.15*angry_level))
    mouth_rect = pygame.Rect(0,0,mouth_w,mouth_h)
    mouth_rect.center = (face_rect.centerx + random.randint(-6,6), face_rect.centery + int(face_h * (0.32 + 0.05*random.random())))
    mouth_col = (5,5,5) if not invert else (250, 80, 80)
    pygame.draw.ellipse(surf, mouth_col + (255,), mouth_rect)
    # зубы / зубчатость
    teeth = 4 + int(angry_level * 8)
    for i in range(teeth):
        tx = mouth_rect.left + int(i * (mouth_w / max(1, teeth)))
        tx2 = tx + max(3, mouth_w // max(1, teeth))
        tooth = [
            (tx + 2, mouth_rect.top + mouth_h // 8),
            ((tx + tx2)//2, mouth_rect.top - max(4, mouth_h//4) - random.randint(0,8)),
            (tx2 - 2, mouth_rect.top + mouth_h // 8)
        ]
        pygame.draw.polygon(surf, (240,240,240,255), tooth)
    # дополнительные тени/царапины
    for _ in range(int(20 * angry_level) + 10):
        x1 = random.randint(face_rect.left, face_rect.right)
        y1 = random.randint(face_rect.top, face_rect.bottom)
        x2 = x1 + random.randint(-10, 10)
        y2 = y1 + random.randint(-10, 10)
        pygame.draw.line(surf, (random.randint(10,40),0,0,120), (x1,y1),(x2,y2),1)
    return surf

# --- Horror manager (управляет состоянием horror mode) ---
class HorrorManager:
    def __init__(self):
        self.active = False
        self.start_time = 0
        self.stage = 0
        self.duration = 6000 
        self.last_spawn = 0
        self.particles = []
        self.shake = 0
        self.invert = False
        self.face_seed = random.randint(0,1000000)
        self.face_scale = 1.0
        self.angry = 0.2
        self.typing_queue = deque()
        self.typing_last = 0
        self.typing_interval = 70
        self.typing_pos = 0
        self.typing_target = ""
        self.messages_to_emit = deque()
    def start(self):
        self.active = True
        self.start_time = pygame.time.get_ticks()
        self.stage = 0
        self.particles.clear()
        self.shake = 10
        self.invert = False
        self.face_seed = random.randint(0,1000000)
        self.face_scale = 1.0
        self.angry = 0.2
        self.typing_queue.clear()
        self.typing_last = 0
        self.typing_pos = 0
        self.typing_target = ""
        self.messages_to_emit = deque([
            "[Ошибка 101] Скоро…",
            "[Ошибка 404] Не найдено",
            "[Ошибка 666] Нечто приближается",
            "[WARNING] Процесс вмешался в память"
        ])
    def stop(self):
        self.active = False
        self.particles.clear()
        self.shake = 0
        self.invert = False
        self.typing_queue.clear()
        self.typing_target = ""
    def update(self, now, dt):
        if not self.active:
            return
        elapsed = now - self.start_time
        
        if elapsed < 1500:
            self.stage = 0
            self.shake = int(6 + 10 * (elapsed/1500))
            self.face_scale = 1.0 + 0.25*(elapsed/1500)
            self.angry = 0.3 + 0.6*(elapsed/1500)
            if now - self.last_spawn > 50:
                for _ in range(random.randint(4,8)):
                    self.spawn_particle()
                self.last_spawn = now
        elif elapsed < 3000:
            self.stage = 1
            self.shake = int(14 + 12 * ((elapsed-1500)/1500))
            self.face_scale = 1.25 + 0.35*((elapsed-1500)/1500)
            self.angry = 0.9 * ((elapsed-1500)/1500) + 0.6
            if now - self.last_spawn > 40:
                for _ in range(random.randint(6,12)):
                    self.spawn_particle(big=True)
                self.last_spawn = now
        elif elapsed < 5000:
            self.stage = 2
            self.invert = True if ((elapsed//200) % 2 == 0) else False
            self.shake = int(24 - 4*((elapsed-3000)/2000))
            if now - self.last_spawn > 30:
                for _ in range(random.randint(12,24)):
                    self.spawn_particle(big=True)
                self.last_spawn = now
        else:
            self.stage = 3
            self.shake = 8
            # emit queued messages slowly via typing
            if self.messages_to_emit and not self.typing_target:
                self.typing_target = self.messages_to_emit.popleft()
                self.typing_pos = 0
                self.typing_last = now
            # type characters
            if self.typing_target:
                if now - self.typing_last >= self.typing_interval:
                    self.typing_pos += 1
                    self.typing_last = now
                    # if completed, push to lines and clear
                    if self.typing_pos >= len(self.typing_target):
                        add_line(self.typing_target)
                        self.typing_target = ""
                        self.typing_pos = 0
            if now - self.last_spawn > 150:
                for _ in range(random.randint(2,6)):
                    self.spawn_particle()
                self.last_spawn = now
        # update particles
        for p in list(self.particles):
            p['x'] += p['vx'] * dt/16
            p['y'] += p['vy'] * dt/16
            p['life'] -= dt
            p['alpha'] -= dt * 0.15
            if p['life'] <= 0 or p['alpha'] <= 0:
                try:
                    self.particles.remove(p)
                except:
                    pass
    def spawn_particle(self, big=False):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        vx = random.uniform(-2, 2)
        vy = random.uniform(-2, 2)
        life = random.randint(300, 1800) if not big else random.randint(600, 2400)
        size = random.randint(1,3) if not big else random.randint(2,7)
        alpha = random.randint(80, 200)
        color = (200 + random.randint(0,55), random.randint(0,40), random.randint(0,40))
        self.particles.append({'x': x, 'y': y, 'vx': vx, 'vy': vy, 'life': life, 'size': size, 'alpha': alpha, 'color': color})

    def draw(self, target_surf):
        if not self.active:
            return
        # render face surface
        face_surf = draw_horror_face_surface((WIDTH, HEIGHT), seed=self.face_seed + random.randint(0,999), scale=self.face_scale, angry_level=self.angry, invert=self.invert)
        # maybe rotate a bit by random small angle
        ang = random.uniform(-8, 8) * (self.angry/1.5)
        face_surf = pygame.transform.rotozoom(face_surf, ang, 1.0)
        # draw face with additive-like effect
        face_rect = face_surf.get_rect(center=(WIDTH//2 + random.randint(-10,10), HEIGHT//2 + random.randint(-10,10)))
        target_surf.blit(face_surf, face_rect, special_flags=0)
        # draw particles
        for p in self.particles:
            col = p['color']
            a = max(0, min(255, int(p['alpha'])))
            s = pygame.Surface((p['size']*2, p['size']*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (col[0],col[1],col[2], a), (p['size'], p['size']), p['size'])
            target_surf.blit(s, (int(p['x']), int(p['y'])))
        # occasional red streaks
        if random.random() > 0.97:
            rx1 = random.randint(0, WIDTH)
            ry1 = random.randint(0, HEIGHT)
            rx2 = rx1 + random.randint(-80,80)
            ry2 = ry1 + random.randint(-80,80)
            pygame.draw.line(target_surf, (180,20,20), (rx1,ry1), (rx2,ry2), random.randint(1,3))

horror = HorrorManager()

# --- Всплывающее сообщение ---
class FlashMessage:
    def __init__(self, text, duration=1000, color=(255, 255, 255), size=24, offset_strength=10):
        self.text = text
        self.duration = duration
        self.color = color
        self.start_time = pygame.time.get_ticks()
        self.font = pygame.font.SysFont(None, size)
        self.offset_strength = offset_strength
        self.active = True
        
    def update(self, now):
        if now - self.start_time > self.duration:
            self.active = False
            
    def draw(self, target_surf):
        if not self.active:
            return
            
        elapsed = pygame.time.get_ticks() - self.start_time
        # Альфа-канал для исчезновения (Fade in/out)
        alpha = 255
        if elapsed < 200: # Fade in
            alpha = int(255 * (elapsed / 200))
        elif elapsed > self.duration - 400: # Fade out
            alpha = int(255 * ( (self.duration - elapsed) / 400 ))
        alpha = max(0, min(255, alpha))
        
        # Случайный сдвиг (дрожание)
        offset_x = random.uniform(-self.offset_strength, self.offset_strength) * (alpha / 255)
        offset_y = random.uniform(-self.offset_strength, self.offset_strength) * (alpha / 255)
        
        # Рисование
        col_with_alpha = self.color + (alpha,)
        text_surf = self.font.render(self.text, True, col_with_alpha)
        
        # Центрируем текст, но с небольшим случайным смещением
        x = WIDTH // 2 + offset_x + random.randint(-15, 15)
        y = HEIGHT // 2 + offset_y + random.randint(-15, 15)
        
        text_rect = text_surf.get_rect(center=(int(x), int(y)))
        target_surf.blit(text_surf, text_rect)

flash_messages = [] # <-- Всплывающие сообщения

# --- Функции для режима Edit Mode ---

def get_shape_hitbox(shape):
    """Возвращает прямоугольник (Rect) вокруг фигуры для проверки попадания."""
    t = shape['type']
    if t == 'circle':
        x, y = shape['pos']
        r = shape['r']
        return pygame.Rect(x - r, y - r, 2 * r, 2 * r)
    elif t == 'square':
        return shape['rect']
    elif t == 'triangle':
        # Вычисляем ограничивающий прямоугольник для треугольника
        min_x = min(p[0] for p in shape['points'])
        max_x = max(p[0] for p in shape['points'])
        min_y = min(p[1] for p in shape['points'])
        max_y = max(p[1] for p in shape['points'])
        return pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)
    elif t == 'angle_line':
        # Для линии берем небольшой квадрат вокруг ее центра
        cx, cy = shape['center']
        return pygame.Rect(cx - 20, cy - 20, 40, 40)
    return None

def move_shape(shape, dx, dy):
    """Перемещает фигуру на (dx, dy)."""
    t = shape['type']
    if t == 'circle':
        shape['pos'] = (shape['pos'][0] + dx, shape['pos'][1] + dy)
    elif t == 'square':
        shape['rect'].move_ip(dx, dy)
    elif t == 'triangle':
        shape['points'] = [(p[0] + dx, p[1] + dy) for p in shape['points']]
    elif t == 'angle_line':
        shape['center'] = (shape['center'][0] + dx, shape['center'][1] + dy)


# --- Основной игровой цикл ---
running = True
while running:
    dt = clock.tick(FPS)
    now = pygame.time.get_ticks()

    for event in pygame.event.get():
        # --- мышь ---
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            
            if SUPPORT_BTN_RECT.collidepoint(event.pos):
                # ... (код кнопки поддержки)
                if horror.active:
                    horror.stop()
                    add_line("[Система] Horror остановлен (Support).")
                else:
                    for _ in range(4):
                        screen.fill((255, 0, 0))
                        pygame.display.flip()
                        pygame.time.delay(60)
                        screen.fill(theme['bg'])
                        pygame.display.flip()
                        pygame.time.delay(60)
                    face = draw_horror_face_surface((WIDTH, HEIGHT), seed=random.randint(0,9999), scale=1.15, angry_level=0.9)
                    screen.blit(face, (0, 0))
                    pygame.display.flip()
                    pygame.time.delay(900)
                    add_line('[Ошибка 101] Скоро…')
                    
            elif edit_mode:
                # В режиме редактирования пытаемся выбрать фигуру
                selected_shape_index = None
                for i, shape in enumerate(reversed(shapes)):
                    hitbox = get_shape_hitbox(shape)
                    if hitbox and hitbox.collidepoint(mouse_x, mouse_y):
                        # Найдена фигура. Индекс берется с конца списка (последний отрисованный - первый выбранный)
                        selected_shape_index = len(shapes) - 1 - i
                        
                        # Расчет смещения для плавного перетаскивания
                        if shape['type'] == 'circle':
                            shape_x, shape_y = shape['pos']
                        elif shape['type'] == 'square':
                            shape_x, shape_y = shape['rect'].center
                        elif shape['type'] == 'triangle':
                            min_x = min(p[0] for p in shape['points'])
                            min_y = min(p[1] for p in shape['points'])
                            max_x = max(p[0] for p in shape['points'])
                            max_y = max(p[1] for p in shape['points'])
                            shape_x, shape_y = (min_x + max_x) // 2, (min_y + max_y) // 2
                        elif shape['type'] == 'angle_line':
                            shape_x, shape_y = shape['center']
                            
                        mouse_offset = (mouse_x - shape_x, mouse_y - shape_y)
                        break
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if edit_mode and selected_shape_index is not None:
                add_line(f"[Edit] Фигура {selected_shape_index} перемещена.")
                selected_shape_index = None
                mouse_offset = (0, 0)

        elif event.type == pygame.MOUSEMOTION:
            if edit_mode and selected_shape_index is not None and event.buttons[0]:
                mouse_x, mouse_y = event.pos
                shape = shapes[selected_shape_index]
                
                # Новая центральная позиция для фигуры, компенсирующая смещение
                new_center_x = mouse_x - mouse_offset[0]
                new_center_y = mouse_y - mouse_offset[1]
                
                # Находим текущую центральную позицию фигуры для расчета смещения
                if shape['type'] == 'circle':
                    current_center = shape['pos']
                elif shape['type'] == 'square':
                    current_center = shape['rect'].center
                elif shape['type'] == 'triangle':
                    min_x = min(p[0] for p in shape['points'])
                    min_y = min(p[1] for p in shape['points'])
                    max_x = max(p[0] for p in shape['points'])
                    max_y = max(p[1] for p in shape['points'])
                    current_center = ((min_x + max_x) // 2, (min_y + max_y) // 2)
                elif shape['type'] == 'angle_line':
                    current_center = shape['center']
                    
                # Рассчитываем фактическое смещение (dx, dy)
                dx = new_center_x - current_center[0]
                dy = new_center_y - current_center[1]
                
                # Перемещаем фигуру
                move_shape(shape, dx, dy)
        # --- конец мыши ---

        # --- выход ---
        elif event.type == pygame.QUIT:
            running = False

        # --- клавиатура ---
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_BACKSPACE:
                current = current[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                # ENTER pressed
                add_line(PROMPT + current)
                cmd_raw = current
                cmd = normalize_cmd(current)

                # --- Если мы в режиме блокнота ---
                if notepad_mode:
                    if cmd in {"exit", "выход"}:
                        notepad_mode = False
                        add_line("[Notepad] Закрыт. Возвращаемся в терминал.")
                        history.append(cmd_raw)
                        current = ""
                        history_index = None
                        continue
                    notepad_lines.append(cmd_raw)
                    add_line(f"[Notepad] {cmd_raw}")
                    history.append(cmd_raw)
                    current = ""
                    history_index = None
                    continue
                
                # --- РЕЖИМ РЕДАКТИРОВАНИЯ ---
                if cmd == "edit":
                    edit_mode = True
                    add_line("[Edit Mode] Включен. Перетаскивайте фигуры мышью. Команда 'edit stop' — выйти.")
                    history.append(cmd_raw)
                    current = ""
                    history_index = None
                    continue
                elif cmd == "edit stop":
                    edit_mode = False
                    selected_shape_index = None
                    add_line("[Edit Mode] Выключен.")
                    history.append(cmd_raw)
                    current = ""
                    history_index = None
                    continue

                # --- Режим браузера (С WEBBROWSER) ---
                if cmd == "browser":
                    browser_mode = True
                    add_line("[Browser] Открыт. Введите поисковый запрос (exit — выйти).")
                    history.append(cmd_raw)
                    current = ""
                    history_index = None
                    continue

                if browser_mode:
                    if cmd in {"exit", "quit", "выход"}:
                        browser_mode = False
                        add_line("[Browser] Закрыт.")
                        history.append(cmd_raw)
                        current = ""
                        history_index = None
                        continue
                    
                    search_query = cmd_raw.strip()
                    if search_query:
                        search_url = f"https://www.google.com/search?q={search_query}"
                        
                        add_line(f"[Browser] Открываю браузер с запросом: '{search_query}'...")
                        
                        try:
                            webbrowser.open(search_url) 
                            add_line("[Browser] Браузер должен быть открыт. Возвращайтесь сюда для новых команд.")
                        except Exception as e:
                            add_line(f"[Browser] ОШИБКА: Не удалось открыть браузер. {e}")
                    else:
                        add_line("[Browser] Пожалуйста, введите поисковый запрос.")
                    
                    history.append(cmd_raw)
                    current = ""
                    history_index = None
                    continue
                # --- КОНЕЦ РЕЖИМА БРАУЗЕРА ---

                # --- темы ---
                if cmd == "theme dark":
                    theme = theme_dark
                    add_line("[Тема] Тёмный режим активирован")
                    history.append(cmd_raw)
                    current = ""
                    history_index = None
                    continue
                elif cmd == "theme light":
                    theme = theme_light
                    add_line("[Тема] Светлый режим активирован")
                    history.append(cmd_raw)
                    current = ""
                    history_index = None
                    continue

                # --- очистка ---
                if cmd in CLEAR_ALL_ALIASES:
                    shapes.clear()
                    variables.clear()
                    lines.clear()
                    lines.append(WELCOME_LINE)
                    add_line("[Система] Полная очистка")
                    history.append(cmd_raw)
                    current = ""
                    history_index = None
                    continue
                elif cmd in CLEAR_ALIASES:
                    shapes.clear()
                    add_line("[Система] Все фигуры удалены")
                    history.append(cmd_raw)
                    current = ""
                    history_index = None
                    continue

                # --- set имя число ---
                if cmd.startswith("set "):
                    parts = cmd_raw.split()
                    if len(parts) == 3:
                        name = parts[1]
                        try:
                            value = float(parts[2])
                            if value.is_integer():
                                value = int(value)
                            variables[name] = value
                            add_line(f"[Переменная] {name} = {value}")
                        except:
                            variables[name] = parts[2]
                            add_line(f"[Переменная] {name} = {parts[2]}")
                    else:
                        add_line("Использование: set имя число")
                    history.append(cmd_raw)
                    current = ""
                    history_index = None
                    continue

                # --- imprimer ---
                if cmd.startswith("imprimer"):
                    parts = cmd_raw.split(maxsplit=1)
                    if len(parts) == 2 and parts[1].strip() != "":
                        arg = parts[1].strip()
                        if (arg.startswith('"') and arg.endswith('"')) or (arg.startswith("'") and arg.endswith("'")):
                            add_line(arg[1:-1])
                        else:
                            if arg in variables:
                                add_line(str(variables[arg]))
                            else:
                                add_line(arg)
                    else:
                        try:
                            inside = cmd_raw[cmd_raw.index("(") + 1 : cmd_raw.rindex(")")]
                            inside = inside.strip().strip("'\"")
                            add_line(inside)
                        except:
                            add_line("Ошибка: imprimer x или imprimer('текст')")
                    history.append(cmd_raw)
                    current = ""
                    history_index = None
                    continue
                
                # --- flash ---
                if cmd_raw.lower().startswith("flash"):
                    parts = cmd_raw.split(maxsplit=1)
                    if len(parts) == 2 and parts[1].strip():
                        text = parts[1].strip().strip("'\"")
                        duration = random.randint(800, 1500)
                        size = random.randint(30, 48)
                        color_choice = random.choice([(255, 0, 0), (255, 255, 255), (255, 100, 100)])
                        offset_strength = random.randint(5, 15)
                        flash_messages.append(FlashMessage(text, duration, color_choice, size, offset_strength))
                        add_line(f"[Flash] Сообщение '{text}' показано на {duration}ms.")
                    else:
                        add_line("Использование: flash 'текст'")
                    history.append(cmd_raw)
                    current = ""
                    history_index = None
                    continue

                # --- clock ---
                if cmd == "clock":
                    now_time = datetime.datetime.now()
                    add_line(f"[CLOCK] Текущее время: {now_time.strftime('%H:%M:%S')}")
                    add_line(f"[CLOCK] Дата: {now_time.strftime('%Y-%m-%d')}")
                    history.append(cmd_raw)
                    current = ""
                    history_index = None
                    continue

                # --- system ---
                if cmd == "system":
                    add_line("[SYSTEM] Информация:")
                    add_line(f"FPS: {int(clock.get_fps())}")
                    add_line(f"Строк вывода: {len(lines)}")
                    add_line(f"Фигур: {len(shapes)}")
                    add_line(f"Переменных: {len(variables)}")
                    add_line(f"Тема: {'dark' if theme is theme_dark else 'light'}")
                    add_line(f"Браузер: {'ON' if browser_mode else 'OFF'}")
                    add_line(f"Edit Mode: {'ON' if edit_mode else 'OFF'}") # <-- НОВОЕ
                    add_line(f"Horror: {'ON' if horror.active else 'OFF'}")
                    history.append(cmd_raw)
                    current = ""
                    history_index = None
                    continue

                # --- фигуры ---
                if cmd == "круг":
                    shapes.append({'type': 'circle', 'pos': (WIDTH // 2, HEIGHT // 2), 'r': 60})
                    add_line("[Фигура] Круг добавлен")
                    history.append(cmd_raw)
                    current = ""
                    history_index = None
                    continue
                if cmd == "квадрат":
                    shapes.append({'type': 'square', 'rect': pygame.Rect(WIDTH // 2 - 60, HEIGHT // 2 - 60, 120, 120)})
                    add_line("[Фигура] Квадрат добавлен")
                    history.append(cmd_raw)
                    current = ""
                    history_index = None
                    continue
                if cmd == "треугольник":
                    shapes.append({'type': 'triangle', 'points': [
                        (WIDTH // 2, HEIGHT // 2 - 70),
                        (WIDTH // 2 - 70, HEIGHT // 2 + 70),
                        (WIDTH // 2 + 70, HEIGHT // 2 + 70)
                    ]})
                    add_line("[Фигура] Треугольник добавлен")
                    history.append(cmd_raw)
                    current = ""
                    history_index = None
                    continue

                # --- добавление блокнота через команду ---
                if cmd in {"notepad", "блокнот"}:
                    notepad_mode = True
                    add_line("[Notepad] Открыт. Введите строки. Команда 'exit' закрывает блокнот.")
                    history.append(cmd_raw)
                    current = ""
                    history_index = None
                    continue

                # --- число — угол линии ---
                try:
                    v = int(cmd)
                    if -360 <= v <= 360:
                        shapes.append({'type': 'angle_line', 'angle': v, 'center': (WIDTH // 2, HEIGHT // 2), 'length': 200})
                        add_line(f"[Линия] Под {v}°")
                    else:
                        add_line(cmd_raw)
                except:
                    if current.strip():
                        add_line(current)
                history.append(cmd_raw)
                current = ""
                history_index = None

            # стрелки истории
            elif event.key == pygame.K_UP:
                if history:
                    if history_index is None:
                        history_index = len(history) - 1
                    else:
                        history_index = max(0, history_index - 1)
                    current = history[history_index]
            elif event.key == pygame.K_DOWN:
                if history:
                    if history_index is None:
                        pass
                    else:
                        history_index += 1
                        if history_index >= len(history):
                            history_index = None
                            current = ""
                        else:
                            current = history[history_index]
            else:
                ch = event.unicode
                if ch and ord(ch) >= 32:
                    current += ch

            # --- конец событий ---

    # курсор мигает
    if now - last_cursor_toggle >= CURSOR_BLINK_MS:
        show_cursor = not show_cursor
        last_cursor_toggle = now

    # update horror manager
    horror.update(now, dt)
    
    # update flash messages
    for msg in list(flash_messages):
        msg.update(now)
        if not msg.active:
            flash_messages.remove(msg)

    # --- Рисование ---
    # prepare base surface (we may shake / offset it)
    base = pygame.Surface((WIDTH, HEIGHT))
    base.fill(theme['bg'])

    # кнопка поддержки
    pygame.draw.rect(base, (60, 60, 60), SUPPORT_BTN_RECT, border_radius=6)
    text_sup = font.render("Поддержка", True, (230, 230, 230))
    base.blit(text_sup, (SUPPORT_BTN_RECT.x + 5, SUPPORT_BTN_RECT.y + 8))

    # фигуры
    for i, s in enumerate(shapes):
        t = s['type']
        
        # Рисуем саму фигуру
        color = theme['shape_colors'][t]
        if t == 'circle':
            pygame.draw.circle(base, color, s['pos'], s['r'])
        elif t == 'square':
            pygame.draw.rect(base, color, s['rect'])
        elif t == 'triangle':
            pygame.draw.polygon(base, color, s['points'])
        elif t == 'angle_line':
            ang = math.radians(s['angle'])
            cx, cy = s['center']
            length = s['length']
            x2 = cx + math.cos(ang) * length
            y2 = cy - math.sin(ang) * length
            pygame.draw.line(base, color, (cx, cy), (x2, y2), 3)
            
        # Рисуем выделение, если фигура выбрана в режиме Edit Mode
        if edit_mode and i == selected_shape_index:
            hitbox = get_shape_hitbox(s)
            if hitbox:
                # Рисуем рамку вокруг фигуры
                padding = 5
                border_rect = hitbox.inflate(padding*2, padding*2)
                pygame.draw.rect(base, theme['shape_colors']['selected_border'], border_rect, 2, border_radius=3)


    # всплывающие сообщения
    for msg in flash_messages:
        msg.draw(base)
        
    # лог (draw onto base)
    max_visible = (HEIGHT - 3 * PADDING - line_height) // line_height
    start = max(0, len(lines) - max_visible)
    visible = list(lines)[start:]
    y = PADDING
    for ln in visible:
        surf = font.render(ln, True, theme['text'])
        base.blit(surf, (PADDING, y))
        y += line_height

    # строка ввода
    input_y = HEIGHT - PADDING - line_height
    
    prompt_text = PROMPT
    prompt_color = theme['prompt']
    
    if notepad_mode:
        prompt_text = "[Notepad] "
    elif browser_mode:
        prompt_text = "[Browser] "
        prompt_color = (80, 160, 255) # Синий для браузера
    elif edit_mode: # <-- НОВОЕ: Промпт для режима редактирования
        prompt_text = "[EDIT] "
        prompt_color = theme['shape_colors']['selected_border']
        
    prompt_surf = font.render(prompt_text, True, prompt_color)
    base.blit(prompt_surf, (PADDING, input_y))
    input_surf = font.render(current, True, theme['text'])
    base.blit(input_surf, (PADDING + prompt_surf.get_width(), input_y))


    if show_cursor:
        current_prompt_width = prompt_surf.get_width()
        cursor_x = PADDING + current_prompt_width + input_surf.get_width()
        cursor_y = input_y
        cursor_rect = pygame.Rect(cursor_x, cursor_y + 3, 8, line_height - 6)
        pygame.draw.rect(base, theme['text'], cursor_rect)

    # apply horror drawing / effects onto base
    if horror.active:
        horror.draw(base)
        if horror.invert:
            inv = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            inv.fill((255,255,255,30))
            base.blit(inv, (0,0), special_flags=pygame.BLEND_RGBA_SUB)
        # screen shake: random small offset
        offset_x = random.randint(-horror.shake, horror.shake)
        offset_y = random.randint(-horror.shake, horror.shake)
    else:
        offset_x = 0
        offset_y = 0

    # draw subtle box for modes
    if notepad_mode or browser_mode or edit_mode: # <-- ДОБАВЛЕН edit_mode
        box_h = line_height + PADDING // 2
        box = pygame.Surface((WIDTH - 2*PADDING, box_h), pygame.SRCALPHA)
        if browser_mode:
            color = (50, 50, 200, 40)
        elif edit_mode:
            color = (255, 255, 0, 40) # Желтоватый для Edit Mode
        else: # Notepad
            color = (0, 0, 0, 40)
            
        box.fill(color)
        base.blit(box, (PADDING, input_y - 2))
        
    # final blit to screen with offset (shake)
    screen.fill((0,0,0))
    screen.blit(base, (offset_x, offset_y))

    # if horror active, draw some translucent scanlines / flicker
    if horror.active:
        flick = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for i in range(0, WIDTH, 20):
            a = random.randint(5,30)
            pygame.draw.line(flick, (0,0,0,a), (i,0), (i + random.randint(-4,4), HEIGHT), 1)
        screen.blit(flick, (0,0), special_flags=pygame.BLEND_RGBA_SUB)

    pygame.display.flip()

    # --- Команды управления horror через ввод ---
    if history:
        last_cmd = history[-1] if history else ""
        lc = normalize_cmd(last_cmd)
        
        if lc == "horror":
            if not horror.active:
                horror.start()
                add_line("[Horror] Страшный режим 2.0 запущен. Для остановки: 'horror stop' или нажмите Поддержка.")
            else:
                add_line("[Horror] Уже запущен.")
            history[-1] = ""
        elif lc == "horror stop":
            if horror.active:
                horror.stop()
                add_line("[Horror] Режим остановлен пользователем.")
            else:
                add_line("[Horror] Режим не был активен.")
            history[-1] = ""

# выход
pygame.quit()
sys.exit() 