import pygame
from random import randint
import sqlite3

pygame.init()

WIDTH, HEIGHT = 800, 600
FPS = 60

window = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

pygame.display.set_caption('Танки')
pygame.display.set_icon(pygame.image.load('images/tank1.png'))

fontUI = pygame.font.Font(None, 30)
fontBig = pygame.font.Font(None, 70)
fontTitle = pygame.font.Font(None, 140)

imgBrick = pygame.image.load('images/block_brick.png')
imgTanks = [
    pygame.image.load('images/tank1.png'),
    pygame.image.load('images/tank2.png'),
    pygame.image.load('images/tank3.png'),
    pygame.image.load('images/tank4.png'),
    pygame.image.load('images/tank5.png'),
    pygame.image.load('images/tank6.png'),
    pygame.image.load('images/tank7.png'),
    pygame.image.load('images/tank8.png'), ]
imgBangs = [
    pygame.image.load('images/bang1.png'),
    pygame.image.load('images/bang2.png'),
    pygame.image.load('images/bang3.png'),
    pygame.image.load('images/bang2.png'),
    pygame.image.load('images/bang1.png'), ]
imgBonuses = [
    pygame.image.load('images/bonus_star.png'),
    pygame.image.load('images/bonus_tank.png'), ]

sndShot = pygame.mixer.Sound('sounds/shot.wav')
sndDestroy = pygame.mixer.Sound('sounds/destroy.wav')
sndDead = pygame.mixer.Sound('sounds/dead.wav')
sndLive = pygame.mixer.Sound('sounds/live.wav')
sndStar = pygame.mixer.Sound('sounds/star.wav')
pygame.mixer.music.load('sounds/level_start.mp3')
pygame.mixer.music.play()

DIRECTS = [[0, -1], [1, 0], [0, 1], [-1, 0]]
TILE = 32

MOVE_SPEED = [1, 2, 2, 1, 2, 3, 3, 2]
BULLET_SPEED = [4, 5, 6, 5, 5, 5, 6, 7]
BULLET_DAMAGE = [1, 1, 2, 3, 2, 2, 3, 4]
SHOT_DELAY = [60, 50, 30, 40, 30, 25, 25, 30]

# Глобальные переменные для настроек
game_time = 300  # Время игры по умолчанию (5 минут)
tank_hp = 5  # Количество жизней по умолчанию


# База данных
def create_database():
    conn = sqlite3.connect('tank_game.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player1 TEXT NOT NULL,
            player2 TEXT NOT NULL,
            score1 INTEGER NOT NULL,
            score2 INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def register_player(login, password):
    conn = sqlite3.connect('tank_game.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO players (login, password) VALUES (?, ?)', (login, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:  # Если логин уже существует
        return False
    finally:
        conn.close()


def login_player(login, password):
    conn = sqlite3.connect('tank_game.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM players WHERE login = ? AND password = ?', (login, password))
    player = cursor.fetchone()
    conn.close()
    return player is not None


def save_match_result(player1, player2, score1, score2):
    conn = sqlite3.connect('tank_game.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO matches (player1, player2, score1, score2) VALUES (?, ?, ?, ?)',
                   (player1, player2, score1, score2))
    conn.commit()
    conn.close()


# Создаем базу данных при запуске
create_database()


class Tank:
    def __init__(self, color, px, py, direct, keysList, nickname, hp):
        objects.append(self)
        self.type = 'tank'

        self.color = color
        self.rect = pygame.Rect(px, py, TILE, TILE)
        self.direct = direct
        self.moveSpeed = 2

        self.shotTimer = 0
        self.shotDelay = 60
        self.bulletSpeed = 5
        self.bulletDamage = 1
        self.isMove = False

        self.hp = hp
        self.nickname = nickname

        self.keyLEFT = keysList[0]
        self.keyRIGHT = keysList[1]
        self.keyUP = keysList[2]
        self.keyDOWN = keysList[3]
        self.keySHOT = keysList[4]

        self.rank = 0
        self.image = pygame.transform.rotate(imgTanks[self.rank], -self.direct * 90)
        self.rect = self.image.get_rect(center=self.rect.center)

    def update(self, keys):
        self.image = pygame.transform.rotate(imgTanks[self.rank], -self.direct * 90)
        self.image = pygame.transform.scale(self.image, (self.image.get_width() - 5, self.image.get_height() - 5))
        self.rect = self.image.get_rect(center=self.rect.center)

        self.moveSpeed = MOVE_SPEED[self.rank]
        self.bulletDamage = BULLET_DAMAGE[self.rank]
        self.bulletSpeed = BULLET_SPEED[self.rank]
        self.shotDelay = SHOT_DELAY[self.rank]

        oldX, oldY = self.rect.topleft
        if keys[self.keyUP]:
            self.rect.y -= self.moveSpeed
            self.direct = 0
            self.isMove = True
        elif keys[self.keyRIGHT]:
            self.rect.x += self.moveSpeed
            self.direct = 1
            self.isMove = True
        elif keys[self.keyDOWN]:
            self.rect.y += self.moveSpeed
            self.direct = 2
            self.isMove = True
        elif keys[self.keyLEFT]:
            self.rect.x -= self.moveSpeed
            self.direct = 3
            self.isMove = True
        else:
            self.isMove = False

        # Ограничение на выход за границы поля
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > HEIGHT:
            self.rect.bottom = HEIGHT

        if keys[self.keySHOT] and self.shotTimer == 0:
            dx = DIRECTS[self.direct][0] * self.bulletSpeed
            dy = DIRECTS[self.direct][1] * self.bulletSpeed
            Bullet(self, self.rect.centerx, self.rect.centery, dx, dy, self.bulletDamage)
            self.shotTimer = self.shotDelay

        if self.shotTimer > 0: self.shotTimer -= 1

        for obj in objects:
            if obj != self and obj.type == 'block':
                if self.rect.colliderect(obj):
                    self.rect.topleft = oldX, oldY

    def draw(self):
        window.blit(self.image, self.rect)

    def damage(self, value):
        self.hp -= value
        if self.hp <= 0:
            objects.remove(self)
            sndDead.play()
            print(self.nickname, 'is dead')


class Bullet:
    def __init__(self, parent, px, py, dx, dy, damage):
        self.parent = parent
        self.px, self.py = px, py
        self.dx, self.dy = dx, dy
        self.damage = damage

        bullets.append(self)
        sndShot.play()

    def update(self):
        self.px += self.dx
        self.py += self.dy

        if self.px < 0 or self.px > WIDTH or self.py < 0 or self.py > HEIGHT:
            bullets.remove(self)
        else:
            for obj in objects:
                if obj != self.parent and obj.type != 'bang' and obj.type != 'bonus':
                    if obj.rect.collidepoint(self.px, self.py):
                        obj.damage(self.damage)
                        bullets.remove(self)
                        Bang(self.px, self.py)
                        sndDestroy.play()
                        break

    def draw(self):
        pygame.draw.circle(window, 'yellow', (self.px, self.py), 2)


class Bang:
    def __init__(self, px, py):
        objects.append(self)
        self.type = 'bang'

        self.px, self.py = px, py
        self.frame = 0

    def update(self):
        self.frame += 0.2
        if self.frame >= 5: objects.remove(self)

    def draw(self):
        img = imgBangs[int(self.frame)]
        rect = img.get_rect(center=(self.px, self.py))
        window.blit(img, rect)


class Block:
    def __init__(self, px, py, size):
        objects.append(self)
        self.type = 'block'

        self.rect = pygame.Rect(px, py, size, size)
        self.hp = 1

    def update(self):
        pass

    def draw(self):
        window.blit(imgBrick, self.rect)

    def damage(self, value):
        self.hp -= value
        if self.hp <= 0: objects.remove(self)


class Bonus:
    def __init__(self, px, py, bonusNum):
        objects.append(self)
        self.type = 'bonus'

        self.px, self.py = px, py
        self.bonusNum = bonusNum
        self.timer = 600

        self.image = imgBonuses[self.bonusNum]
        self.rect = self.image.get_rect(center=(self.px, self.py))

    def update(self):
        if self.timer > 0:
            self.timer -= 1
        else:
            objects.remove(self)

        for obj in objects:
            if obj.type == 'tank' and self.rect.colliderect(obj.rect):
                if self.bonusNum == 0:
                    if obj.rank < len(imgTanks) - 1:
                        obj.rank += 1
                        sndStar.play()
                        objects.remove(self)
                        break
                elif self.bonusNum == 1:
                    obj.hp += 1
                    sndLive.play()
                    objects.remove(self)
                    break

    def draw(self):
        if self.timer % 30 < 15:
            window.blit(self.image, self.rect)


class Button:
    def __init__(self, text, x, y, width, height, color, hover_color):
        self.text = text
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.hover_color = hover_color

    def draw(self, screen):
        mouse = pygame.mouse.get_pos()
        if self.x < mouse[0] < self.x + self.width and self.y < mouse[1] < self.y + self.height:
            pygame.draw.rect(screen, self.hover_color, (self.x, self.y, self.width, self.height))
        else:
            pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))

        text_surface = fontUI.render(self.text, True, 'white')
        text_rect = text_surface.get_rect(center=(self.x + self.width / 2, self.y + self.height / 2))
        screen.blit(text_surface, text_rect)

    def is_clicked(self, mouse_pos):
        return self.x < mouse_pos[0] < self.x + self.width and self.y < mouse_pos[1] < self.y + self.height


def login_menu():
    input_box1 = pygame.Rect(300, 180, 200, 40)
    input_box2 = pygame.Rect(300, 250, 200, 40)
    login_button = Button("Войти", 300, 320, 200, 50, 'blue', 'green')
    register_button = Button("Регистрация", 300, 400, 200, 50, 'blue', 'green')
    back_button = Button("Выйти", 300, 480, 200, 50, 'blue', 'green')  # Новая кнопка
    active_box = 1
    login = ""
    password = ""

    while True:
        window.fill('black')
        title = fontTitle.render('Вход', True, 'white')
        window.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))

        pygame.draw.rect(window, 'white', input_box1, 2)
        pygame.draw.rect(window, 'white', input_box2, 2)
        login_button.draw(window)
        register_button.draw(window)
        back_button.draw(window)  # Отображаем новую кнопку

        login_surface = fontUI.render(login, True, 'white')
        password_surface = fontUI.render("*" * len(password), True, 'white')
        window.blit(login_surface, (input_box1.x + 10, input_box1.y + 10))
        window.blit(password_surface, (input_box2.x + 10, input_box2.y + 10))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if login_button.is_clicked(mouse_pos):
                    if login_player(login, password):
                        return login
                    else:
                        print("Ошибка входа!")
                elif register_button.is_clicked(mouse_pos):
                    if register_player(login, password):
                        print("Регистрация успешна!")
                    else:
                        print("Логин уже занят!")
                elif back_button.is_clicked(mouse_pos):  # Обработка нажатия "Выйти в главное меню"
                    return None  # Возвращаемся в главное меню
                if input_box1.collidepoint(mouse_pos):
                    active_box = 1
                elif input_box2.collidepoint(mouse_pos):
                    active_box = 2
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    if active_box == 1:
                        login = login[:-1]
                    else:
                        password = password[:-1]
                else:
                    if active_box == 1:
                        login += event.unicode
                    else:
                        password += event.unicode

        pygame.display.update()
        clock.tick(FPS)


def main_menu():
    play_button = Button("Играть", 300, 200, 200, 50, 'blue', 'green')
    settings_button = Button("Настройки", 300, 300, 200, 50, 'blue', 'green')
    exit_button = Button("Выход", 300, 400, 200, 50, 'blue', 'green')

    while True:
        window.fill('black')
        title = fontTitle.render('Танки', True, 'white')
        window.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))

        play_button.draw(window)
        settings_button.draw(window)
        exit_button.draw(window)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if play_button.is_clicked(mouse_pos):
                    player1 = login_menu()
                    if player1:
                        player2 = login_menu()
                        if player2:
                            game_loop(player1, player2)
                elif settings_button.is_clicked(mouse_pos):
                    settings_menu()
                elif exit_button.is_clicked(mouse_pos):
                    pygame.quit()
                    return

        pygame.display.update()
        clock.tick(FPS)


def settings_menu():
    global game_time, tank_hp
    time_button_1 = Button("1 минута", 150, 200, 200, 50, 'red', 'green')
    time_button_5 = Button("5 минут", 150, 300, 200, 50, 'red', 'green')
    time_button_10 = Button("10 минут", 150, 400, 200, 50, 'red', 'green')
    hp_button_1 = Button("1 жизнь", 460, 200, 200, 50, 'red', 'green')
    hp_button_3 = Button("3 жизни", 460, 300, 200, 50, 'red', 'green')
    hp_button_5 = Button("5 жизней", 460, 400, 200, 50, 'red', 'green')
    hp_button_10 = Button("10 жизней", 460, 500, 200, 50, 'red', 'green')
    back_button = Button("Назад", 150, 500, 200, 50, 'red', 'green')

    while True:
        window.fill('black')
        title = fontTitle.render('Настройки', True, 'white')
        window.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))

        time_button_1.draw(window)
        time_button_5.draw(window)
        time_button_10.draw(window)
        hp_button_1.draw(window)
        hp_button_3.draw(window)
        hp_button_5.draw(window)
        hp_button_10.draw(window)
        back_button.draw(window)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if time_button_1.is_clicked(mouse_pos):
                    game_time = 60
                elif time_button_5.is_clicked(mouse_pos):
                    game_time = 300
                elif time_button_10.is_clicked(mouse_pos):
                    game_time = 600
                elif hp_button_1.is_clicked(mouse_pos):
                    tank_hp = 1
                elif hp_button_3.is_clicked(mouse_pos):
                    tank_hp = 3
                elif hp_button_5.is_clicked(mouse_pos):
                    tank_hp = 5
                elif hp_button_10.is_clicked(mouse_pos):
                    tank_hp = 10
                elif back_button.is_clicked(mouse_pos):
                    return

        pygame.display.update()
        clock.tick(FPS)


def game_loop(player1_login, player2_login):
    global game_time, tank_hp, bullets, objects
    bullets = []  # Инициализируем bullets
    objects = []  # Инициализируем objects

    tank1 = Tank('blue', 50, 50, 1, (pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s, pygame.K_SPACE), player1_login,
                 tank_hp)
    tank2 = Tank('red', 700, 500, 3, (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN, pygame.K_RETURN),
                 player2_login, tank_hp)

    for _ in range(100):
        while True:
            x = randint(0, WIDTH // TILE - 1) * TILE
            y = randint(1, HEIGHT // TILE - 1) * TILE
            rect = pygame.Rect(x, y, TILE, TILE)
            fined = False
            for obj in objects:
                if rect.colliderect(obj): fined = True
            if not fined: break
        Block(x, y, TILE)

    bonusTimer = 180
    timer = 0
    isMove = False
    isWin = False
    y = 0
    paused = False  # Состояние паузы

    start_ticks = pygame.time.get_ticks()

    play = True
    while play:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                play = False
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:  # Обработка паузы
                    paused = not paused  # Переключаем состояние паузы

        if not paused:  # Если игра не на паузе
            keys = pygame.key.get_pressed()  # Получаем состояние клавиш

            seconds_left = game_time - (pygame.time.get_ticks() - start_ticks) // 1000
            if seconds_left < 0:
                seconds_left = 0

            if seconds_left == 0 and not isWin:
                isWin = True
                timer = 1000

            timer += 1
            oldIsMove = isMove
            isMove = False
            for obj in objects:
                if obj.type == 'tank': isMove = isMove or obj.isMove

            if bonusTimer > 0:
                bonusTimer -= 1
            else:
                Bonus(randint(50, WIDTH - 50), randint(50, HEIGHT - 50), randint(0, len(imgBonuses) - 1))
                bonusTimer = randint(120, 240)

            for bullet in bullets: bullet.update()
            for obj in objects:
                if obj.type == 'tank':
                    obj.update(keys)  # Передаём keys только для танков
                else:
                    obj.update()  # Для других объектов keys не требуется

        window.fill('black')
        for bullet in bullets: bullet.draw()
        for obj in objects: obj.draw()

        timer_text = fontUI.render(f"Time: {seconds_left // 60:02}:{seconds_left % 60:02}", True, 'white')
        window.blit(timer_text, (WIDTH // 2 - 50, 10))

        i = 0
        for obj in objects:
            if obj.type == 'tank':
                pygame.draw.rect(window, obj.color, (5 + i * 70, 5, 22, 22))
                text = fontUI.render(str(obj.rank), 1, 'black')
                rect = text.get_rect(center=(5 + i * 70 + 11, 5 + 11))
                window.blit(text, rect)
                text = fontUI.render(str(obj.hp), 1, obj.color)
                rect = text.get_rect(center=(5 + i * 70 + TILE, 5 + 11))
                window.blit(text, rect)
                i += 1

        t = 0
        tankWin = None
        for obj in objects:
            if obj.type == 'tank':
                t += 1
                tankWin = obj

        if t == 1 and not isWin:
            isWin = True
            timer = 1000

        if timer < 260:
            y += 2
            pygame.draw.rect(window, 'white', (WIDTH // 2 - 300, HEIGHT // 2 - 200 + y, 600, 250))
            pygame.draw.rect(window, 'red', (WIDTH // 2 - 300, HEIGHT // 2 - 200 + y, 600, 250), 3)
            text = fontTitle.render('ТАНКИ', 1, 'black')
            rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100 + y))
            window.blit(text, rect)
            text = fontBig.render('Яндекс Лицей', 1, 'black')
            rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20 + y))
            window.blit(text, rect)

        if t == 1:
            text = fontBig.render(f'ПОБЕДИЛ {tankWin.nickname}', 1, 'white')
            rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))
            window.blit(text, rect)

            # Сохраняем результат матча с счётом
            if tankWin.nickname == player1_login:
                save_match_result(player1_login, player2_login, tank2.hp, tank1.hp)
            else:
                save_match_result(player1_login, player2_login, tank2.hp, tank1.hp)

            # Задержка перед возвратом в меню
            pygame.display.update()
            pygame.time.wait(3000)  # Ждем 3 секунды
            return  # Возвращаемся в главное меню

        if isWin and timer == 1000:
            pygame.mixer.music.load('sounds/level_finish.mp3')
            pygame.mixer.music.play()

        # Отображение "НИЧЬЯ" при окончании времени
        if seconds_left == 0:
            text = fontBig.render('НИЧЬЯ', 1, 'white')
            rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            window.blit(text, rect)

            # Сохраняем результат матча (ничья)
            save_match_result(player1_login, player2_login, tank1.hp, tank2.hp)

            # Задержка перед возвратом в меню
            pygame.display.update()
            pygame.time.wait(3000)  # Ждем 3 секунды
            return  # Возвращаемся в главное меню

        # Отображение паузы
        if paused:
            pause_text = fontBig.render('ПАУЗА', 1, 'white')
            rect = pause_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            window.blit(pause_text, rect)

        pygame.display.update()
        clock.tick(FPS)


# Запуск игры
if __name__ == "__main__":
    main_menu()