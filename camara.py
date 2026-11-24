import cv2

from maze import QR_POSITIONS

# 手机摄像头编号
CAMERA_ID = 0


class Camera:

    def __init__(self, camera_id=CAMERA_ID):

        # 连接手机摄像头
        self.cap = cv2.VideoCapture(
            camera_id,
            cv2.CAP_DSHOW
        )

        if not self.cap.isOpened():
            self.cap.release()
            raise RuntimeError(
                "Não foi possível abrir a câmera."
            )

        # 初始化二维码识别器
        self.detector = cv2.QRCodeDetector()

        print("Câmara conectada com sucesso.")

    # 获取实时画面
    def read(self):

        ret, frame = self.cap.read()

        if ret:
            return frame

        return None

    # 扫描二维码
    def scan_qr(self, frame):

        if frame is None:
            return None

        data, points, _ = self.detector.detectAndDecode(frame)

        data = data.strip()

        # 判断是否为地图中的二维码
        if data in QR_POSITIONS:

            print(f"Código QR detetado: {data}")
            print(f"Posição: {QR_POSITIONS[data]}")

            return data

        return None

    # 关闭摄像头
    def close(self):

        self.cap.release()

        print("Câmara desligada.")


# ==========================
# 独立测试摄像头和二维码
# ==========================

if __name__ == "__main__":

    camera = Camera()

    last_qr = None

    print("Pressione ESPAÇO para ler o código QR.")
    print("Pressione Q ou ESC para sair.")

    try:

        while True:

            frame = camera.read()

            if frame is None:
                print("Não foi possível obter a imagem.")
                break

            # 显示最近识别的二维码
            if last_qr is not None:

                cv2.putText(
                    frame,
                    f"QR: {last_qr}",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2
                )

            # 显示实时摄像头画面
            cv2.imshow("Thymio Camera", frame)

            key = cv2.waitKey(1) & 0xFF

            # 按 Q 或 ESC 退出
            if key == ord("q") or key == 27:
                break

            # 按空格测试二维码识别
            elif key == 32:

                qr_data = camera.scan_qr(frame)

                if qr_data is not None:

                    last_qr = qr_data

                else:

                    print("Nenhum código QR encontrado.")

    finally:

        camera.close()
        cv2.destroyAllWindows()