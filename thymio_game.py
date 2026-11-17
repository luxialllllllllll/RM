
import cv2
import pygame
import numpy as np

from tdmclient import ClientAsync

# ==========================
# 配置
# ==========================

CAMERA_ID = 0

SPEED = 100
TURN_SPEED = 70

WINDOW_WIDTH = 960
WINDOW_HEIGHT = 540


# ==========================
# 主程序
# ==========================

async def main():

    # 连接 Thymio
    with ClientAsync() as client:

        print("正在连接 Thymio...")

        node = await client.wait_for_node()
        await node.lock()

        print("Thymio 连接成功！")

        # 初始化摄像头
        cap = cv2.VideoCapture(
            CAMERA_ID,
            cv2.CAP_DSHOW
        )

        if not cap.isOpened():
            await node.unlock()
            raise RuntimeError(
                "Não foi possível abrir a câmera."
            )

        # 初始化 Pygame
        pygame.init()

        screen = pygame.display.set_mode(
            (WINDOW_WIDTH, WINDOW_HEIGHT)
        )

        pygame.display.set_caption(
            "Thymio Escape Room"
        )

        clock = pygame.time.Clock()

        async def move(left, right):
            await node.set_variables({
                "motor.left.target": [left],
                "motor.right.target": [right]
            })

        running = True
        last_command = None

        try:

            await move(0, 0)

            while running:

                # ==========================
                # 1. 读取键盘
                # ==========================

                for event in pygame.event.get():

                    if event.type == pygame.QUIT:
                        running = False

                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_q:
                            running = False

                keys = pygame.key.get_pressed()

                if not running:
                    command = (0, 0)

                elif keys[pygame.K_SPACE]:
                    command = (0, 0)

                elif keys[pygame.K_UP]:
                    command = (SPEED, SPEED)

                elif keys[pygame.K_DOWN]:
                    command = (-SPEED, -SPEED)

                elif keys[pygame.K_LEFT]:
                    command = (-TURN_SPEED, TURN_SPEED)

                elif keys[pygame.K_RIGHT]:
                    command = (TURN_SPEED, -TURN_SPEED)

                else:
                    command = (0, 0)

                # 仅在指令改变时发送
                if command != last_command:
                    await move(*command)
                    last_command = command

                if not running:
                    break

                # ==========================
                # 2. 读取摄像头
                # ==========================

                ret, frame = cap.read()

                if ret:

                    frame = cv2.resize(
                        frame,
                        (WINDOW_WIDTH, WINDOW_HEIGHT)
                    )

                    # OpenCV BGR -> RGB
                    frame = cv2.cvtColor(
                        frame,
                        cv2.COLOR_BGR2RGB
                    )

                    # 转换成 Pygame Surface
                    frame = np.transpose(
                        frame,
                        (1, 0, 2)
                    )

                    surface = pygame.surfarray.make_surface(
                        frame
                    )

                    screen.blit(surface, (0, 0))

                else:
                    screen.fill((0, 0, 0))

                # ==========================
                # 3. 显示控制信息
                # ==========================

                font = pygame.font.SysFont(
                    "arial",
                    22
                )

                info = font.render(
                    "Arrow Keys: Move | SPACE: Stop | Q: Quit",
                    True,
                    (255, 255, 255)
                )

                # 半透明背景
                overlay = pygame.Surface(
                    (WINDOW_WIDTH, 45),
                    pygame.SRCALPHA
                )

                overlay.fill((0, 0, 0, 150))

                screen.blit(overlay, (0, 0))
                screen.blit(info, (15, 10))

                pygame.display.flip()

                # 保持异步通信运行
                await client.sleep(0.02)

                clock.tick(30)

        finally:

            print("正在停止机器人...")

            try:
                await move(0, 0)
            finally:
                cap.release()
                pygame.quit()
                await node.unlock()

            print("程序已退出")


ClientAsync.aw(main())
