SPEED = 100
TURN_SPEED = 70

# 障碍物检测阈值
OBSTACLE_THRESHOLD = 3000


class Robot:

    def __init__(self, node):

        self.node = node
        self.last_command = None

    # ==========================
    # 初始化传感器
    # ==========================

    async def init_sensors(self):

        await self.node.wait_for_variables({
            "prox.horizontal"
        })

        print("Sensores inicializados.")

    # ==========================
    # 控制左右电机
    # ==========================

    async def move(self, left, right):

        command = (left, right)

        # 避免重复发送相同的电机指令
        if command != self.last_command:

            await self.node.set_variables({
                "motor.left.target": [left],
                "motor.right.target": [right]
            })

            self.last_command = command

    # 前进
    async def forward(self):

        await self.move(SPEED, SPEED)

    # 后退
    async def backward(self):

        await self.move(-SPEED, -SPEED)

    # 停止
    async def stop(self):

        await self.move(0, 0)

    # 左转
    async def turn_left(self):

        await self.move(-TURN_SPEED, TURN_SPEED)

    # 右转
    async def turn_right(self):

        await self.move(TURN_SPEED, -TURN_SPEED)

    # ==========================
    # 获取红外传感器数据
    # ==========================

    def get_proximity(self):

        return list(self.node.v.prox.horizontal)

    # ==========================
    # 判断前方是否存在障碍物
    # ==========================

    def has_obstacle(self):

        prox = self.get_proximity()

        return max(prox[:5]) >= OBSTACLE_THRESHOLD

    # ==========================
    # 判断左右方向
    # ==========================

    def choose_direction(self):

        prox = self.get_proximity()

        left = prox[0] + prox[1]
        right = prox[3] + prox[4]

        # 数值越小，通常表示障碍物越远
        if left < right:

            return "LEFT"

        return "RIGHT"