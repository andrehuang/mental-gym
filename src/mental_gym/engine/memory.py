"""SM-2 spaced repetition scheduler adapted for conceptual knowledge."""

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class SM2Result:
    """Result of SM-2 calculation."""
    interval: float  # days until next review
    easiness: float  # updated easiness factor
    repetitions: int  # consecutive correct count
    next_review: str  # ISO datetime string


def sm2_update(quality: float, interval: float, easiness: float,
               repetitions: int) -> SM2Result:
    """Run SM-2 algorithm on a single review.

    Args:
        quality: Score 1-5 (from exercise overall_score). 3+ is "passing".
        interval: Current interval in days.
        easiness: Current easiness factor (>= 1.3).
        repetitions: Current count of consecutive correct reviews.

    Returns:
        SM2Result with updated parameters.
    """
    # Normalize quality to 0-5 scale for SM-2 (our scores are 1-5)
    q = quality  # Already 1-5

    if q >= 3.0:
        # Correct response
        if repetitions == 0:
            new_interval = 1.0
        elif repetitions == 1:
            new_interval = 3.0
        else:
            new_interval = interval * easiness

        new_repetitions = repetitions + 1
    else:
        # Incorrect / poor response — reset
        new_interval = 0.5  # Review again soon (12 hours)
        new_repetitions = 0

    # Update easiness factor
    # SM-2 formula: EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    new_easiness = easiness + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    new_easiness = max(1.3, new_easiness)  # Floor at 1.3

    # Cap interval at 180 days (6 months) for domain knowledge
    new_interval = min(new_interval, 180.0)

    # Calculate next review datetime
    next_dt = datetime.utcnow() + timedelta(days=new_interval)

    return SM2Result(
        interval=round(new_interval, 1),
        easiness=round(new_easiness, 2),
        repetitions=new_repetitions,
        next_review=next_dt.isoformat(),
    )


def update_mastery(current_mastery: float, overall_score: float,
                   alpha: float = 0.3) -> float:
    """Update topic mastery using exponential moving average.

    Args:
        current_mastery: Current mastery level (0-1).
        overall_score: Exercise overall score (1-5).
        alpha: Weight of new score vs history.

    Returns:
        New mastery level (0-1).
    """
    normalized = overall_score / 5.0
    new_mastery = alpha * normalized + (1 - alpha) * current_mastery
    return round(min(1.0, max(0.0, new_mastery)), 3)


def mastery_to_difficulty(mastery: float) -> int:
    """Map mastery level to difficulty level (1-6)."""
    if mastery < 0.2:
        return 1
    elif mastery < 0.4:
        return 2
    elif mastery < 0.6:
        return 3
    elif mastery < 0.75:
        return 4
    elif mastery < 0.9:
        return 5
    else:
        return 6
