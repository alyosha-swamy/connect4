import numpy as np
from scipy.signal import convolve2d
from dataclasses import dataclass
from typing import Any, TypeAlias, Literal

@dataclass
class State:
    """State of the game"""
    board: np.ndarray[Any, np.dtype[np.int8]]

@dataclass
class Observation:
    """Observation by a single player of the game"""
    board: np.ndarray[Any, np.dtype[np.int8]]


# Column to place it in
Action:TypeAlias = np.int8

# Reward for the agent
Reward:TypeAlias = np.float32

# Value of an observation for an agent
Value:TypeAlias = np.float32

# Advantage of a particular action for an agent
Advantage:TypeAlias = np.float32

Player:TypeAlias = np.int8

PLAYER1:Player = np.int8(1)
PLAYER2:Player = np.int8(2)

def opponent(actor:Player) -> Player:
    return PLAYER2 if actor == PLAYER1 else PLAYER1

def print_obs(o:Observation):
    for row in reversed(o.board):
        # We print '#' for our item, and 'O' for the opponent
        for x in row:
            c = ' '
            if x == 1:
                c = '#'
            elif x == 2:
                c = 'O'
            print(c, end=" ")
        print()
    print()

def initial_state(dims:tuple[int, int]) -> State:
    return State(np.zeros(dims, dtype=np.int8))

def state_to_observation(state: State, actor: np.int8) -> Observation:
    s = state.board
    o = s.copy()
    o[s == actor] = 1
    o[s != actor] = 2
    o[s == 0] = 0
    return Observation(o)


class Env():
    def __init__(
        self,
        dims:tuple[int,int]
    ):
        self._game_over = False
        self._winner = None
        self._moves = []
        self.state: State = initial_state(dims)

    def reset(self) -> None:
        self._game_over = False
        self._winner = None
        self._moves = []
        self.state = initial_state(self.state.board.shape)

    def observe(self, actor: np.int8) -> Observation:
        return state_to_observation(self.state, actor)

    def game_over(self) -> bool:
        return self._game_over

    def winner(self) -> Player | None:
        return self._winner

    def dims(self) -> tuple[int, int]:
        return self.state.board.shape

    def legal_mask(self) -> np.ndarray[Any, np.dtype[np.bool_]]:
        return self.state.board[-1] == 0

    def legal_actions(self) -> list[Action]:
        return [Action(i) for i in range(self.dims()[1]) if self.legal_mask()[i]]

    def step(self, a: Action, actor: Player) -> Reward:
        # 1. Assume the move is legal. Modify the game board to reflect the move.
        col = int(a)
        row = np.argmax(self.state.board[:, col] == 0)
        self.state.board[row, col] = actor

        # 1.5 Add the move to self._moves.
        self._moves.append((row, col))

        # 2. Check if the game is over. If so, set self._game_over and self._winner.
        if self.is_game_over(row, col):
            self._game_over = True
            self._winner = actor

        # 3. Return the reward for the agent.
        if self._game_over and self._winner == actor:
            return 1.0  # Agent wins
        elif self._game_over and self._winner != actor:
            return -1.0  # Agent loses
        else:
            return 0.0  # Game continues, no reward

    def is_game_over(self, row: int, col: int) -> bool:
        board = self.state.board

        # Check for four in a row horizontally
        horizontal_kernel = np.array([[1, 1, 1, 1]])
        if np.any(convolve2d(board, horizontal_kernel, mode='valid') >= 4):
            return True

        # Check for four in a row vertically
        vertical_kernel = np.array([[1], [1], [1], [1]])
        if np.any(convolve2d(board, vertical_kernel, mode='valid') >= 4):
            return True

        # Check for four in a row diagonally (top-left to bottom-right)
        diag_kernel1 = np.eye(4)
        if np.any(convolve2d(board, diag_kernel1, mode='valid') >= 4):
            return True

        # Check for four in a row diagonally (top-right to bottom-left)
        diag_kernel2 = np.fliplr(diag_kernel1)
        if np.any(convolve2d(board, diag_kernel2, mode='valid') >= 4):
            return True

        # Check for a tie (board is full)
        if np.all(board != 0):
            return True

        return False

    def check_line(self, idx: int, line: np.ndarray) -> bool:
        length = 4
        start = 0
        end = start + length
        while end <= line.size:
            if np.all(line[start:end] == line[idx]):
                return True
            start += 1
            end += 1
        return False

    
    def undo(self):
        if len(self._moves) == 0:
            return
        self.state.board[self._moves.pop()] = 0
        self._winner = None
        self._game_over = False
