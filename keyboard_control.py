
import pygame
from tdmclient import ClientAsync

SPEED = 100
TURN_SPEED = 70

async def main():
    with ClientAsync() as client:
        node = await client.wait_for_node()
        await node.lock()

        pygame.init()
        screen = pygame.display.set_mode((500, 250))
        pygame.display.set_caption("Thymio Control")
        clock = pygame.time.Clock()

        async def move(left, right):
            await node.set_variables({
                "motor.left.target": [left],
                "motor.right.target": [right]
            })

        last_command = None
        running = True

        try:
            await move(0, 0)
            print("conectado ao Thymio! Use as setas do teclado para controlar o robô. Pressione ESPAÇO para parar.")

            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False

                keys = pygame.key.get_pressed()

                if keys[pygame.K_SPACE]:
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

                # 仅当方向改变时发送命令
                if command != last_command:
                    await move(*command)
                    last_command = command

                screen.fill((30, 30, 30))
                pygame.display.flip()

                # 保持 Python 异步通信正常运行
                await client.sleep(0.05)
                clock.tick(20)

        finally:
            await move(0, 0)
            await node.unlock()
            pygame.quit()

ClientAsync.aw(main())
