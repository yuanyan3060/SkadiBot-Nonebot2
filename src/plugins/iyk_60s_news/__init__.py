import httpx
from nonebot import on_command, get_driver, require, get_bot
from nonebot.matcher import Matcher
from nonebot.params import Arg, CommandArg, ArgPlainText
from nonebot.adapters.onebot.v11 import Bot
from nonebot.adapters.onebot.v11 import MessageEvent, MessageSegment, Message
import asyncio
from nonebot.adapters.onebot.v11.exception import ActionFailed
from nonebot.log import logger
scheduler = require("nonebot_plugin_apscheduler").scheduler

async def get_news()->bytes:
    url = "http://api.iyk0.com/60s/"
    async with httpx.AsyncClient() as client:
        rep = await client.get(url)
        image_url = rep.json()["imageUrl"]
        async with httpx.AsyncClient() as client:
            rep = await client.get(image_url)
            return rep.content

@scheduler.scheduled_job("cron", hour=6, minute=30)
async def _():
    news = await get_news()
    msg = Message([MessageSegment.image(news)])
    bot:Bot = get_bot()  # type: ignore
    for group in await bot.get_group_list():
        group_id:int = group["group_id"]
        try:
            await bot.send_group_msg(group_id=group_id, message=msg)
            await asyncio.sleep(1)
        except ActionFailed:
            logger.error(f"{group_id} 群被禁言中，无法发送每日新闻")