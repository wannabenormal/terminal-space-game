import asyncio
import time
import curses
import random
from itertools import cycle

from curses_tools import draw_frame, read_controls, get_frame_size


async def blink(canvas, row, column, symbol='*'):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)

        for _ in range(random.randint(0, 10)):
            await asyncio.sleep(0)

        for _ in range(20):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)

        for _ in range(3):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)

        for _ in range(5):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def spaceship(canvas, start_row, start_col, frames):
    previous_frame = None
    previous_row = None
    previous_col = None
    canvas_h, canvas_w = canvas.getmaxyx()

    frame_h, frame_w = get_frame_size(frames[0])

    row = start_row - int(frame_h / 2)
    col = start_col - int(frame_w / 2)

    for frame in cycle(frames):
        previous_row = row
        previous_col = col

        row_direction, column_direction, _ = read_controls(canvas)

        if row + row_direction > 0 and row + row_direction < canvas_h - frame_h:
            row = row + row_direction

        if col + column_direction > 0 and col + column_direction < canvas_w - frame_w:
            col = col + column_direction

        if previous_frame:
            draw_frame(canvas, previous_row, previous_col, previous_frame, negative=True)

        draw_frame(canvas, row, col, frame)
        previous_frame = frame
        canvas.refresh()

        await asyncio.sleep(0)
        await asyncio.sleep(0)


def draw(canvas):
    TIC_TIMEOUT = 0.1
    STARS_COUNT = 100

    ROCKET_FRAMES_PATHS = [
        'frames/rocket_frame_1.txt',
        'frames/rocket_frame_2.txt',
    ]

    rocket_frames = []

    for rocket_frame_path in ROCKET_FRAMES_PATHS:
        with open(rocket_frame_path, 'r') as file:
            rocket_frames.append(file.read())

    max_row, max_col = canvas.getmaxyx()
    stars_symbols = ['*', '+', ':']

    curses.curs_set(False)
    canvas.nodelay(True)

    stars_coordinates = [
        (random.randint(1, max_row - 2), random.randint(1, max_col - 2))
        for _ in range(STARS_COUNT)
    ]

    coroutines = [
        blink(canvas, row, column, symbol=random.choice(stars_symbols))
        for row, column in list(set(stars_coordinates))
    ]

    coroutines.append(
        fire(canvas, int(max_row / 2), int(max_col / 2))
    )

    coroutines.append(
        spaceship(canvas, int(max_row / 2), int(max_col / 2), rocket_frames)
    )

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        if len(coroutines) == 0:
            break

        canvas.refresh()
        canvas.border()
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
