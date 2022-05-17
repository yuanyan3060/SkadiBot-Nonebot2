import asyncio
from nonebot import get_driver, export, require
import nonebot
from .database import Source, Version
import httpx
from typing import List, Protocol, Coroutine, Dict, Optional, Tuple
import aiofiles
import pathlib
import hashlib
from nonebot.log import logger
from . import database

scheduler = require("nonebot_plugin_apscheduler").scheduler
driver = get_driver()

class Md5UnmatchException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class Observer(Protocol):
    @classmethod
    async def on_update(cls, update_file:Dict[str, str]):
        pass


class Downloader:
    base_url = "https://vivien8261.gitee.io/arknights-bot-resource/{}"
    base_path = pathlib.Path("resource/arknight_resources")
    observers: List[Observer] = []

    @classmethod
    async def init(cls):
        await cls.update()

    @classmethod
    async def update(cls)->Tuple[bool, bool]:
        """
        更新明日方舟素材，返回（是否需要更新，是否更新成功）
        """
        async def save(sem:asyncio.Semaphore, name:str, md5:str):
            async with sem:
                done = await cls.download(name, md5)
                if done:
                    await Source.update_md5(name, md5) 
                    logger.debug("下载文件:{}", name)
                else:
                    logger.warning("下载文件失败:{}", name)
                return done
        version = await cls.get_version()
        if version==await Version.get_version():
            return False, True
        old_file_glob = await Source.get_all()
        new_file_glob = await cls.get_file_glob()
        sem = asyncio.Semaphore(10)
        tasks: List[Coroutine] = []
        update_file:Dict[str, str]={}
        for name, md5 in new_file_glob.items():
            if not cls.fliter(name):
                continue
            if md5!=old_file_glob.get(name, ""):
                tasks.append(save(sem, name, md5))
                update_file[name]=md5
        if len(tasks)>0:
            success = True
            done, pending = await asyncio.wait(tasks)
            if len(pending)==0:
                for i in done:
                    if not i.result():
                        success=False
                        break
            if success:
                await Version.update_version(version)
                await cls.notify_observers(update_file)
                return True, True
            else:
                return True, False
        return False, True

    @classmethod
    async def get_version(cls) -> str:
        """
        返回：游戏客户端资源版本
        """
        async with httpx.AsyncClient() as client:
            url = cls.base_url.format("version")
            rep = await client.get(url)
            return rep.text

    @classmethod
    async def get_file_glob(cls) -> Dict[str, str]:
        """
        返回：{文件相对路径:md5值}的字典
        """
        async with httpx.AsyncClient() as client:
            url = cls.base_url.format("file_dict.json")
            rep = await client.get(url, timeout=100)
            return rep.json()

    @classmethod
    def fliter(cls, path: str)->bool:
        if path.endswith(".txt"):
            return False
        if path.startswith("gamedata/excel"):
            return True
        if path.startswith("portrait") and path.endswith("_1.png"):
            return True
        return False
    @classmethod
    async def download(cls, path: str, md5:Optional[str]=None)->bool:
        """
        根据素材相对路径下载文件
        """
        for _ in range(5):
            try:
                async with httpx.AsyncClient() as client:
                    url = cls.base_url.format(path.replace("#", "%23"))
                    rep = await client.get(url)
                    file_path = cls.base_path/path
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    m = hashlib.md5()
                    if md5 is not None:
                        m.update(rep.content)
                    if md5!=m.hexdigest():
                        raise Md5UnmatchException
                    async with aiofiles.open(file_path, "wb") as fp:
                        await fp.write(rep.content)
                    return True
            except httpx.TimeoutException:
                pass
            except Md5UnmatchException:
                pass
            except Exception as e:
                logger.error("下载文件异常{}:{}", path, e)
                return False
        return False

    @classmethod
    def register_observer(cls, observer: Observer):
        cls.observers.append(observer)

    @classmethod
    def remove_observer(cls, observer: Observer):
        cls.observers.remove(observer)

    @classmethod
    async def notify_observers(cls, update_file:Dict[str, str]):
        tasks: List[Coroutine] = []
        for observer in cls.observers:
            tasks.append(observer.on_update(update_file))
        if len(tasks)>0:
            await asyncio.wait(tasks)


export().Downloader = Downloader
@scheduler.scheduled_job("cron", minute=20)
async def auto_update():
    await Downloader.update()
@driver.on_startup
async def _():
    await database.init()
    await Downloader.update()