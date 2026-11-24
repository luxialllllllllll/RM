import pygame
import cv2
import numpy as np

from maze import MAZE, START, EXIT, QR_POSITIONS
from maze import ROWS, COLS


# ==========================
# 窗口配置
# ==========================

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800

CAMERA_X = 20
CAMERA_Y = 100

CAMERA_WIDTH = 780
CAMERA_HEIGHT = 580

MAP_X = 820
MAP_Y = 100

CELL_SIZE = 14


# ==========================
# 颜色配置
# ==========================

BACKGROUND = (15, 23, 42)
PANEL = (30, 41, 59)

WHITE = (248, 250, 252)
GRAY = (148, 163, 184)

FOG = (8, 12, 20)
WALL = (20, 28, 40)
PATH = (100, 116, 139)

GREEN = (74, 222, 128)
BLUE = (56, 189, 248)
YELLOW = (250, 204, 21)
RED = (248, 113, 113)


class GameUI:

    def __init__(self):

        # 初始化 Pygame
        pygame.init()

        self.screen = pygame.display.set_mode(
            (WINDOW_WIDTH, WINDOW_HEIGHT)
        )

        pygame.display.set_caption(
            "Escape Room Robótico Inteligente"
        )

        self.font_title = pygame.font.SysFont(
            "Arial", 28, bold=True
        )

        self.font = pygame.font.SysFont(
            "Arial", 18
        )

        self.font_small = pygame.font.SysFont(
            "Arial", 12
        )

        self.font_value = pygame.font.SysFont(
            "Arial", 22, bold=True
        )

    # ==========================
    # 绘制文字
    # ==========================

    def draw_text(
        self, text, x, y,
        color=WHITE, font=None
    ):

        if font is None:
            font = self.font

        surface = font.render(
            str(text), True, color
        )

        self.screen.blit(surface, (x, y))

    # ==========================
    # 绘制摄像头画面
    # ==========================

    def draw_camera(self, frame):

        self.draw_text(
            "Câmara em tempo real",
            CAMERA_X,
            CAMERA_Y - 30
        )

        pygame.draw.rect(
            self.screen,
            FOG,
            (
                CAMERA_X,
                CAMERA_Y,
                CAMERA_WIDTH,
                CAMERA_HEIGHT
            )
        )

        if frame is None:

            self.draw_text(
                "Sem imagem da câmara",
                CAMERA_X + 250,
                CAMERA_Y + 250,
                GRAY
            )

            return

        # 获取原始画面尺寸
        height, width = frame.shape[:2]

        # 保持画面比例，避免变形
        scale = min(
            CAMERA_WIDTH / width,
            CAMERA_HEIGHT / height
        )

        new_width = int(width * scale)
        new_height = int(height * scale)

        frame = cv2.resize(
            frame,
            (new_width, new_height)
        )

        # OpenCV 使用 BGR，Pygame 使用 RGB
        frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        # 转换为 Pygame 图像
        surface = pygame.surfarray.make_surface(
            np.transpose(frame, (1, 0, 2))
        )

        # 将画面居中
        x = CAMERA_X + (
            CAMERA_WIDTH - new_width
        ) // 2

        y = CAMERA_Y + (
            CAMERA_HEIGHT - new_height
        ) // 2

        self.screen.blit(surface, (x, y))

    # ==========================
    # 绘制迷雾地图
    # ==========================

    def draw_map(self, fog_map):

        self.draw_text(
            "Mapa de exploração",
            MAP_X,
            MAP_Y - 30
        )

        for y in range(ROWS):

            for x in range(COLS):

                rect = pygame.Rect(
                    MAP_X + x * CELL_SIZE,
                    MAP_Y + y * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE
                )

                # 默认全部被迷雾覆盖
                color = FOG

                # 只显示已经探索的通道
                if fog_map.is_explored(x, y):

                    if MAZE[y][x] == "1":
                        color = PATH
                    else:
                        color = WALL

                pygame.draw.rect(
                    self.screen,
                    color,
                    rect
                )

        # 绘制起点
        self.draw_marker(START, GREEN)

        # 只有探索到出口才显示
        if fog_map.is_explored(*EXIT):

            self.draw_marker(EXIT, RED)

        # 只显示已经扫描的二维码
        for qr_id, position in QR_POSITIONS.items():

            if fog_map.is_qr_scanned(qr_id):

                self.draw_marker(
                    position,
                    YELLOW,
                    qr_id
                )

        # 绘制机器人当前位置
        self.draw_marker(
            fog_map.robot_position,
            BLUE
        )

    # ==========================
    # 绘制地图标记
    # ==========================

    def draw_marker(
        self, position, color, label=None
    ):

        x, y = position

        center_x = (
            MAP_X + x * CELL_SIZE
            + CELL_SIZE // 2
        )

        center_y = (
            MAP_Y + y * CELL_SIZE
            + CELL_SIZE // 2
        )

        pygame.draw.circle(
            self.screen,
            color,
            (center_x, center_y),
            5
        )

        if label is not None:

            self.draw_text(
                label,
                center_x + 6,
                center_y - 8,
                color,
                self.font_small
            )

    # ==========================
    # 绘制地图图例
    # ==========================

    def draw_legend(self):

        legend = [
            (GREEN, "Entrada"),
            (BLUE, "Robô"),
            (YELLOW, "Código QR"),
            (RED, "Saída"),
            (PATH, "Zona explorada"),
            (FOG, "Zona desconhecida")
        ]

        for i, (color, label) in enumerate(legend):

            x = MAP_X + (i % 2) * 210
            y = 570 + (i // 2) * 28

            pygame.draw.rect(
                self.screen,
                color,
                (x, y, 14, 14)
            )

            self.draw_text(
                label,
                x + 22,
                y - 3,
                GRAY
            )

    # ==========================
    # 绘制状态卡片
    # ==========================

    def draw_card(
        self, x, title, value, color
    ):

        y = 700
        width = 300
        height = 65

        pygame.draw.rect(
            self.screen,
            PANEL,
            (x, y, width, height),
            border_radius=8
        )

        self.draw_text(
            title,
            x + 12,
            y + 8,
            GRAY
        )

        self.draw_text(
            value,
            x + 12,
            y + 30,
            color,
            self.font_value
        )

    # ==========================
    # 绘制游戏状态
    # ==========================

    def draw_status(
        self, fog_map, state, has_key
    ):

        self.draw_card(
            20,
            "Estado",
            state,
            GREEN
        )

        self.draw_card(
            335,
            "Último código QR",
            fog_map.last_qr,
            BLUE
        )

        key_text = (
            "Encontrada"
            if has_key
            else "Não encontrada"
        )

        self.draw_card(
            650,
            "Chave",
            key_text,
            GREEN if has_key else YELLOW
        )

        self.draw_card(
            965,
            "Exploração",
            f"{fog_map.get_progress():.1f}%",
            BLUE
        )

    # ==========================
    # 更新整个游戏界面
    # ==========================

    def render(
        self,
        frame,
        fog_map,
        state="A explorar",
        has_key=False
    ):

        self.screen.fill(BACKGROUND)

        self.draw_text(
            "ESCAPE ROOM ROBÓTICO",
            20,
            15,
            WHITE,
            self.font_title
        )

        self.draw_camera(frame)

        self.draw_map(fog_map)

        self.draw_legend()

        self.draw_status(
            fog_map,
            state,
            has_key
        )

        self.draw_text(
            "ESC - Sair do jogo",
            20,
            778,
            GRAY,
            self.font_small
        )

        pygame.display.flip()

    # ==========================
    # 处理退出事件
    # ==========================

    def handle_events(self):

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    return False

        return True

    # ==========================
    # 关闭游戏窗口
    # ==========================

    def close(self):

        pygame.quit()


# ==========================
# 独立测试游戏界面
# ==========================

if __name__ == "__main__":

    from camara import Camera
    from fog_map import FogMap

    ui = GameUI()
    fog_map = FogMap()
    camera = None

    clock = pygame.time.Clock()

    try:

        camera = Camera()

        running = True

        while running:

            running = ui.handle_events()

            frame = camera.read()

            ui.render(
                frame,
                fog_map,
                state="Em espera",
                has_key=False
            )

            clock.tick(30)

    finally:

        if camera is not None:
            camera.close()

        ui.close()