
import random

def _safe_apply(a, op, b):
    if op == "+": return a + b
    if op == "-": return a - b
    if op == "*": return a * b
    if op == "/":
        if b == 0 or a % b != 0: return None
        return a // b
    return None

# Sve dostizne vrijednosti za SREDNJE (n op n, brojevi 0-5, ukljucujuci negativne)
_MEDIUM_TARGETS = [
    -5, -4, -3, -2, -1,
     0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10,
    12, 15, 16, 20, 25
]

# Sve dostizne vrijednosti za TESKO ((n op n) op n, lijevo na desno, ukljucujuci negativne)
_HARD_TARGETS = [
    -25, -20, -16, -15, -12, -10, -9, -8, -7, -6, -5, -4, -3, -2, -1,
      0,   1,   2,   3,   4,   5,   6,   7,   8,   9, 10, 11, 12, 13,
     14,  15,  16,  17,  18,  19,  20,  21,  22,  23, 24, 25, 26, 27,
     28,  29,  30,  32,  35,  36,  40,  45,  48,  50, 60, 64, 75, 80,
    100, 125
]

def generate_target(difficulty: str):
    """Vraca garantirano dostizan ciljni broj za zadanu tezinu."""
    difficulty = str(difficulty).strip().upper()

    if difficulty == "LAGANO":
        return None

    if difficulty == "SREDNJE":
        return random.choice(_MEDIUM_TARGETS)

    if difficulty == "TESKO":
        return random.choice(_HARD_TARGETS)

    # Fallback
    return random.randint(0, 10)