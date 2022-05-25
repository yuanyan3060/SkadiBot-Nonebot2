from time import pthread_getcpuclockid
import httpx
from tortoise import Tortoise
from nonebot import get_driver, require
from .models import PoolModel, UserBoxModel, OperatorModel
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from .config import checkin_tickets, checkin_favor, max_favor
from lxml import etree
driver = get_driver()
Downloader = require("arknight_resources").Downloader
scheduler = require("nonebot_plugin_apscheduler").scheduler
from nonebot_plugin_apscheduler import scheduler
@driver.on_startup
async def init():
    from . import models
    await Tortoise.init(
        db_url="sqlite://database/{0}/{0}.db".format("arknight_gacha"),
        modules={"models": [locals()["models"]]},
    )
    await Tortoise.generate_schemas()
    await Pool.spider_pool()
    scheduler.add_job(Pool.spider_pool, "cron", minute=20)
    Downloader.register_observer(Pool)
driver.on_shutdown(Tortoise.close_connections)


class UserBox:

    @classmethod
    async def get_user(cls, qq: int) -> UserBoxModel:
        user, _ = await UserBoxModel.get_or_create(
            defaults={
                "ten_gacha_tickets": 30,
                "last_checkin_time": datetime.fromtimestamp(0.0),
                "favor": 0,
                "no6_times": 0
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
        return await PoolModel.get_or_none(id=pool_id)

    @classmethod
    async def get_pools(cls) -> List[PoolModel]:
        return await PoolModel.all()

    @classmethod
    async def spider_pool(cls):
        print("开始爬取")
        url = "https://prts.wiki/w/%E5%8D%A1%E6%B1%A0%E4%B8%80%E8%A7%88/%E9%99%90%E6%97%B6%E5%AF%BB%E8%AE%BF"
        pools:List[PoolModel] = []
        async with httpx.AsyncClient() as client:
            rep = await client.get(url)
            html: etree._Element = etree.HTML(rep.text, parser=None)
            index = 0
            for tr in html.xpath("//table/tbody/tr"):
                td_list = tr.xpath("./td")
                if len(td_list)!=4:
                    continue
                index+=1
                name:str = td_list[0].xpath(".//text()")[0]
                if name.endswith("复刻") or name.endswith("返场") or name.startswith("【跨年欢庆寻访】"):
                    continue
                pickup_6 = []
                pickup_5 = []
                pickup_4 = []
                for up in td_list[2:]:
                    for a in up.xpath(".//a"):
                        up_name = a.xpath("./@title")[0]
                        up_rarity = int(a.xpath(".//img[@id='levlicon']/@data-src")[0][-5:-4])
                        if up_rarity==5:
                            pickup_6.append(up_name)
                        elif up_rarity==4:
                            pickup_5.append(up_name)
                        elif up_rarity==3:
                            pickup_4.append(up_name)
                pool = PoolModel(
                    id=index,
                    name=name,
                    pickup_4=pickup_4,
                    pickup_5=pickup_5,
                    pickup_6=pickup_6
                )
                pools.append(pool)
            if len(pools)>10:
                await PoolModel.all().delete()
                await PoolModel.bulk_create(pools)

    @classmethod
    async def on_update(cls, update_file: Dict[str, str]):
        if "gamedata/excel/gacha_table.json" in update_file:
            await cls.spider_pool()


