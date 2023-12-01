# rich with loguru
from loguru import logger
from rich.console import Console
from rich.logging import RichHandler
from rich.highlighter import Highlighter

class DefaultWhite(Highlighter):
    def highlight(self, text):
        text.stylize(f"color(254)")


default_white = DefaultWhite()

console = Console(style="white", color_system="256", no_color=True, highlighter=default_white)

rich_handler = RichHandler(console=console, highlighter=DefaultWhite(), show_level=False, show_time=False, show_path=False)

LOG_FORMAT = "[{time:HH:mm:ss_DD-MM-YYYY}] | {level} | <level>{message}</level>"
logger.remove()
logger.add(rich_handler, format=LOG_FORMAT)
logger.add("logs/code_generation_{time}.log", format=LOG_FORMAT)
# logger.add(sys.stdout, colorize=True, format="<green>[{time: HH:mm:ss_DD-MM-YYYY}]</green> | {level} | <level>{message}</level>")