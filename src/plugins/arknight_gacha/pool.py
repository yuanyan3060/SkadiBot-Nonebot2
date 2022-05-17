from nonebot import on_command
from nonebot.matcher import Matcher
from nonebot.params import Arg, CommandArg, ArgPlainText
from nonebot.adapters.onebot.v11 import MessageEvent, MessageSegment, Message

from .database import UserBox, Pool
from PIL import Image, ImageDraw
from src.utils import loadImage, saveImage ,SarasaFont
from .config import max_favor
pool = on_command("卡池", priority=5, block=True)


@pool.handle()
async def _(event: MessageEvent):
    #todo
    pass