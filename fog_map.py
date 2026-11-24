from maze import MAZE, START, QR_POSITIONS
from maze import is_walkable


class FogMap:

    def __init__(self):

        # 已探索的地图格子
        self.explored = set()

        # 已扫描的二维码
        self.scanned_qrs = set()

        # 二维码扫描历史
        self.qr_history = []

        # 机器人当前位置
        self.robot_position = START

        # 最近识别的二维码
        self.last_qr = "START"

        # 解锁初始区域
        self.reveal_area(3, 29, 5, 31)

    # 解锁指定区域
    def reveal_area(self, x1, y1, x2, y2):

        for y in range(min(y1, y2), max(y1, y2) + 1):

            for x in range(min(x1, x2), max(x1, x2) + 1):

                if is_walkable(x, y):

                    self.explored.add((x, y))

    # 解锁经过的路线
    def reveal_path(self, path):

        for x, y in path:

            if is_walkable(x, y):

                self.explored.add((x, y))

    # 处理识别到的二维码
    def process_qr(self, qr_id, robot_position=None, path=None):

        # 检查二维码是否有效
        if qr_id not in QR_POSITIONS:

            print("Código QR inválido.")

            return False

        # 避免连续重复记录同一个二维码
        if qr_id == self.last_qr:

            return False

        # 解锁经过的路线
        if path is not None:

            self.reveal_path(path)

        # 更新机器人实际位置
        if robot_position is not None:

            self.update_position(*robot_position)

        # 保存二维码记录
        self.scanned_qrs.add(qr_id)

        self.qr_history.append(qr_id)

        self.last_qr = qr_id

        print(f"Código QR registado: {qr_id}")

        print(f"Posição do QR: {QR_POSITIONS[qr_id]}")

        print(f"Exploração: {self.get_progress():.1f}%")

        return True

    # 判断格子是否已经探索
    def is_explored(self, x, y):

        return (x, y) in self.explored

    # 判断二维码是否已经扫描
    def is_qr_scanned(self, qr_id):

        return qr_id in self.scanned_qrs

    # 更新机器人位置
    def update_position(self, x, y):

        if is_walkable(x, y):

            self.robot_position = (x, y)

            self.explored.add((x, y))

    # 计算地图探索进度
    def get_progress(self):

        total = sum(row.count("1") for row in MAZE)

        if total == 0:

            return 0

        return len(self.explored) / total * 100

    # 获取二维码扫描历史
    def get_qr_history(self):

        return self.qr_history.copy()

    # 重置地图
    def reset(self):

        self.explored.clear()

        self.scanned_qrs.clear()

        self.qr_history.clear()

        self.robot_position = START

        self.last_qr = "START"

        self.reveal_area(3, 29, 5, 31)

        print("Mapa reiniciado.")