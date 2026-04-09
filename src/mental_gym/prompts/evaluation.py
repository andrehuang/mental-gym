"""Exercise type registry — maps slugs to exercise type instances."""

from mental_gym.exercises.explain import ExplainExercise
from mental_gym.exercises.predict import PredictExercise
from mental_gym.exercises.connect import ConnectExercise
from mental_gym.exercises.defend import DefendExercise
from mental_gym.exercises.teach import TeachExercise
from mental_gym.exercises.write import WriteExercise


EXERCISE_TYPES = {
    "explain": ExplainExercise(),
    "predict": PredictExercise(),
    "connect": ConnectExercise(),
    "defend": DefendExercise(),
    "teach": TeachExercise(),
    "write": WriteExercise(),
}


def get_exercise_type(slug: str):
    """Get exercise type instance by slug."""
    if slug not in EXERCISE_TYPES:
        raise ValueError(f"Unknown exercise type: {slug}. Available: {list(EXERCISE_TYPES.keys())}")
    return EXERCISE_TYPES[slug]
