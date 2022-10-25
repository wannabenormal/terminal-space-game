import asyncio
import time
import curses
import random
from itertools import cycle

from curses_tools import draw_frame, read_controls, get_frame_size


async def blink(canvas, row, column, offset_tics=5, symbol='*'):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)

        for _ in range(offset_tics):
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


async def render_spaceship(canvas, start_row, start_col, frames, speed=1):
    border_width = 1
    canvas_h, canvas_w = canvas.getmaxyx()

    frame_h, frame_w = get_frame_size(frames[0])

    row = start_row - int(frame_h / 2)
    col = start_col - int(frame_w / 2)

    for frame in cycle(frames):
        row_direction, column_direction, _ = read_controls(canvas)

        next_row = row + row_direction * speed
        next_col = col + column_direction * speed

        next_row = min(next_row, canvas_h - frame_h - border_width)
        next_col = min(next_col, canvas_w - frame_w - border_width)

        next_row = max(next_row, border_width)
        next_col = max(next_col, border_width)

        row = next_row
        col = next_col

        draw_frame(canvas, row, col, frame)
        await asyncio.sleep(0)

        draw_frame(canvas, row, col, frame, negative=True)


def draw(canvas):
    tic_timeout = 0.1
    stars_count = 100
    border_width = 1
    canvas_coord_offset = 1

    rocket_frames_paths = [
        'frames/rocket_frame_1.txt',
        'frames/rocket_frame_2.txt'
    ]

    rocket_frames = []

    for rocket_frame_path in rocket_frames_paths:
        with open(rocket_frame_path, 'r') as file:
            frame = file.read()
            rocket_frames.append(frame)
            rocket_frames.append(frame)

    canvas_h, canvas_w = canvas.getmaxyx()
    stars_symbols = '*+:'

    max_row = canvas_h - border_width - canvas_coord_offset
    max_col = canvas_w - border_width - canvas_coord_offset

    curses.curs_set(False)
    canvas.nodelay(True)

    stars_coordinates = [
        (random.randint(1, max_row), random.randint(1, max_col))
        for _ in range(stars_count)
    ]

    coroutines = [
        blink(
            canvas, row, column,
            offset_tics=random.randint(0, 10),
            symbol=random.choice(stars_symbols)
        )
        for row, column in list(set(stars_coordinates))
    ]

    coroutines.append(
        fire(canvas, int(canvas_h / 2), int(canvas_w / 2))
    )

    coroutines.append(
        render_spaceship(canvas, int(canvas_h / 2), int(canvas_w / 2), rocket_frames)
    )

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        canvas.border()
        time.sleep(tic_timeout)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
