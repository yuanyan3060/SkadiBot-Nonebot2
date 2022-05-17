from tortoise.models import Model
from tortoise import fields
from tortoise import Tortoise, run_async
from nonebot import get_driver
from .models import SourceModel, VersionModel
from typing import Dict, List, Optional
from datetime import datetime, time
driver = get_driver()


async def init():
    from . import models
    await Tortoise.init(
        db_url="sqlite://database/{0}/{0}.db".format("arknight_resources"),
        modules={"models": [locals()["models"]]},
    )
    await Tortoise.generate_schemas()
driver.on_shutdown(Tortoise.close_connections)


class Source:
    @classmethod
    async def update_md5(cls, name: str, md5: str):
        await SourceModel.update_or_create({"md5": md5}, name=name)

    @classmethod
    async def get_md5(cls, name: str) -> Optional[str]:
        source = await SourceModel.get_or_none(name=name)
        if source is None:
            return None
        return source.md5

    @classmethod
    async def get_all(cls) -> Dict[str, str]:
        result = await SourceModel.all()
        return {i.name: i.md5 for i in result}


class Version:
    @classmethod
    async def update_version(cls, version: str):
        data = await VersionModel.first()
        if data is None:
            await VersionModel.update_or_create(version=version, update_time=datetime.now())
            return
        if data is None or version != data.version:
            await data.update_or_create(version=version, update_time=datetime.now())
            return

    @classmethod
    async def get_version(cls) -> Optional[str]:
        data = await VersionModel.first()
        if data is None:
            return None
        else:
            return data.version

    @classmethod
    async def get_update_time(cls) -> Optional[datetime]:
        data = await VersionModel.first()
        if data is None:
            return None
        else:
            return data.update_time
