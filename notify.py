# Mostly taken from https://github.com/AndreasArvidsson/andreas-talon/blob/a75f09ab67a979fca8032a2ab3304fac36220608/misc/screen.py
from typing import Optional

from talon import Module, ui
from talon.canvas import Canvas
from talon.skia import Paint as Paint
from talon.skia.imagefilter import ImageFilter as ImageFilter

mod = Module()

canvas: Optional[Canvas] = None


@mod.action_class
class Actions:
    def private_wax_notify_sticky(text: str):
        """Show notification"""
        global canvas

        def on_draw(c):
            # The min(width, height) is to not get gigantic size on portrait height
            height = min(c.width, c.height)
            rect = set_text_size_and_get_rect(c, height, text)
            x = c.rect.center.x - rect.center.x
            y = c.rect.center.y + rect.height / 2
            draw_text(c, text, x, y)

        canvas = Canvas.from_rect(ui.main_screen().rect)
        canvas.register("draw", on_draw)
        canvas.freeze()

    def private_wax_hide_sticky_notification():
        """Hide notification"""
        global canvas

        if canvas is not None:
            canvas.close()
            canvas = None


def set_text_size_and_get_rect(c, height: int, text: str):
    height_div = 14
    while True:
        c.paint.textsize = round(height / height_div)
        rect = c.paint.measure_text(text)[1]
        if rect.width < c.width * 0.75:
            return rect
        height_div += 2


def draw_text(c, text: str, x: int, y: int):
    filter = ImageFilter.drop_shadow(2, 2, 1, 1, "000000")
    c.paint.imagefilter = filter

    c.paint.style = c.paint.Style.FILL
    c.paint.color = "ffffff"
    c.draw_text(text, x, y)
