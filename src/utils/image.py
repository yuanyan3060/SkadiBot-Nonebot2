from PIL import Image, ImageDraw
import aiofiles
import pathlib
from typing import Union, Tuple, List
from io import BytesIO
from functools import lru_cache
import re
import unicodedata
from .font import SarasaFont
from dataclasses import dataclass
path_like = Union[str, pathlib.Path]


async def loadImage(path: path_like) -> Image.Image:
    buffer = BytesIO()
    async with aiofiles.open(path, "rb") as fp:
        temp = await fp.read()
        buffer.write(temp)
        return Image.open(buffer)


def saveImage(img: Image.Image) -> BytesIO:
    buffer = BytesIO()
    img.save(buffer, format="png")
    return buffer


@dataclass
class ColorText:
    text: str
    color: Tuple[int, int, int]


def get_text_color(text: str) -> List[ColorText]:
    """<color="#FF0000">红色字体</color>"""
    color_stack = []
    pos_color = []
    start = 0
    end = len(text)
    color = (0, 0, 0)
    for i in re.finditer('(<color="#([0-9a-fA-F]{6})")|(</color>)', text):
        pos, endpos = i.span()
        if len(color_stack) > 0:
            color = color_stack[-1]
        else:
            color = (0, 0, 0)
        end = pos
        if start < end:
            pos_color.append(((start, end), color))
        start = endpos
        s = i.group()
        if s.startswith("</"):
            color_stack.pop()
        else:
            start = endpos+1
            r = int(s[9:11], 16)
            g = int(s[11:13], 16)
            b = int(s[13:15], 16)
            color_stack.append((r, g, b))
    if start != len(text):
        pos_color.append(((start, len(text)), color))
    return [ColorText(text[pos[0]:pos[1]], color) for pos, color in pos_color]


@lru_cache
def get_ambiguous_char_width(c: str) -> int:
    return SarasaFont.getlength(c)


def get_char_width(c: str) -> Union[float, int]:
    east_asian_width = unicodedata.east_asian_width(c)
    if east_asian_width in ["F", "W"]:
        return SarasaFont.size
    elif east_asian_width == "A":
        return get_ambiguous_char_width(c)
    else:
        return SarasaFont.size/2


def text2image(text: str, max_width: int = 520, edge: int = 10) -> Image.Image:
    color_texts: List[ColorText] = get_text_color(text)
    x = edge
    y = 0
    for color_text in color_texts:
        for char in color_text.text:
            if char == "\n":
                x = edge
                y += SarasaFont.size+5
                continue
            char_width = get_char_width(char)
            if char_width+x > max_width-2*edge:
                x = edge+char_width
                y += SarasaFont.size+5
            else:
                x += char_width
    if x != edge:
        y += SarasaFont.size+5
    img = Image.new(mode="RGBA", size=(max_width, y), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    x = edge
    y = 0
    for color_text in color_texts:
        temp_str = ""
        temp_length = 0
        for char in color_text.text:
            if char == "\n":
                draw.text((x-temp_length, y), text=temp_str,
                          fill=color_text.color, font=SarasaFont)
                x = edge
                y += SarasaFont.size+5
                temp_str = ""
                temp_length = 0
                continue
            char_width = get_char_width(char)
            if char_width+x > max_width-2*edge:
                draw.text((x-temp_length, y), text=temp_str,
                          fill=color_text.color, font=SarasaFont)
                x = edge
                y += SarasaFont.size+5
                temp_str = ""
                temp_length = 0
            temp_length += char_width
            temp_str += char
            x += char_width
        if temp_length != 0:
            draw.text((x-temp_length, y), text=temp_str,
                      fill=color_text.color, font=SarasaFont)
    return img
