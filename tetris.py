import pygame
import random
import sys

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
PLAY_WIDTH = 300
PLAY_HEIGHT = 600
BLOCK_SIZE = 30

TOP_LEFT_X = (SCREEN_WIDTH - PLAY_WIDTH) // 2
TOP_LEFT_Y = SCREEN_HEIGHT - PLAY_HEIGHT - 10

TARGET_FPS = 60  # Target frames per second

# --- Fonts ---
FONT_FAMILY = 'consolas'
TITLE_SIZE = 40
SCORE_SIZE = 24
NEXT_SIZE = 24
MENU_SIZE = 30
GAMEOVER_SIZE = 55
INSTRUCTION_SIZE = 22
PAUSE_SIZE = 50

# --- Colors ---
GRID_LINE_COLOR = (60, 60, 60)
BORDER_COLOR = (100, 100, 100)
PAUSE_TEXT_COLOR = (200, 200, 200)
BACKGROUND_COLOR = (0, 0, 0)
INFO_TEXT_COLOR = (255, 255, 255)

# --- Scoring ---
POINTS_PER_LINE = {1: 40, 2: 100, 3: 300, 4: 1200}
POINTS_PER_SOFT_DROP = 1

# --- Gameplay Constants ---
LOCK_DELAY_MS = 400

# NES-like speed curve (frames per gridcell drop)
LEVEL_SPEED_FRAMES = {
    1: 48, 2: 43, 3: 38, 4: 33, 5: 28, 6: 23, 7: 18, 8: 13, 9: 8, 10: 6,
    11: 5, 12: 5, 13: 5, 14: 4, 15: 4, 16: 4, 17: 3, 18: 3, 19: 3
}
DEFAULT_SPEED_FRAMES_LEVEL_19_PLUS = 3
DEFAULT_SPEED_FRAMES_LEVEL_29_PLUS = 2

# --- Tetromino Shapes & Colors ---
S = [['.....',
      '.....',
      '..00.',
      '.00..',
      '.....'],
     ['.....',
      '..0..',
      '..00.',
      '...0.',
      '.....']]

Z = [['.....',
      '.....',
      '.00..',
      '..00.',
      '.....'],
     ['.....',
      '..0..',
      '.00..',
      '.0...',
      '.....']]

I = [['..0..',
      '..0..',
      '..0..',
      '..0..',
      '.....'],
     ['.....',
      '0000.',
      '.....',
      '.....',
      '.....']]

O = [['.....',
      '.....',
      '.00..',
      '.00..',
      '.....']]

J = [['.....',
      '.0...',
      '.000.',
      '.....',
      '.....'],
     ['.....',
      '..00.',
      '..0..',
      '..0..',
      '.....'],
     ['.....',
      '.....',
      '.000.',
      '...0.',
      '.....'],
     ['.....',
      '..0..',
      '..0..',
      '.00..',
      '.....']]

L = [['.....',
      '...0.',
      '.000.',
      '.....',
      '.....'],
     ['.....',
      '..0..',
      '..0..',
      '..00.',
      '.....'],
     ['.....',
      '.....',
      '.000.',
      '.0...',
      '.....'],
     ['.....',
      '.00..',
      '..0..',
      '..0..',
      '.....']]

T = [['.....',
      '..0..',
      '.000.',
      '.....',
      '.....'],
     ['.....',
      '..0..',
      '..00.',
      '..0..',
      '.....'],
     ['.....',
      '.....',
      '.000.',
      '..0..',
      '.....'],
     ['.....',
      '..0..',
      '.00..',
      '..0..',
      '.....']]

master_shapes = [S, Z, I, O, J, L, T]
shape_colors = [
    (0, 255, 0), (255, 0, 0), (0, 255, 255), (255, 255, 0),
    (255, 165, 0), (0, 0, 255), (128, 0, 128)
]
current_bag = []


class Piece(object):
    """Represents a Tetris piece."""

    def __init__(self, column, row, shape):
        self.x = column
        self.y = row
        self.shape = shape
        self.color = shape_colors[master_shapes.index(shape)]
        self.rotation = 0


def get_light_color(color, amount=50):
    """Lightens the given color by the specified amount."""
    if color == BACKGROUND_COLOR:
        return color
    return tuple(min(255, c + amount) for c in color)


def get_dark_color(color, amount=50):
    """Darkens the given color by the specified amount."""
    if color == BACKGROUND_COLOR:
        return color
    return tuple(max(0, c - amount) for c in color)


def create_grid(locked_positions={}):
    """Creates the game grid based on locked pieces."""
    grid = [[BACKGROUND_COLOR for _ in range(10)] for _ in range(20)]
    for y_pos in range(len(grid)):
        for x_pos in range(len(grid[y_pos])):
            if (x_pos, y_pos) in locked_positions:
                grid[y_pos][x_pos] = locked_positions[(x_pos, y_pos)]
    return grid


def convert_shape_format(shape_obj):
    """Converts the shape's string format to grid coordinates."""
    positions = []
    shape_pattern = shape_obj.shape[shape_obj.rotation % len(shape_obj.shape)]
    for i, line in enumerate(shape_pattern):
        row = list(line)
        for j, column in enumerate(row):
            if column == '0':
                positions.append((shape_obj.x + j, shape_obj.y + i))

    offset_x = 2
    offset_y = 4
    for i, pos in enumerate(positions):
        positions[i] = (pos[0] - offset_x, pos[1] - offset_y)
    return positions


def is_valid_space(shape_obj, grid):
    """Checks if the piece is in a valid position on the grid."""
    accepted_positions = [
        (j, i) for i in range(20) for j in range(10) if grid[i][j] == BACKGROUND_COLOR
    ]
    formatted_shape = convert_shape_format(shape_obj)
    for pos in formatted_shape:
        x_pos, y_pos = pos
        if not (0 <= x_pos < 10):
            return False  # Out of bounds horizontally
        if y_pos >= 20:
            return False  # Out of bounds vertically
        if y_pos >= 0 and pos not in accepted_positions:
            return False  # Colliding with another piece
    return True


def check_if_should_lock(shape_obj, grid):
    """Checks if the piece is resting on the ground or another piece."""
    shape_obj.y += 1
    is_blocked_below = not is_valid_space(shape_obj, grid)
    shape_obj.y -= 1
    return is_blocked_below


def get_shape():
    """Returns a new random piece from the bag."""
    global current_bag
    if not current_bag:
        current_bag = list(master_shapes)
        random.shuffle(current_bag)
    shape_definition = current_bag.pop()
    return Piece(5, 0, shape_definition)


def clear_rows(grid, locked):
    """Clears completed rows and returns the number of cleared rows."""
    rows_cleared = 0
    rows_to_clear_indices = []
    for i in range(len(grid) - 1, -1, -1):
        if BACKGROUND_COLOR not in grid[i]:
            rows_cleared += 1
            rows_to_clear_indices.append(i)
            for j in range(10):
                if (j, i) in locked:
                    del locked[(j, i)]

    if rows_cleared > 0:
        temp_locked = locked.copy()
        locked.clear()
        # Sort by y-key to handle shifting down correctly
        sorted_keys = sorted(temp_locked.items(), key=lambda item: item[0][1], reverse=True)
        for (x_key, y_key), color in sorted_keys:
            cleared_below_count = sum(1 for r_index in rows_to_clear_indices if r_index > y_key)
            new_key = (x_key, y_key + cleared_below_count)
            locked[new_key] = color
    return rows_cleared


def draw_block(surface, color, x, y, size):
    """Draws a single block with a pseudo-3D effect."""
    if color == BACKGROUND_COLOR:
        return
    light_color = get_light_color(color)
    dark_color = get_dark_color(color)
    pygame.draw.rect(surface, color, (x, y, size, size))
    pygame.draw.line(surface, light_color, (x, y), (x + size - 1, y))
    pygame.draw.line(surface, light_color, (x, y), (x, y + size - 1))
    pygame.draw.line(surface, dark_color, (x, y + size - 1), (x + size - 1, y + size - 1))
    pygame.draw.line(surface, dark_color, (x + size - 1, y), (x + size - 1, y + size - 1))


def draw_text_middle(text, size, color, surface):
    """Draws text centered on the screen."""
    font = pygame.font.SysFont(FONT_FAMILY, size, bold=True)
    label = font.render(text, 1, color)
    center_x = SCREEN_WIDTH / 2 - label.get_width() / 2
    center_y = SCREEN_HEIGHT / 2 - label.get_height() / 2
    surface.blit(label, (center_x, center_y))


def draw_text_middle_offset(text, size, color, surface, y_offset=0):
    """Draws text centered on the screen with a vertical offset."""
    font = pygame.font.SysFont(FONT_FAMILY, size, bold=True)
    label = font.render(text, 1, color)
    center_x = SCREEN_WIDTH / 2 - label.get_width() / 2
    center_y = SCREEN_HEIGHT / 2 - label.get_height() / 2 + y_offset
    surface.blit(label, (center_x, center_y))


def draw_text_top_center(text, size, color, surface, y_pos):
    """Draws text centered above the play area."""
    font = pygame.font.SysFont(FONT_FAMILY, size, bold=True)
    label = font.render(text, 1, color)
    center_x = TOP_LEFT_X + PLAY_WIDTH / 2 - label.get_width() / 2
    surface.blit(label, (center_x, y_pos))


def draw_grid_lines(surface):
    """Draws the grid lines for the play area."""
    start_x = TOP_LEFT_X
    start_y = TOP_LEFT_Y
    for i in range(21):  # Horizontal lines
        pygame.draw.line(surface, GRID_LINE_COLOR, (start_x, start_y + i * BLOCK_SIZE),
                         (start_x + PLAY_WIDTH, start_y + i * BLOCK_SIZE), 1)
    for j in range(11):  # Vertical lines
        pygame.draw.line(surface, GRID_LINE_COLOR, (start_x + j * BLOCK_SIZE, start_y),
                         (start_x + j * BLOCK_SIZE, start_y + PLAY_HEIGHT), 1)


def draw_next_shape(shape_obj, surface):
    """Draws the 'next piece' preview."""
    font = pygame.font.SysFont(FONT_FAMILY, NEXT_SIZE)
    label = font.render('Next:', 1, INFO_TEXT_COLOR)

    preview_area_x = TOP_LEFT_X + PLAY_WIDTH + 50
    preview_area_y = TOP_LEFT_Y + PLAY_HEIGHT / 2 - 80
    label_y_pos = preview_area_y - 85

    surface.blit(label, (preview_area_x + 10, label_y_pos))

    # Centering and drawing logic
    shape_pattern = shape_obj.shape[0]
    temp_piece = Piece(0, 0, shape_obj.shape)
    positions = convert_shape_format(temp_piece)
    if not positions:
        return

    min_x = min(p[0] for p in positions)
    max_x = max(p[0] for p in positions)
    min_y = min(p[1] for p in positions)
    max_y = max(p[1] for p in positions)

    shape_w = (max_x - min_x + 1) * BLOCK_SIZE
    shape_h = (max_y - min_y + 1) * BLOCK_SIZE
    box_w = 4 * BLOCK_SIZE
    box_h = 4 * BLOCK_SIZE

    start_x = preview_area_x + (box_w - shape_w) / 2
    start_y = preview_area_y + (box_h - shape_h) / 2

    for i, line in enumerate(shape_pattern):
        for j, column in enumerate(list(line)):
            if column == '0':
                draw_x = start_x + (j - 2) * BLOCK_SIZE
                draw_y = start_y + (i - 2) * BLOCK_SIZE
                draw_block(surface, shape_obj.color, draw_x, draw_y, BLOCK_SIZE)


def draw_window(surface, grid, score=0, level=1):
    """Draws all static elements of the game window."""
    surface.fill(BACKGROUND_COLOR)
    draw_text_top_center('TETRIS', TITLE_SIZE, INFO_TEXT_COLOR, surface, 20)

    # Display Level, Score, and Pause instructions
    font = pygame.font.SysFont(FONT_FAMILY, SCORE_SIZE)
    info_x = TOP_LEFT_X + PLAY_WIDTH + 50
    info_y = TOP_LEFT_Y + 50
    line_height = 30

    label_level = font.render(f'Level: {level}', 1, INFO_TEXT_COLOR)
    surface.blit(label_level, (info_x, info_y))
    label_score = font.render(f'Score: {score}', 1, INFO_TEXT_COLOR)
    surface.blit(label_score, (info_x, info_y + line_height))
    label_pause = font.render('P - Pause', 1, INFO_TEXT_COLOR)
    surface.blit(label_pause, (info_x, info_y + line_height * 2))

    # Draw locked pieces from the grid
    for i in range(len(grid)):
        for j in range(len(grid[i])):
            draw_block(surface, grid[i][j], TOP_LEFT_X + j * BLOCK_SIZE, TOP_LEFT_Y + i * BLOCK_SIZE, BLOCK_SIZE)

    # Draw border and grid lines
    draw_grid_lines(surface)
    pygame.draw.rect(surface, BORDER_COLOR, (TOP_LEFT_X, TOP_LEFT_Y, PLAY_WIDTH, PLAY_HEIGHT), 2)


def main(window):
    """Runs the main game loop."""
    global current_bag
    current_bag = []  # Reset the bag for a new game

    locked_positions = {}
    change_piece = False
    game_running = True
    paused = False

    current_piece = get_shape()
    next_piece = get_shape()
    clock = pygame.time.Clock()
    fall_time_accumulator = 0

    score = 0
    level = 1
    lines_cleared_total = 0
    lock_timer_start = None

    while game_running:
        grid = create_grid(locked_positions)
        time_now = pygame.time.get_ticks()
        delta_time_ms = clock.tick(TARGET_FPS)
        fall_time_accumulator += delta_time_ms

        if paused:
            draw_text_middle("Paused", PAUSE_SIZE, PAUSE_TEXT_COLOR, window)
            pygame.display.update()
            while paused:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        game_running = False
                        paused = False
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_p:
                            paused = False
                        if event.key == pygame.K_ESCAPE:
                            game_running = False
                            paused = False
                clock.tick(15)  # Lower tick rate while paused

            # Reset timers after unpausing
            fall_time_accumulator = 0
            lock_timer_start = None
            continue

        # --- Gravity ---
        frames_per_drop = LEVEL_SPEED_FRAMES.get(level)
        if frames_per_drop is None:
            frames_per_drop = DEFAULT_SPEED_FRAMES_LEVEL_29_PLUS if level >= 29 else DEFAULT_SPEED_FRAMES_LEVEL_19_PLUS
        time_per_drop_ms = frames_per_drop * (1000.0 / TARGET_FPS) if TARGET_FPS > 0 else float('inf')

        if fall_time_accumulator >= time_per_drop_ms:
            fall_time_accumulator = 0
            current_piece.y += 1
            if not is_valid_space(current_piece, grid):
                current_piece.y -= 1

        moved_or_rotated = False

        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_running = False
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    paused = True
                    continue
                if event.key == pygame.K_ESCAPE:
                    game_running = False
                    continue

                original_x = current_piece.x
                original_rot = current_piece.rotation

                if event.key == pygame.K_LEFT:
                    current_piece.x -= 1
                    if not is_valid_space(current_piece, grid):
                        current_piece.x = original_x
                    else:
                        moved_or_rotated = True

                elif event.key == pygame.K_RIGHT:
                    current_piece.x += 1
                    if not is_valid_space(current_piece, grid):
                        current_piece.x = original_x
                    else:
                        moved_or_rotated = True

                elif event.key == pygame.K_DOWN:  # Soft drop
                    current_piece.y += 1
                    if is_valid_space(current_piece, grid):
                        score += POINTS_PER_SOFT_DROP
                        fall_time_accumulator = 0  # Reset gravity timer on soft drop
                        moved_or_rotated = True
                    else:
                        current_piece.y -= 1

                elif event.key == pygame.K_UP:  # Rotate + Wall Kick
                    current_piece.rotation = (current_piece.rotation + 1) % len(current_piece.shape)
                    if not is_valid_space(current_piece, grid):
                        # Try wall kick
                        current_piece.x += 1
                        if not is_valid_space(current_piece, grid):
                            current_piece.x -= 2
                            if not is_valid_space(current_piece, grid):
                                current_piece.x = original_x  # Revert x
                                current_piece.rotation = original_rot  # Revert rotation
                            else:
                                moved_or_rotated = True
                        else:
                            moved_or_rotated = True
                    else:
                        moved_or_rotated = True

                elif event.key == pygame.K_SPACE:  # Hard drop
                    while is_valid_space(current_piece, grid):
                        current_piece.y += 1
                    current_piece.y -= 1
                    change_piece = True
                    lock_timer_start = None

        # --- Lock Delay ---
        should_be_locking_now = check_if_should_lock(current_piece, grid)
        if should_be_locking_now and not change_piece:
            if lock_timer_start is None:
                lock_timer_start = time_now
            else:
                if moved_or_rotated:
                    lock_timer_start = None  # Reset timer if piece moved
                elif time_now - lock_timer_start >= LOCK_DELAY_MS:
                    if check_if_should_lock(current_piece, grid):
                        change_piece = True
                    lock_timer_start = None
        elif not should_be_locking_now:
            lock_timer_start = None

        # --- Piece Locking & State Update ---
        if change_piece:
            final_piece_positions = convert_shape_format(current_piece)
            for pos in final_piece_positions:
                locked_positions[(pos[0], pos[1])] = current_piece.color

            # Game Over Check 1: Piece locked above the screen
            if any(y < 1 for _, y in final_piece_positions):
                game_running = False

            grid_after_lock = create_grid(locked_positions)
            rows_cleared = clear_rows(grid_after_lock, locked_positions)

            if rows_cleared > 0:
                lines_cleared_total += rows_cleared
                score += POINTS_PER_LINE.get(rows_cleared, 0) * level
                level = lines_cleared_total // 10 + 1

            current_piece = next_piece
            next_piece = get_shape()
            change_piece = False
            lock_timer_start = None

            # Game Over Check 2: New piece spawns in an invalid spot
            if game_running and not is_valid_space(current_piece, grid_after_lock):
                game_running = False

        # --- Drawing ---
        draw_window(window, grid, score, level)
        draw_next_shape(next_piece, window)

        # Draw current piece
        if game_running:
            current_piece_pos = convert_shape_format(current_piece)
            for x_pos, y_pos in current_piece_pos:
                if y_pos >= 0:
                    # CORRECTED a bug here: The arguments were in the wrong order.
                    draw_block(window,
                               current_piece.color,
                               TOP_LEFT_X + x_pos * BLOCK_SIZE,
                               TOP_LEFT_Y + y_pos * BLOCK_SIZE,
                               BLOCK_SIZE)

        pygame.display.update()

    # --- Game Over Screen ---
    draw_text_middle_offset("Game Over", GAMEOVER_SIZE, (255, 255, 255), window, -20)
    draw_text_middle_offset("Press any key to return to menu", INSTRUCTION_SIZE, (255, 255, 255), window, 30)
    pygame.display.update()
    pygame.time.delay(500)

    waiting_for_key = True
    while waiting_for_key:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                waiting_for_key = False


def main_menu(window):
    """Displays the main menu and waits for player input."""
    menu_running = True
    while menu_running:
        window.fill((0, 0, 0))
        draw_text_middle('Press any key to start or ESC to Exit', MENU_SIZE, INFO_TEXT_COLOR, window)
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                menu_running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    menu_running = False
                else:
                    main(window)  # Start the game

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    pygame.init()
    pygame.font.init()
    game_window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('Tetris')
    main_menu(game_window)
