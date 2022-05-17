from nonebot import on_command
from .download import Downloader
from nonebot.matcher import Matcher
from nonebot.adapters import Message
from nonebot.params import Arg, CommandArg, ArgPlainText
update = on_command("更新明日方舟", aliases={"明日方舟更新"}, priority=1)

@update.handle()
async def _(matcher: Matcher, args: Message = CommandArg()):
    is_update, is_success = await Downloader.update()
    if not is_update:
        await update.finish("本地资源无需更新")
    if is_success:
        await update.finish("本地资源更新完成")
    await update.finish("本地资源更新失败")