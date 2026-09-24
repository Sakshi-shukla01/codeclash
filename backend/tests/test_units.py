"""
Unit tests: pure logic (Elo, matchmaking, security). Postgres/Redis ki zaroorat nahi.
Chalao:  cd backend && pytest -q
"""
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.services.elo import expected_score, rating_changes
from app.services.matchmaker import allowed_range, find_pairs


# ------------------------------------------------------------------ Elo
def test_equal_ratings_expected_half():
    assert expected_score(1200, 1200) == 0.5


def test_equal_ratings_win_gives_16():
    assert rating_changes(1200, 1200, 1.0) == (16, -16)


def test_upset_win_gives_more_points():
    underdog_win, _ = rating_changes(1000, 1400, 1.0)
    favourite_win, _ = rating_changes(1400, 1000, 1.0)
    assert underdog_win > favourite_win


def test_draw_between_equals_is_zero():
    assert rating_changes(1500, 1500, 0.5) == (0, 0)


def test_changes_are_zero_sum():
    a, b = rating_changes(1337, 1111, 0.0)
    assert a + b == 0


# ------------------------------------------------------------------ Matchmaking
def test_range_grows_with_wait_time():
    assert allowed_range(0) == 100
    assert allowed_range(10) == 200
    assert allowed_range(1000) == 500  # cap


def test_pairs_close_ratings():
    now = 1000.0
    players = [(1, 1200, now), (2, 1250, now), (3, 1900, now)]
    assert find_pairs(players, now) == [(1, 2)]


def test_far_ratings_not_paired_immediately():
    now = 1000.0
    assert find_pairs([(1, 1000, now), (2, 1400, now)], now) == []


def test_far_ratings_paired_after_waiting():
    now = 1000.0
    players = [(1, 1000, now - 60), (2, 1400, now)]  # player 1 ne 60s wait kiya
    assert find_pairs(players, now) == [(1, 2)]


def test_each_player_matched_once():
    now = 0.0
    players = [(i, 1200 + i, now) for i in range(5)]
    pairs = find_pairs(players, now)
    ids = [u for p in pairs for u in p]
    assert len(ids) == len(set(ids)) == 4


# ------------------------------------------------------------------ Security
def test_password_hashing():
    h = hash_password("secret123")
    assert h != "secret123"
    assert verify_password("secret123", h)
    assert not verify_password("wrong", h)


def test_jwt_roundtrip():
    assert decode_access_token(create_access_token(42)) == 42
    assert decode_access_token("garbage.token.here") is None
