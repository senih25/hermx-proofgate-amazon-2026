"""SM-2 spaced-repetition scheduling.

Pure functions, no I/O. Given a card's current state and a recall grade
(0-5), returns the next interval, easiness factor, and repetition count.
Reference: Piotr Wozniak's SuperMemo-2 algorithm.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

MIN_EF = 1.3  # SM-2 lower bound on easiness; below this cards churn forever


@dataclass
class Schedule:
    repetitions: int
    interval_days: int
    easiness: float
    due: date


def review(
    grade: int,
    repetitions: int,
    interval_days: int,
    easiness: float,
    today: date | None = None,
) -> Schedule:
    """Advance one card after a review.

    grade: 0-5 (0-2 = fail/forgot, 3-5 = recalled with effort..perfect).
    A failing grade resets the repetition streak but keeps the (penalised)
    easiness factor so genuinely hard cards stay hard.
    """
    if not 0 <= grade <= 5:
        raise ValueError(f"grade must be 0-5, got {grade}")
    today = today or date.today()

    if grade < 3:
        repetitions = 0
        interval_days = 1
    else:
        if repetitions == 0:
            interval_days = 1
        elif repetitions == 1:
            interval_days = 6
        else:
            interval_days = round(interval_days * easiness)
        repetitions += 1

    # EF update applies on every review, pass or fail.
    easiness = easiness + (0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02))
    easiness = max(MIN_EF, easiness)

    return Schedule(
        repetitions=repetitions,
        interval_days=interval_days,
        easiness=round(easiness, 4),
        due=today + timedelta(days=interval_days),
    )


def _demo() -> None:
    d0 = date(2026, 1, 1)
    # Perfect recalls grow the interval; EF drifts up from the 2.5 default.
    s = review(5, 0, 0, 2.5, d0)
    assert s.repetitions == 1 and s.interval_days == 1, s
    s = review(5, s.repetitions, s.interval_days, s.easiness, d0)
    assert s.repetitions == 2 and s.interval_days == 6, s
    s = review(5, s.repetitions, s.interval_days, s.easiness, d0)
    assert s.interval_days > 6 and s.easiness > 2.5, s

    # A lapse resets the streak to a 1-day interval and never lets EF fall
    # below the floor.
    lapse = review(0, 8, 40, 1.3, d0)
    assert lapse.repetitions == 0 and lapse.interval_days == 1, lapse
    assert lapse.easiness == MIN_EF, lapse

    # Grade bounds are enforced.
    for bad in (-1, 6):
        try:
            review(bad, 0, 0, 2.5, d0)
        except ValueError:
            pass
        else:
            raise AssertionError(f"grade {bad} should have raised")

    print("srs self-check ok")


if __name__ == "__main__":
    _demo()
