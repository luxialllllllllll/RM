import qrcode
from pathlib import Path

from maze import QR_POSITIONS

# 二维码保存目录
OUTPUT_DIR = Path(__file__).parent / "qrcodes"

# 创建目录
OUTPUT_DIR.mkdir(exist_ok=True)

# 遍历所有二维码
for qr_id, position in QR_POSITIONS.items():

    # 创建二维码
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=20,
        border=4
    )

    # 二维码只保存编号
    qr.add_data(qr_id)

    qr.make(fit=True)

    # 生成二维码图片
    img = qr.make_image(
        fill_color="black",
        back_color="white"
    )

    # 保存图片
    img.save(OUTPUT_DIR / f"{qr_id}.png")

    print(f"{qr_id} criado com sucesso. Posição: {position}")

print("Todos os códigos QR foram criados.")