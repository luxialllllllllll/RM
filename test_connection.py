
from tdmclient import ClientAsync

async def main():
    with ClientAsync() as client:
        node = await client.wait_for_node()
        await node.lock()

        print("Thymio 连接成功！")

        try:
            # 前进
            print("电机启动")
            await node.set_variables({
                "motor.left.target": [80],
                "motor.right.target": [80]
            })

            await client.sleep(1)

            # 停止
            await node.set_variables({
                "motor.left.target": [0],
                "motor.right.target": [0]
            })

            print("测试完成！")

        finally:
            await node.set_variables({
                "motor.left.target": [0],
                "motor.right.target": [0]
            })
            await node.unlock()

ClientAsync.aw(main())
