import sys


class Color:
    GRAY = "\033[90m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    RETURN = "\033[07m"  # 反転
    ACCENT = "\033[01m"  # 強調
    FLASH = "\033[05m"  # 点滅
    RED_FLASH = "\033[05;41m"  # 赤背景+点滅
    END = "\033[0m"

def user_input(str: str):
    try:
        query = input(Color.GREEN + str).rstrip()
        print(Color.END)
        return query
    except KeyboardInterrupt:
        print(Color.RED + "\n入力が中断されました" + Color.END)
        sys.exit(1)


def llm_print(str: str):
    print(Color.BLUE + str + Color.END)


def event_print(str: str):
    print(Color.GRAY + str + Color.END)


def error_print(str: str):
    print(Color.RED + str + Color.END)
