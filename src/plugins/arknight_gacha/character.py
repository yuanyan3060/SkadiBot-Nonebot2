from dataclasses import dataclass
import json
from typing import Any, Dict, List, Optional
import pathlib
from nonebot import get_driver, require, export
import aiofiles

base_path = pathlib.Path("resource/arknight_resources")
driver = get_driver()
Downloader = require("arknight_resources").Downloader

@dataclass
class Character:
    code: str
    name: str
    rarity: int
    profession: str


class CharaterTable:
    character_list: List[Character] = [] # 感觉这个规模没有必要上hash表优化查询
    path = base_path/"gamedata/excel/character_table.json"

    @classmethod
    async def load(cls):
        async with aiofiles.open(cls.path, "r", encoding="UTF-8") as fp:
            json_str = await fp.read()
        json_data: Dict[str, Dict[str, Any]] = json.loads(json_str)
        cls.character_list.clear()
        for code, data in json_data.items():
            if not code.startswith("char"):
                continue
            name: str = data["name"]
            rarity: int = data["rarity"]
            profession: str = data["profession"]
            itemObtainApproach: Optional[str] = data["itemObtainApproach"]
            if itemObtainApproach is not None:
                character = Character(code, name, rarity, profession)
                cls.character_list.append(character)

    @classmethod
    async def on_update(cls, update_file:Dict[str, str]):
        if "gamedata/excel/character_table.json" in update_file:
            await cls.load()

    @classmethod
    def find_code(cls, code: str) -> Optional[Character]:
        for character in cls.character_list:
            if character.code == code:
                return character
        return None

    @classmethod
    def find_name(cls, name: str) -> Optional[Character]:
        for character in cls.character_list:
            if character.name == name:
                return character
        return None


@driver.on_startup
async def init():
    await CharaterTable.load()

Downloader.register_observer(CharaterTable)