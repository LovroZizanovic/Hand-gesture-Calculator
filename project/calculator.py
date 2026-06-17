"""
calculator.py - Logika kalkulatora, state machine i game mode generiranje izraza
"""

from enum import Enum, auto
import time
from challenge import generate_target, _safe_apply

class GameDifficulty(Enum):
    EASY   = "LAGANO"
    MEDIUM = "SREDNJE"
    HARD   = "TESKO"

class GameState(Enum):
    PLAYING   = auto()
    GAME_OVER = auto()

class InputState(Enum):
    NUM1 = 1
    OP1  = 2
    NUM2 = 3
    OP2  = 4
    NUM3 = 5

class GameSession:
    HOLD_DURATION = 1.5
    FREEZE_DURATION = 1.5  

    def __init__(self, difficulty: GameDifficulty):
        self.difficulty = difficulty
        self.time_limit = {
            GameDifficulty.EASY: None,
            GameDifficulty.MEDIUM: 25.0,
            GameDifficulty.HARD: 20.0
        }[difficulty]
        self.score = 0
        self.history = []
        self.freeze_until = None
        self.final_expr_snapshot = ""
        self.restart()

    def restart(self):
        self.score = 0
        self.game_state = GameState.PLAYING
        self.fail_reason = ""
        self.freeze_until = None
        self.final_expr_snapshot = ""
        self._start_new_round()

    def _start_new_round(self):
        self.target = generate_target(self.difficulty.value)
        self.timer_start = time.time()
        self.input_state = InputState.NUM1
        
        self.n1 = None
        self.op1 = None
        self.n2 = None
        self.op2 = None
        self.n3 = None
        
        self._hold_start = None
        self._hold_value = None

    def reset_round_timer(self):
        self.timer_start = time.time()

    def time_remaining(self):
        if self.time_limit is None or self.timer_start is None:
            return self.time_limit
        if self.freeze_until is not None:
            return self.time_limit
        elapsed = time.time() - self.timer_start
        return max(0.0, self.time_limit - elapsed)

    def hold_progress(self):
        if self.freeze_until is not None or self._hold_start is None:
            return 0.0
        elapsed = time.time() - self._hold_start
        return min(elapsed / self.HOLD_DURATION, 1.0)

    def update(self, fingers: int, gesture: str):
        if self.freeze_until is not None:
            if time.time() >= self.freeze_until:
                self.freeze_until = None
                self.final_expr_snapshot = ""
                self._start_new_round()
                self.reset_round_timer()
            return self._status()

        if self.game_state != GameState.PLAYING:
            return self._status()

        if self.time_limit is not None and self.time_remaining() <= 0:
            self.game_state = GameState.GAME_OVER
            self.fail_reason = "Isteklo vrijeme!"
            return self._status()

        expected_val = None
        if self.input_state in (InputState.NUM1, InputState.NUM2, InputState.NUM3):
            expected_val = fingers if fingers != -1 else None
        elif self.input_state in (InputState.OP1, InputState.OP2):
            expected_val = gesture

        if expected_val is None:
            self._hold_start = None
            self._hold_value = None
            return self._status()

        if self._hold_value != expected_val:
            self._hold_value = expected_val
            self._hold_start = time.time()
        elif time.time() - self._hold_start >= self.HOLD_DURATION:
            self._advance_state(expected_val)

        return self._status()

    def _advance_state(self, val):
        if self.input_state == InputState.NUM1:
            self.n1 = val
            self.input_state = InputState.OP1
        elif self.input_state == InputState.OP1:
            self.op1 = val
            self.input_state = InputState.NUM2
        elif self.input_state == InputState.NUM2:
            self.n2 = val
            if self.difficulty == GameDifficulty.HARD:
                self.input_state = InputState.OP2
            else:
                self._evaluate()
        elif self.input_state == InputState.OP2:
            self.op2 = val
            self.input_state = InputState.NUM3
        elif self.input_state == InputState.NUM3:
            self.n3 = val
            self._evaluate()

        self._hold_start = None
        self._hold_value = None

    def _evaluate(self):
        res1 = _safe_apply(self.n1, self.op1, self.n2)
        final_res = res1
        
        if self.difficulty == GameDifficulty.HARD and res1 is not None:
            final_res = _safe_apply(res1, self.op2, self.n3)

        expr_str = self._build_expr_str(False)

        if final_res is None:
            if self.difficulty == GameDifficulty.EASY:
                self.final_expr_snapshot = f"{expr_str} = Greska"
                self.history.append(self.final_expr_snapshot)
                self.freeze_until = time.time() + self.FREEZE_DURATION
            else:
                self.game_state = GameState.GAME_OVER
                self.fail_reason = "Neispravan matematicki izraz!"
            return

        if self.difficulty == GameDifficulty.EASY:
            self.final_expr_snapshot = f"{expr_str} = {final_res}"
            self.history.append(self.final_expr_snapshot)
            self.freeze_until = time.time() + self.FREEZE_DURATION
        else:
            if final_res == self.target:
                self.score += 1
                # POPRAVLJENO: Maknuta kvačica zbog OpenCV renderiranja
                self.final_expr_snapshot = f"{expr_str} = {final_res} (TOCNO)"
                self.history.append(self.final_expr_snapshot)
                self.freeze_until = time.time() + self.FREEZE_DURATION
            else:
                self.game_state = GameState.GAME_OVER
                self.fail_reason = f"Krivo: {expr_str} = {final_res}"

    def _build_expr_str(self, include_placeholders=True):
        parts = []
        parts.append(str(self.n1) if self.n1 is not None else ("_" if include_placeholders else ""))
        
        if self.input_state.value > InputState.NUM1.value or self.op1 is not None:
            parts.append(self.op1 if self.op1 is not None else "?")
            
        if self.input_state.value > InputState.OP1.value or self.n2 is not None:
            parts.append(str(self.n2) if self.n2 is not None else ("_" if include_placeholders else ""))
            
        if self.difficulty == GameDifficulty.HARD:
            if self.input_state.value > InputState.NUM2.value or self.op2 is not None:
                parts.append(self.op2 if self.op2 is not None else "?")
            if self.input_state.value > InputState.OP2.value or self.n3 is not None:
                parts.append(str(self.n3) if self.n3 is not None else ("_" if include_placeholders else ""))
                
        return " ".join(p for p in parts if p)

    def _status(self):
        current_expr = self.final_expr_snapshot if self.freeze_until is not None else self._build_expr_str(True)
        instruction = "Pricekaj trenutak..." if self.freeze_until is not None else ("Gradi izraz: Unesi " + ("BROJ (0-5 prstiju)" if self.input_state in (InputState.NUM1, InputState.NUM2, InputState.NUM3) else "OPERACIJU (Gesta)"))

        return {
            "game_state": self.game_state,
            "difficulty_name": self.difficulty.value,
            "target": self.target,
            "expression_str": current_expr,
            "score": self.score,
            "time_remaining": self.time_remaining(),
            "time_limit": self.time_limit,
            "hold_progress": self.hold_progress(),
            "instruction": instruction,
            "history": self.history,
            "fail_reason": getattr(self, "fail_reason", ""),
            "expected_input": self.input_state.name,
            "is_frozen": self.freeze_until is not None
        }