"""
Elo rating system (chess wala).

Idea: kamzor player agar strong player ko hara de, toh use zyada points milte hain.
  Expected score  E_a = 1 / (1 + 10^((R_b - R_a) / 400))
  Rating change   Δ_a = K × (S_a − E_a)       S_a: jeet=1, draw=0.5, haar=0
"""
K_FACTOR = 32


def expected_score(rating_a: int, rating_b: int) -> float:
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))


def rating_changes(rating_a: int, rating_b: int, score_a: float, k: int = K_FACTOR) -> tuple[int, int]:
    """Return (change_for_a, change_for_b). Zero-sum hai: jitna A ko mila, utna B ka gaya."""
    delta_a = round(k * (score_a - expected_score(rating_a, rating_b)))
    return delta_a, -delta_a
