from nonebot import on_command
from nonebot.matcher import Matcher
from nonebot.params import Arg, CommandArg, ArgPlainText
from nonebot.adapters.onebot.v11 import MessageEvent, MessageSegment, Message

from .database import UserBox
from PIL import Image, ImageDraw
from src.utils import loadImage, saveImage ,SarasaFont
from .config import max_favor
checkin = on_command("签到", priority=5)


@checkin.handle()
async def _(event: MessageEvent):
    user, tickets = await UserBox.checkin(event.user_id)
    if tickets is None:
        await checkin.finish("今日已签过到")
    img = await Draw(user.ten_gacha_tickets-tickets, tickets, user.favor)
    msg = Message([
        MessageSegment.image(saveImage(img)),
        MessageSegment.at(event.user_id)
    ])
    await checkin.finish(msg)


async def Draw(origin_tickets: int, gain_tickets: int, favor: int) -> Image.Image:
    template = await loadImage("resource/arknight_gacha/checkin/template.png")
    draw = ImageDraw.Draw(template)
    text=f"寻访凭证:{origin_tickets}"
    draw.text(xy=(20, 650),
              text=text,
              font=SarasaFont,
              fill=(0, 0, 0, 255)
              )
    w, h = SarasaFont.getsize(text)
    draw.text(xy=(20+w, 650),
              text=f"+{gain_tickets}",
              font=SarasaFont,
              fill=(0, 255, 0, 255)
              )
    draw.text(xy=(20, 650+h),
              text=f"好感度:{favor/max_favor:.2%}",
              font=SarasaFont,
              fill=(0, 0, 0, 255)
              )
    return template
