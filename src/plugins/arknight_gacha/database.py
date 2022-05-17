from genericpath import exists
import httpx
from tortoise.models import Model
from tortoise import fields
from tortoise import Tortoise, run_async
from nonebot import get_driver, require, export
from .models import PoolModel, UserBoxModel, OperatorModel
from typing import Dict, List, Optional, Tuple
from datetime import datetime, time, timedelta
from .config import checkin_tickets, checkin_favor, max_favor
from dataclasses import dataclass
from lxml import etree
driver = get_driver()
Downloader = require("arknight_resources").Downloader


@driver.on_startup
async def init():
    from . import models
    await Tortoise.init(
        db_url="sqlite://database/{0}/{0}.db".format("arknight_gacha"),
        modules={"models": [locals()["models"]]},
    )
    await Tortoise.generate_schemas()
    await Pool.spider_pool()
driver.on_shutdown(Tortoise.close_connections)


class UserBox:

    @classmethod
    async def get_user(cls, qq: int) -> UserBoxModel:
        user, _ = await UserBoxModel.get_or_create(
            defaults={
                "ten_gacha_tickets": 30,
                "last_checkin_time": datetime.fromtimestamp(0.0),
                "favor": 0,
                "pool_name": "搅动潮汐之剑复刻（斯卡蒂UP）"
            },
            qq=qq
        )
        return user

    @classmethod
    async def append_operators(cls, qq: int, codes: List[str]):
        for code in codes:
            operator, is_create = await OperatorModel.get_or_create(
                defaults={
                    "nums": 1,
                    "gain_time": datetime.now(),
                },
                user_id=qq,
                code=code
            )
            if is_create:
                continue
            operator.update_from_dict({"nums": operator.nums+1})
            await operator.save()

    @classmethod
    async def get_operators(cls, qq: int) -> List[OperatorModel]:
        return await OperatorModel.filter(user_id=qq).all()

    @classmethod
    async def checkin(cls, qq: int) -> Tuple[UserBoxModel, Optional[int]]:
        user = await cls.get_user(qq)
        now = datetime.now()
        offset = timedelta(hours=4)
        if (user.last_checkin_time-offset).date() == (now-offset).date():
            return user, None
        await user.update_from_dict({
            "ten_gacha_tickets": user.ten_gacha_tickets+checkin_tickets,
            "last_checkin_time": now,
            "favor": min(max_favor, user.favor+checkin_favor)
        })
        await user.save()
        return user, checkin_tickets

    @classmethod
    async def give_tickets(cls, qq: int, nums: int):
        user = await cls.get_user(qq)
        user.update_from_dict({
            "ten_gacha_tickets": user.ten_gacha_tickets+nums,
        })
        await user.save()

    @classmethod
    async def set_pool(cls, qq: int, pool: str):
        user = await cls.get_user(qq)
        user.update_from_dict({
            "pool_name": pool,
        })
        await user.save()


class Pool:
    @classmethod
    async def get_pool(cls, pool_id: int) -> Optional[PoolModel]:
        return await PoolModel.get_or_none(index=pool_id)

    @classmethod
    async def get_pools(cls) -> List[PoolModel]:
        return await PoolModel.all()

    @classmethod
    async def spider_pool(cls):
        url = "https://wiki.biligame.com/arknights/%E5%B9%B2%E5%91%98%E5%AF%BB%E8%AE%BF%E6%A8%A1%E6%8B%9F%E5%99%A8"
        async with httpx.AsyncClient() as client:
            rep = await client.get(url)
            html: etree._Element = etree.HTML(rep.text, parser=None)
            gyxf_up_list = html.xpath('//*[@class="gyxf_up_list"]')
            if len(gyxf_up_list) > 0:
                await PoolModel.filter().delete()
            for i in gyxf_up_list:
                title = i.xpath("./@data-title")
                if len(title) > 0:
                    title = title[0]
                pickup_4 = i.xpath(
                    './/*[text()="★★★★"]/..//*[@class="gy_upface"]//text()')
                pickup_5 = i.xpath(
                    './/*[text()="★★★★★"]/..//*[@class="gy_upface"]//text()')
                pickup_6 = i.xpath(
                    './/*[text()="★★★★★★"]/..//*[@class="gy_upface"]//text()')
                pool = PoolModel(
                    name=title,
                    pickup_4=pickup_4,
                    pickup_5=pickup_5,
                    pickup_6=pickup_6
                )
                await pool.save()

    @classmethod
    async def on_update(cls, update_file: Dict[str, str]):
        if "gamedata/excel/gacha_table.json" in update_file:
            await cls.spider_pool()
Downloader.register_observer(Pool)