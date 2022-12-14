import asyncio
import time
import curses
import random
from itertools import cycle

from curses_tools import draw_frame, read_controls, get_frame_size
from physics import update_speed
from obstacles import Obstacle
from explosions import explode
from game_scenario import PHRASES, get_garbage_delay_tics


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)


async def blink(canvas, row, column, offset_tics=5, symbol='*'):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)

        await sleep(offset_tics)

        await sleep(20)

        canvas.addstr(row, column, symbol)

        await sleep(3)

        canvas.addstr(row, column, symbol, curses.A_BOLD)

        await sleep(5)

        canvas.addstr(row, column, symbol)
        await sleep(3)


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await sleep()

    canvas.addstr(round(row), round(column), 'O')
    await sleep()
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        for obstacle in obstacles:
            if obstacle.has_collision(row, column):
                obstacles_in_last_collisions.append(obstacle)
                return

        canvas.addstr(round(row), round(column), symbol)
        await sleep()
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def render_spaceship(canvas, start_row, start_col, frames, max_speed=1):
    canvas_h, canvas_w = canvas.getmaxyx()

    frame_h, frame_w = get_frame_size(frames[0])

    row = start_row - int(frame_h / 2)
    col = start_col - int(frame_w / 2)

    row_speed = column_speed = 0

    for frame in cycle(frames):
        row_direction, column_direction, space_pressed = read_controls(canvas)

        row_speed, column_speed = update_speed(
            row_speed,
            column_speed,
            row_direction,
            column_direction,
            row_speed_limit=max_speed,
            column_speed_limit=max_speed
        )

        row += row_speed
        col += column_speed

        row = min(row, canvas_h - frame_h - border_width)
        col = min(col, canvas_w - frame_w - border_width)

        row = max(row, border_width)
        col = max(col, border_width)

        if space_pressed and year >= 2020:
            coroutines.append(fire(canvas, row, col + int(frame_w / 2)))

        draw_frame(canvas, row, col, frame)
        await sleep()

        draw_frame(canvas, row, col, frame, negative=True)

        for obstacle in obstacles:
            if obstacle.has_collision(row, col):
                coroutines.append(show_gameover(canvas, gameover_frame))
                return


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom. ??olumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()
    frame_h, frame_w = get_frame_size(garbage_frame)

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0

    while row < rows_number:
        try:
            obstacle = Obstacle(row, column, frame_h, frame_w)
            obstacles.append(obstacle)

            frame_row_center_pos = int(row + frame_h / 2)
            frame_col_center_pos = int(column + frame_w / 2)

            draw_frame(canvas, row, column, garbage_frame)
            await sleep()
            draw_frame(canvas, row, column, garbage_frame, negative=True)
            row += speed

            if obstacle in obstacles_in_last_collisions:
                obstacles_in_last_collisions.remove(obstacle)
                coroutines.append(
                    explode(canvas, frame_row_center_pos, frame_col_center_pos)
                )
                return
        finally:
            obstacles.remove(obstacle)


async def fill_orbit_with_garbage(canvas, garbage_frames):
    _, columns_number = canvas.getmaxyx()

    while True:
        garbage_delay_tics = get_garbage_delay_tics(year)
        column = random.randint(0, columns_number)
        column = min(column, columns_number - border_width - canvas_coord_offset)
        column = max(column, border_width)

        if garbage_delay_tics:
            coroutines.append(fly_garbage(canvas, column, random.choice(garbage_frames)))
        await sleep(garbage_delay_tics or 1)


async def show_gameover(canvas, frame):
    rows_number, columns_number = canvas.getmaxyx()
    frame_h, frame_w = get_frame_size(frame)

    center_row = int((rows_number - border_width - canvas_coord_offset) / 2 - frame_h / 2)
    center_col = int((columns_number - border_width - canvas_coord_offset) / 2 - frame_w / 2)

    while True:
        draw_frame(canvas, center_row, center_col, frame)

        await sleep()
        draw_frame(canvas, center_row, center_col, frame, negative=True)


async def draw_year(canvas):
    rows_number, _ = canvas.getmaxyx()
    year_area_height = 6
    year_area_width = 42

    year_area = canvas.derwin(
        year_area_height,
        year_area_width,
        rows_number - border_width - year_area_height,
        border_width
    )

    while True:
        frame_h, frame_w = get_frame_size(str(year))

        frame_row_pos = int(year_area_height / 2 - frame_h / 2)
        frame_col_pos = int(year_area_width / 2 - frame_w / 2)

        phrase = PHRASES.get(year)
        year_area.border()
        draw_frame(year_area, frame_row_pos, frame_col_pos, str(year))

        if phrase:
            draw_frame(year_area, frame_row_pos + 1, 1, phrase)

        await sleep()
        draw_frame(year_area, frame_row_pos, frame_col_pos, str(year), negative=True)

        if phrase:
            draw_frame(year_area, frame_row_pos + 1, 1, phrase, negative=True)


async def pass_years():
    global year
    while True:
        await sleep(15)
        year += 1


def draw(canvas):
    tic_timeout = 0.1
    stars_count = 100

    rocket_frames_paths = [
        'frames/rocket_frame_1.txt',
        'frames/rocket_frame_2.txt'
    ]

    garbage_frames_paths = [
        'frames/garbage/duck.txt',
        'frames/garbage/hubble.txt',
        'frames/garbage/lamp.txt',
        'frames/garbage/trash_large.txt',
        'frames/garbage/trash_small.txt',
        'frames/garbage/trash_xl.txt'
    ]

    rocket_frames = []
    garbage_frames = []

    for rocket_frame_path in rocket_frames_paths:
        with open(rocket_frame_path, 'r') as file:
            frame = file.read()
            rocket_frames.extend([frame, frame])

    for garbage_frame_path in garbage_frames_paths:
        with open(garbage_frame_path, 'r') as file:
            garbage_frames.append(file.read())

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

    coroutines.extend([
        blink(
            canvas, row, column,
            offset_tics=random.randint(0, 10),
            symbol=random.choice(stars_symbols)
        )
        for row, column in list(set(stars_coordinates))
    ])

    coroutines.extend(
        [
            render_spaceship(canvas, int(canvas_h / 2), int(canvas_w / 2), rocket_frames),
            fill_orbit_with_garbage(canvas, garbage_frames),
            draw_year(canvas),
            pass_years()
        ]
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
    coroutines = []
    obstacles = []
    obstacles_in_last_collisions = []
    border_width = 1
    canvas_coord_offset = 1
    year = 1957

    with open('frames/game_over.txt', 'r') as file:
        gameover_frame = file.read()

    curses.update_lines_cols()
    curses.wrapper(draw)
