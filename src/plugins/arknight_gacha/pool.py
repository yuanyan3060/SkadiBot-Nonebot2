from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, MessageSegment, Message
from functools import lru_cache
from .database import Pool
from src.utils import saveImage, text2image
pool = on_command("卡池", priority=5, block=True)


@pool.handle()
async def _(event: MessageEvent):
    pools = await Pool.get_pools()
    text = "\n".join(f'<color="#FF0000">[{n+1:0>2d}]</color>{pool.name}' for n, pool in enumerate(pools))
    img = draw_pool_img(text)
    msg = Message([MessageSegment.image(img)])
    await pool.finish(msg)

@lru_cache(maxsize=1)
def draw_pool_img(text:str):
    return saveImage(text2image(text, 820))