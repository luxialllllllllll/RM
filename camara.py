#pip install opencv-python
# 下载 https://iriun.com/?utm_source=chatgpt.com

# 查看摄像头是否连接到电脑，python camara.py

import cv2

# 0 是摄像头编号，可尝试 1、2、3
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
if not cap.isOpened():
    raise RuntimeError("无法打开摄像头")

while True:
    ret, frame = cap.read()

    if not ret:
        break

    cv2.imshow("Thymio Camera", frame)

    # 按 Q 退出
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()


