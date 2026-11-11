#pip install tdmclient opencv-python 


import cv2
import time
from datetime import datetime
from pathlib import Path
from tdmclient import ClientAsync

# 关键帧保存目录
output = Path("critical_frames")
output.mkdir(exist_ok=True)

# 手机摄像头
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    raise RuntimeError("Não foi possível abrir a câmera. Verifique se a câmera está conectada e se o driver está instalado corretamente.")

with ClientAsync() as client:

    async def main():
        node = await client.wait_for_node()

        # 读取 Thymio 的电机目标速度
        await node.wait_for_variables({
            "motor.left.target",
            "motor.right.target"
        })

        was_moving = False
        stop_since = None

        while True:
            ret, frame = cap.read()

            if not ret:
                break

            left = int(node.v.motor.left.target)
            right = int(node.v.motor.right.target)

            moving = abs(left) > 5 or abs(right) > 5

            if moving:
                was_moving = True
                stop_since = None

            elif was_moving:
                if stop_since is None:
                    stop_since = time.monotonic()

                # 停止持续 0.4 秒，避免截图模糊
                elif time.monotonic() - stop_since >= 0.4:

                    timestamp = datetime.now().strftime(
                        "%Y%m%d_%H%M%S_%f"
                    )

                    filename = output / f"frame_{timestamp}.jpg"

                    cv2.imwrite(str(filename), frame)
                    print("Critical frame saved:", filename)

                    # 防止重复截图
                    was_moving = False
                    stop_since = None

            cv2.imshow("Thymio Camera", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            await client.sleep(0.03)

    try:
        client.run_async_program(main)
    finally:
        cap.release()
        cv2.destroyAllWindows()
