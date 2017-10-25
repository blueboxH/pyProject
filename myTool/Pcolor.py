''' cmd print出有颜色字体 '''
import ctypes
STD_INPUT_HANDLE = -10
STD_OUTPUT_HANDLE = -11
STD_ERROR_HANDLE = -12
FOREGROUND_BLACK = 0x0
FOREGROUND_BLUE = 0x01  # text color contains blue.
FOREGROUND_GREEN = 0x02  # text color contains green.
FOREGROUND_RED = 0x04  # text color contains red.
FOREGROUND_INTENSITY = 0x08  # text color is intensified.
BACKGROUND_BLUE = 0x10  # background color contains blue.
BACKGROUND_GREEN = 0x20  # background color contains green.
BACKGROUND_RED = 0x40  # background color contains red.
BACKGROUND_INTENSITY = 0x80  # background color is intensified.

std_out_handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)


def set_cmd_color(color, handle=std_out_handle):
    """(color) -> bit
    Example: set_cmd_color(FOREGROUND_RED | FOREGROUND_GREEN | FOREGROUND_BLUE | FOREGROUND_INTENSITY)
    """
    res = ctypes.windll.kernel32.SetConsoleTextAttribute(handle, color)
    return res


def reset_color():
    """print_blue_text"""
    set_cmd_color(FOREGROUND_RED | FOREGROUND_GREEN | FOREGROUND_BLUE)


def print_red(*print_text):
    """print_blue_text"""
    set_cmd_color(FOREGROUND_RED | FOREGROUND_INTENSITY)
    print(*print_text)
    reset_color()


def print_green(*print_text):
    """print_blue_text"""
    set_cmd_color(FOREGROUND_GREEN | FOREGROUND_INTENSITY)
    print(*print_text)
    reset_color()


def print_blue(*print_text):
    """print_blue_text"""
    set_cmd_color(FOREGROUND_BLUE | FOREGROUND_INTENSITY)
    print(*print_text)
    reset_color()


def print_rd(*print_text):
    """print_red_text_with_blue_bg"""
    set_cmd_color(FOREGROUND_RED | FOREGROUND_INTENSITY |
                  BACKGROUND_BLUE | BACKGROUND_INTENSITY)
    print(*print_text)
    reset_color()


if __name__ == '__main__':

    print_red("haode", "haode")
    print_blue("haode", "haode")
    print_green("haode", "haode")
    print('buhao')
