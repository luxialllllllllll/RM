
import cv2
import pygame
import numpy as np

from tdmclient import ClientAsync


# ==========================
# 基本配置
# ==========================

CAMERA_ID = 0

# 前进速度
SPEED = 80

# 原地转弯速度
TURN_SPEED = 70

# 障碍物检测阈值
OBSTACLE_THRESHOLD = 3000

# 转弯持续时间（秒）
TURN_TIME = 0.15

# 每次控制循环间隔
LOOP_INTERVAL = 0.03

WINDOW_WIDTH = 960
WINDOW_HEIGHT = 540


# ==========================
# 主程序
# ==========================

async def main():

    # 连接 Thymio 机器人
    with ClientAsync() as client:

        print("A tentar conectar ao Thymio...")

        node = await client.wait_for_node()
        await node.lock()

        print("Thymio conectado!")

        cap = None
        pygame_started = False

        # 自动驾驶状态
        automatic = True

        # 当前运动状态
        state = "FORWARD"

        # 转弯方向
        turn_direction = None

        # 上一次电机指令
        last_command = None

        # ==========================
        # 设置左右电机速度
        # ==========================

        async def move(left, right):

            nonlocal last_command

            command = (left, right)

            # 避免重复发送相同的指令
            if command != last_command:

                await node.set_variables({
                    "motor.left.target": [left],
                    "motor.right.target": [right]
                })

                last_command = command

        try:

            # ==========================
            # 1. 初始化传感器
            # ==========================

            print("A inicializar os sensores...")

            await node.wait_for_variables({
                "prox.horizontal"
            })

            # ==========================
            # 2. 初始化摄像头
            # ==========================

            cap = cv2.VideoCapture(
                CAMERA_ID,
                cv2.CAP_DSHOW
            )

            if not cap.isOpened():
                raise RuntimeError(
                    "Não foi possível abrir a câmara."
                )

            cap.set(
                cv2.CAP_PROP_FRAME_WIDTH,
                640
            )

            cap.set(
                cv2.CAP_PROP_FRAME_HEIGHT,
                480
            )

            cap.set(
                cv2.CAP_PROP_BUFFERSIZE,
                1
            )

            # ==========================
            # 3. 初始化游戏窗口
            # ==========================

            pygame.init()
            pygame_started = True

            screen = pygame.display.set_mode(
                (WINDOW_WIDTH, WINDOW_HEIGHT)
            )

            pygame.display.set_caption(
                "Thymio Escape Room - Automatic"
            )

            clock = pygame.time.Clock()

            font = pygame.font.SysFont(
                "arial",
                22
            )

            warning_font = pygame.font.SysFont(
                "arial",
                30,
                bold=True
            )

            running = True

            await move(0, 0)

            print("Modo automático ativado.")
            print("SPACE: pausar ou continuar")
            print("ESC: sair do jogo")

            # ==========================
            # 4. 游戏主循环
            # ==========================

            while running:

                # ==========================
                # 4.1 处理键盘事件
                # ==========================

                for event in pygame.event.get():

                    if event.type == pygame.QUIT:
                        running = False

                    elif event.type == pygame.KEYDOWN:

                        if event.key == pygame.K_ESCAPE:
                            running = False

                        elif event.key == pygame.K_SPACE:

                            automatic = not automatic

                            if not automatic:

                                await move(0, 0)
                                state = "PAUSED"

                                print("Robô em pausa.")

                            else:

                                state = "FORWARD"

                                print(
                                    "Modo automático retomado."
                                )

                if not running:
                    break

                # ==========================
                # 4.2 读取红外传感器
                # ==========================

                await node.wait_for_variables({
                    "prox.horizontal"
                })

                prox = list(
                    node.v.prox.horizontal[:5]
                )

                # 左侧两个传感器
                left_proximity = max(
                    prox[0],
                    prox[1]
                )

                # 中间传感器
                center_proximity = prox[2]

                # 右侧两个传感器
                right_proximity = max(
                    prox[3],
                    prox[4]
                )

                # 前方整体障碍物强度
                max_proximity = max(prox)

                # 判断前方是否有障碍物
                obstacle_detected = (
                    max_proximity > OBSTACLE_THRESHOLD
                )

                # ==========================
                # 4.3 自动导航
                # ==========================

                if automatic:

                    if obstacle_detected:

                        # 发现障碍物，立即停车
                        if state == "FORWARD":

                            await move(0, 0)

                            print(
                                "Obstáculo detetado!"
                            )

                            # 比较左右两侧的障碍物强度
                            if left_proximity < right_proximity:

                                turn_direction = "LEFT"

                                print(
                                    "A virar para a esquerda."
                                )

                            else:

                                turn_direction = "RIGHT"

                                print(
                                    "A virar para a direita."
                                )

                            state = "TURNING"

                    # ==========================
                    # 转弯状态
                    # ==========================

                    if state == "TURNING":

                        if turn_direction == "LEFT":

                            await move(
                                -TURN_SPEED,
                                TURN_SPEED
                            )

                        else:

                            await move(
                                TURN_SPEED,
                                -TURN_SPEED
                            )

                        # 短时间转弯后重新检测
                        await client.sleep(TURN_TIME)

                        await move(0, 0)

                        state = "CHECKING"

                    # ==========================
                    # 重新检查前方
                    # ==========================

                    elif state == "CHECKING":

                        # 下次循环重新获取传感器数据
                        state = "FORWARD"

                    # ==========================
                    # 前方安全，继续前进
                    # ==========================

                    elif state == "FORWARD":

                        if not obstacle_detected:

                            await move(
                                SPEED,
                                SPEED
                            )

                else:

                    await move(0, 0)

                # ==========================
                # 4.4 读取摄像头画面
                # ==========================

                ret, frame = cap.read()

                if ret:

                    frame = cv2.resize(
                        frame,
                        (
                            WINDOW_WIDTH,
                            WINDOW_HEIGHT
                        )
                    )

                    frame = cv2.cvtColor(
                        frame,
                        cv2.COLOR_BGR2RGB
                    )

                    frame = np.transpose(
                        frame,
                        (1, 0, 2)
                    )

                    surface = pygame.surfarray.make_surface(
                        frame
                    )

                    screen.blit(
                        surface,
                        (0, 0)
                    )

                else:

                    screen.fill(
                        (0, 0, 0)
                    )

                    # 摄像头失败时停止机器人
                    await move(0, 0)
                    automatic = False
                    state = "PAUSED"

                # ==========================
                # 4.5 显示状态信息
                # ==========================

                overlay = pygame.Surface(
                    (WINDOW_WIDTH, 45),
                    pygame.SRCALPHA
                )

                overlay.fill(
                    (0, 0, 0, 170)
                )

                screen.blit(
                    overlay,
                    (0, 0)
                )

                info = font.render(
                    "SPACE: Pause/Resume | ESC: Quit",
                    True,
                    (255, 255, 255)
                )

                screen.blit(
                    info,
                    (15, 10)
                )

                # 显示当前运动状态
                status_text = font.render(
                    f"Estado: {state}",
                    True,
                    (255, 255, 255)
                )

                screen.blit(
                    status_text,
                    (15, 55)
                )

                # 显示左右传感器数值
                sensor_text = font.render(
                    (
                        f"Left: {left_proximity} | "
                        f"Center: {center_proximity} | "
                        f"Right: {right_proximity}"
                    ),
                    True,
                    (255, 255, 255)
                )

                screen.blit(
                    sensor_text,
                    (15, WINDOW_HEIGHT - 35)
                )

                # ==========================
                # 4.6 显示障碍物警告
                # ==========================

                if obstacle_detected:

                    warning = warning_font.render(
                        "OBSTACLE DETECTED",
                        True,
                        (255, 70, 70)
                    )

                    warning_rect = warning.get_rect(
                        center=(
                            WINDOW_WIDTH // 2,
                            130
                        )
                    )

                    screen.blit(
                        warning,
                        warning_rect
                    )

                pygame.display.flip()

                # ==========================
                # 4.7 维持通信
                # ==========================

                await client.sleep(
                    LOOP_INTERVAL
                )

                clock.tick(30)

        finally:

            # ==========================
            # 5. 释放资源
            # ==========================

            print("A parar o robô...")

            try:

                await move(0, 0)

            finally:

                if cap is not None:
                    cap.release()

                if pygame_started:
                    pygame.quit()

                await node.unlock()

            print("Programa terminado.")


ClientAsync.aw(main())
