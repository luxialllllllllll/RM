
import cv2
import pygame
import numpy as np

from tdmclient import ClientAsync

# ==========================
# 基本配置
# ==========================

CAMERA_ID = 0

SPEED = 100
TURN_SPEED = 70

# 障碍物检测阈值，需要根据实际测试调整
OBSTACLE_THRESHOLD = 2000

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

        # 设置左右电机速度
        async def move(left, right):
            await node.set_variables({
                "motor.left.target": [left],
                "motor.right.target": [right]
            })

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

            # 设置摄像头分辨率
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

            # 尝试减少摄像头缓冲延迟
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            # ==========================
            # 3. 初始化游戏窗口
            # ==========================

            pygame.init()
            pygame_started = True

            screen = pygame.display.set_mode(
                (WINDOW_WIDTH, WINDOW_HEIGHT)
            )

            pygame.display.set_caption(
                "Thymio Escape Room"
            )

            clock = pygame.time.Clock()

            font = pygame.font.SysFont("arial", 22)

            warning_font = pygame.font.SysFont(
                "arial", 30, bold=True
            )

            running = True
            last_command = None

            # 启动时先停止机器人
            await move(0, 0)

            print("Teclas de seta: mover o robô")
            print("SPACE: parar o robô")
            print("ESC: sair do jogo")

            # ==========================
            # 4. 游戏主循环
            # ==========================

            while running:

                # ==========================
                # 4.1 处理键盘事件
                # ==========================

                for event in pygame.event.get():

                    # 点击窗口关闭按钮
                    if event.type == pygame.QUIT:
                        running = False

                    # 按 ESC 退出游戏
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            print("A sair do jogo...")
                            running = False

                if not running:
                    break

                # 获取当前按键状态
                keys = pygame.key.get_pressed()

                # 窗口失去焦点时停止机器人
                if not pygame.key.get_focused():
                    command = (0, 0)

                # 空格键停止
                elif keys[pygame.K_SPACE]:
                    command = (0, 0)

                # 向前移动
                elif keys[pygame.K_UP]:
                    command = (SPEED, SPEED)

                # 向后移动
                elif keys[pygame.K_DOWN]:
                    command = (-SPEED, -SPEED)

                # 向左转
                elif keys[pygame.K_LEFT]:
                    command = (-TURN_SPEED, TURN_SPEED)

                # 向右转
                elif keys[pygame.K_RIGHT]:
                    command = (TURN_SPEED, -TURN_SPEED)

                # 没有按键时停止
                else:
                    command = (0, 0)

                # ==========================
                # 4.2 检测前方障碍物
                # ==========================

                # 等待传感器变量可用
                await node.wait_for_variables({
                    "prox.horizontal"
                })

                # 读取水平红外传感器数据
                prox = node.v.prox.horizontal

                # 读取前方五个传感器
                front_values = list(prox[:5])

                # 获取最大的接近度数值
                max_proximity = max(front_values)

                # 判断是否检测到障碍物
                obstacle_detected = (
                    max_proximity > OBSTACLE_THRESHOLD
                )

                # 前方有障碍物时禁止继续前进
                if (
                    command == (SPEED, SPEED)
                    and obstacle_detected
                ):
                    command = (0, 0)

                # 仅在电机指令变化时发送
                if command != last_command:
                    await move(*command)
                    last_command = command

                # ==========================
                # 4.3 读取摄像头画面
                # ==========================

                ret, frame = cap.read()

                if ret:

                    # 调整画面尺寸
                    frame = cv2.resize(
                        frame,
                        (WINDOW_WIDTH, WINDOW_HEIGHT)
                    )

                    # 将 OpenCV 的 BGR 转换为 RGB
                    frame = cv2.cvtColor(
                        frame,
                        cv2.COLOR_BGR2RGB
                    )

                    # 调整数组维度以适配 Pygame
                    frame = np.transpose(
                        frame,
                        (1, 0, 2)
                    )

                    # 将图像转换为 Pygame Surface
                    surface = pygame.surfarray.make_surface(
                        frame
                    )

                    # 显示摄像头画面
                    screen.blit(surface, (0, 0))

                else:
                    # 摄像头读取失败时显示黑色背景
                    screen.fill((0, 0, 0))

                # ==========================
                # 4.4 显示游戏控制信息
                # ==========================

                # 创建顶部半透明背景
                overlay = pygame.Surface(
                    (WINDOW_WIDTH, 45),
                    pygame.SRCALPHA
                )

                overlay.fill((0, 0, 0, 170))

                screen.blit(overlay, (0, 0))

                # 显示键盘操作提示
                info = font.render(
                    "Arrows: Move | SPACE: Stop | ESC: Quit",
                    True,
                    (255, 255, 255)
                )

                screen.blit(info, (15, 10))

                # ==========================
                # 4.5 显示传感器数值
                # ==========================

                sensor_text = font.render(
                    f"Front proximity: {max_proximity}",
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
                            85
                        )
                    )

                    screen.blit(
                        warning,
                        warning_rect
                    )

                # 更新游戏窗口
                pygame.display.flip()

                # ==========================
                # 4.7 维持机器人通信
                # ==========================

                await client.sleep(0.02)

                # 限制游戏画面刷新率
                clock.tick(30)

        finally:

            # ==========================
            # 5. 退出程序并释放资源
            # ==========================

            print("A parar o robô...")

            try:
                # 退出前停止左右电机
                await move(0, 0)

            finally:

                # 释放摄像头
                if cap is not None:
                    cap.release()

                # 关闭游戏窗口
                if pygame_started:
                    pygame.quit()

                # 解除机器人锁定
                await node.unlock()

            print("Programa terminado.")


ClientAsync.aw(main())
