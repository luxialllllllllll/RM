import pygame

from time import monotonic
from tdmclient import ClientAsync

from robot import Robot
from camara import Camera
from fog_map import FogMap
from ui import GameUI


# ==========================
# 参数配置
# ==========================

# 停车后等待机器人稳定的时间
STOP_TIME = 0.3

# 二维码扫描超时时间
SCAN_TIMEOUT = 3.0

# 两次二维码识别之间的时间
SCAN_INTERVAL = 0.2

# 机器人转弯时间，需要实际测试
TURN_TIME = 0.8

# 转弯后等待稳定的时间
TURN_STOP_TIME = 0.2

# 主循环间隔
LOOP_INTERVAL = 0.05

# 最大连续转弯尝试次数
MAX_TURN_ATTEMPTS = 4


# ==========================
# 游戏主程序
# ==========================

async def main():

     with ClientAsync() as client:

        print("A procurar o Thymio...")

        # 获取机器人节点
        node = await client.wait_for_node()

        # 等待机器人进入可控制状态
        print("A aguardar pelo Thymio...")

        start_time = monotonic()

        while node.status != client.NODE_STATUS_AVAILABLE:

            # 超过10秒则停止等待
            if monotonic() - start_time >= 10:

                raise RuntimeError(
                    f"Thymio indisponível. Estado: {node.status}"
                )

            await client.sleep(0.1)

        # 获取机器人控制权限
        await node.lock()

        print("Thymio conectado com sucesso.")

        robot = Robot(node)

        camera = None
        ui = None

        try:

            # 初始化机器人
            await robot.stop()
            await robot.init_sensors()

            # 初始化摄像头
            camera = Camera()

            # 初始化迷雾地图
            fog_map = FogMap()

            # 初始化游戏界面
            ui = GameUI()

            # 游戏状态
            state = "MOVING"

            # 状态开始时间
            state_time = monotonic()

            # 最近一次扫码时间
            last_scan_time = 0

            # 钥匙状态
            has_key = False

            # 连续转弯次数
            turn_attempts = 0

            # 当前转弯方向
            direction = None

            # 是否继续运行
            running = True

            # 状态对应的葡萄牙语显示文字
            state_labels = {
                "MOVING": "A explorar",
                "STOPPING": "A parar",
                "SCANNING": "A ler código QR",
                "TURNING": "A virar",
                "CHECKING": "A verificar",
                "PUZZLE": "Puzzle encontrado",
                "FINISHED": "Missão concluída",
                "BLOCKED": "Caminho bloqueado",
                "ERROR": "Erro"
            }

            print("Exploração automática iniciada.")

            # ==========================
            # 开始游戏循环
            # ==========================

            while running:

                # 处理窗口关闭和 ESC
                if not ui.handle_events():

                    await robot.stop()
                    break

                # 持续获取摄像头画面
                frame = camera.read()

                now = monotonic()

                # 摄像头断开时停止机器人
                if frame is None:

                    await robot.stop()

                    state = "ERROR"

                    print("Erro: ligação à câmara perdida.")

                # ==========================
                # 状态一：自动前进
                # ==========================

                if state == "MOVING":

                    if robot.has_obstacle():

                        await robot.stop()

                        state = "STOPPING"
                        state_time = monotonic()

                        print("Obstáculo detetado.")

                    else:

                        await robot.forward()

                        turn_attempts = 0

                # ==========================
                # 状态二：停车并等待稳定
                # ==========================

                elif state == "STOPPING":

                    await robot.stop()

                    if now - state_time >= STOP_TIME:

                        state = "SCANNING"

                        state_time = monotonic()

                        last_scan_time = 0

                        print("A procurar código QR...")

                # ==========================
                # 状态三：扫描二维码
                # ==========================

                elif state == "SCANNING":

                    await robot.stop()

                    qr_data = None

                    # 控制扫码频率
                    if now - last_scan_time >= SCAN_INTERVAL:

                        qr_data = camera.scan_qr(frame)

                        last_scan_time = monotonic()

                    # 成功识别二维码
                    if qr_data is not None:

                        # 记录二维码
                        fog_map.process_qr(qr_data)

                        # 检测谜题区域
                        if qr_data == "QR13" and not has_key:

                            print("Puzzle encontrado.")

                            state = "PUZZLE"

                        # 检测出口区域
                        elif qr_data == "QR15" and has_key:

                            await robot.stop()

                            state = "FINISHED"

                            print("Missão concluída!")

                        else:

                            if qr_data == "QR15":

                                print(
                                    "É necessário encontrar a chave."
                                )

                            state = "TURNING"

                            direction = robot.choose_direction()

                            state_time = monotonic()

                    # 扫描超时
                    elif now - state_time >= SCAN_TIMEOUT:

                        print("Nenhum código QR encontrado.")

                        state = "TURNING"

                        direction = robot.choose_direction()

                        state_time = monotonic()

                # ==========================
                # 状态四：机器人转弯
                # ==========================

                elif state == "TURNING":

                    if now - state_time < TURN_TIME:

                        if direction == "LEFT":

                            await robot.turn_left()

                        else:

                            await robot.turn_right()

                    else:

                        await robot.stop()

                        turn_attempts += 1

                        state = "CHECKING"

                        state_time = monotonic()

                # ==========================
                # 状态五：检查转弯后的方向
                # ==========================

                elif state == "CHECKING":

                    await robot.stop()

                    if now - state_time >= TURN_STOP_TIME:

                        if robot.has_obstacle():

                            # 防止机器人无限原地转弯
                            if turn_attempts >= MAX_TURN_ATTEMPTS:

                                state = "BLOCKED"

                                print("Caminho bloqueado.")

                            else:

                                # 继续向同一个方向转弯
                                state = "TURNING"

                                state_time = monotonic()

                        else:

                            state = "MOVING"

                            state_time = monotonic()

                            print("A continuar a exploração.")

                # ==========================
                # 状态六：谜题区域
                # ==========================

                elif state == "PUZZLE":

                    await robot.stop()

                    # 后续添加推动箱子和获取钥匙逻辑

                # ==========================
                # 状态七：游戏结束
                # ==========================

                elif state == "FINISHED":

                    await robot.stop()

                # ==========================
                # 状态八：道路阻塞或异常
                # ==========================

                elif state in ("BLOCKED", "ERROR"):

                    await robot.stop()

                # ==========================
                # 更新游戏界面
                # ==========================

                ui.render(
                    frame,
                    fog_map,
                    state=state_labels.get(state, state),
                    has_key=has_key
                )

                # 保持机器人异步通信
                await client.sleep(LOOP_INTERVAL)

        except Exception as error:

            print(f"Erro durante a execução: {error}")

            raise

        finally:

            # 无论正常退出还是发生异常
            # 都尝试停止机器人并释放资源
            try:

                await robot.stop()

            finally:

                try:

                    await node.unlock()

                finally:

                    if camera is not None:

                        camera.close()

                    if ui is not None:

                        ui.close()

            print("Programa terminado.")


# ==========================
# 启动程序
# ==========================

if __name__ == "__main__":

    ClientAsync.aw(main())