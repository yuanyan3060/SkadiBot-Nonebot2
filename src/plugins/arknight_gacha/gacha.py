import pathlib
from typing import List, Optional, Tuple
from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, MessageSegment, Message
from .database import UserBox, Pool, PoolModel
from .character import Character, CharaterTable
from PIL import Image
from src.utils import loadImage, saveImage
import random
from nonebot.params import Depends
gacha = on_command("十连", priority=5, block=True)

async def get_pool_index(event: MessageEvent)->str:
    s = str(event.get_message())
    return s[s.rfind(" "):]

@gacha.handle()
async def _(event: MessageEvent, index:str=Depends(get_pool_index)):
    try:
        print(index)
        int_index = int(index)
    except:
        await gacha.finish("示例:蒂蒂十连 5\n数字为卡池编号\n蒂蒂卡池 可查询所有卡池")
    pool = await Pool.get_pool(int_index)
    if pool is None:
        await gacha.finish(f"卡池编号{int_index}不存在")
    user = await UserBox.get_user(event.user_id)
    if user.ten_gacha_tickets<0:
        await gacha.finish("寻访凭证不足")
    chars, n6_times = roll_char_ten(pool, user.no6_times)
    user.update_from_dict({"n6_times":n6_times, "ten_gacha_tickets":user.ten_gacha_tickets-1})
    await user.save()
    await UserBox.append_operators(event.user_id, [char.code for char in chars])
    img = await gacha_img_build(chars)
    msg = Message([MessageSegment.image(saveImage(img))])
    await gacha.finish(msg)

def roll_char_ten(pool:PoolModel, no6_times:int)->Tuple[List[Character], int]:
    result = []
    for i in range(10):
        char = roll_char(pool, no6_times)
        if char is None:
            raise Exception("未找到干员")
        if char.rarity==5:
            no6_times=0
        else:
            no6_times+=1
        result.append(char)
    return result, no6_times
    
def roll_char(pool:PoolModel, no6_times:int)->Optional[Character]:
    pickup_6_pr = max(0.02, 0.02*(no6_times-49))
    pickup_5_pr = 0.08*(0.98/(1-pickup_6_pr))
    pickup_4_pr = 0.50*(0.98/(1-pickup_6_pr))
    pickup_3_pr = 0.40*(0.98/(1-pickup_6_pr))
    up_pr = 0.5
    up_char_names = []
    rarity_rand = random.random()
    if rarity_rand<=pickup_6_pr:
        rarity = 5
        up_char_names = pool.pickup_6
        if len(up_char_names)==2:
            up_pr = 0.70
    elif rarity_rand<=pickup_5_pr:
        rarity = 4
        up_char_names = pool.pickup_5
    elif rarity_rand<=pickup_4_pr:
        rarity = 3
        up_char_names = pool.pickup_4
    else:
        rarity = 2
        return random.choice(CharaterTable.get_from_rarity(2))
    if pool.name=="联合行动" or pool.name=="专属推荐干员寻访":
        if len(up_char_names)>0:
            char_name = random.choice(up_char_names)
            return CharaterTable.find_name(char_name)
    if len(up_char_names)==0:
        return random.choice(CharaterTable.get_from_rarity(rarity))
    index = int(random.random()/(up_pr/len(up_char_names)))
    if index>=len(up_char_names):
        return random.choice([i for i in CharaterTable.get_from_rarity(rarity) if i.name not in up_char_names])
    else:
        return CharaterTable.find_name(up_char_names[index])

async def gacha_img_build(chars:List[Character])->Image.Image:
    base_path = pathlib.Path("resource/arknight_gacha")
    portrait_path = pathlib.Path("resource/arknight_resources/portrait")
    template_img = await loadImage(base_path/"background_img/2.png")
    template_img = template_img.convert("RGBA")
    for i, char in enumerate(chars):
        portrait_img = await loadImage(portrait_path/f"{char.code}_1.png")
        rarity_img = await loadImage(base_path/f"rarity_img/{char.rarity}.png")
        rarity_back_img = await loadImage(base_path/f"background_img/{char.rarity}.png")
        profession_img = await loadImage(base_path/f"profession_img/{char.profession}.png")
        portrait_img = portrait_img.crop((23, 0, 143, 360))
        portrait_img = portrait_img.resize((123, 367))

        rarity_back_img = rarity_back_img.crop((27+i*123, 0, 149+i*123, 720))
        template_img.paste(rarity_back_img, (27+i*123, 0))
        template_img.paste(rarity_img, (27+i*123, 0))
        template_img.alpha_composite(portrait_img, (27+i*123, 175))
        template_img.alpha_composite(profession_img, (34+round(i*122.5), 490))
    return template_img
