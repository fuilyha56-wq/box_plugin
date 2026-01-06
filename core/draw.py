import io
import random
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import emoji

class CardMaker:
    """开盒卡片生成器"""
    
    def __init__(self, resource_dir: Path):
        self.RESOURCE_DIR = resource_dir
        self.FONT_PATH = self.RESOURCE_DIR / "可爱字体.ttf"
        self.EMOJI_FONT_PATH = self.RESOURCE_DIR / "NotoColorEmoji.ttf"
        
        self.FONT_SIZE = 35
        self.TEXT_PADDING = 10
        self.AVATAR_SIZE = None  # None = 与文本高度一致
        self.BORDER_THICKNESS = 10
        self.BORDER_COLOR_RANGE = (64, 255)
        self.CORNER_RADIUS = 30
        
        # 加载字体
        try:
            self.cute_font = ImageFont.truetype(str(self.FONT_PATH), self.FONT_SIZE)
        except Exception as e:
            print(f"加载可爱字体失败: {e}")
            # 使用默认字体
            self.cute_font = ImageFont.load_default()
            
        try:
            self.emoji_font = ImageFont.truetype(str(self.EMOJI_FONT_PATH), self.FONT_SIZE)
        except Exception as e:
            print(f"加载Emoji字体失败: {e}")
            # 使用默认字体
            self.emoji_font = ImageFont.load_default()

    def create(self, avatar: bytes, reply: list) -> bytes:
        """创建开盒卡片"""
        reply_str = "\n".join(reply)

        # 计算文本尺寸（去 emoji 占位）
        temp_img = Image.new("RGBA", (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        
        # 处理emoji占位
        no_emoji_reply = "".join("一" if emoji.is_emoji(c) else c for c in reply_str)
        bbox = temp_draw.textbbox((0, 0), no_emoji_reply, font=self.cute_font)
        text_width = int(bbox[2] - bbox[0])
        text_height = int(bbox[3] - bbox[1])

        img_height = text_height + self.TEXT_PADDING * 2

        # 处理头像
        try:
            avatar_img = Image.open(BytesIO(avatar)).convert("RGBA")
            avatar_size = self.AVATAR_SIZE or text_height
            avatar_img = avatar_img.resize((avatar_size, avatar_size))
        except Exception as e:
            # 如果头像处理失败，使用默认白色图像
            print(f"处理头像失败: {e}")
            avatar_size = self.AVATAR_SIZE or text_height
            avatar_img = Image.new("RGBA", (avatar_size, avatar_size), (255, 255, 255, 255))

        img_width = avatar_img.width + text_width + self.TEXT_PADDING * 2

        # 主图
        img = Image.new("RGBA", (img_width, img_height), (255, 255, 255, 255))

        # 圆角头像
        mask = Image.new("L", (avatar_size, avatar_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle(
            [(0, 0), (avatar_size, avatar_size)],
            self.CORNER_RADIUS,
            fill=255,
        )
        avatar_img.putalpha(mask)
        img.paste(avatar_img, (0, (img_height - avatar_size) // 2), mask)

        # 文本
        self._draw_multi(
            img,
            reply_str,
            avatar_img.width + self.TEXT_PADDING,
            self.TEXT_PADDING,
        )

        # 边框
        border_color = tuple(random.randint(*self.BORDER_COLOR_RANGE) for _ in range(3))
        border_img = Image.new(
            "RGBA",
            (
                img_width + self.BORDER_THICKNESS * 2,
                img_height + self.BORDER_THICKNESS * 2,
            ),
            border_color,
        )
        border_img.paste(img, (self.BORDER_THICKNESS, self.BORDER_THICKNESS))

        out = io.BytesIO()
        border_img.save(out, format="PNG")
        return out.getvalue()

    def _draw_multi(self, img, text, text_x=10, text_y=10):
        """绘制多行文本"""
        lines = text.split("\n")
        draw = ImageDraw.Draw(img)
        current_y = text_y

        for line in lines:
            line_color = (
                random.randint(0, 128),
                random.randint(0, 128),
                random.randint(0, 128),
                random.randint(240, 255),
            )
            current_x = text_x

            for char in line:
                if char in emoji.EMOJI_DATA:
                    draw.text(
                        (current_x, current_y + 10),
                        char,
                        font=self.emoji_font,
                        fill=line_color,
                    )
                    bbox = self.emoji_font.getbbox(char)
                else:
                    draw.text(
                        (current_x, current_y),
                        char,
                        font=self.cute_font,
                        fill=line_color,
                    )
                    bbox = self.cute_font.getbbox(char)

                current_x += bbox[2] - bbox[0]

            current_y += 40