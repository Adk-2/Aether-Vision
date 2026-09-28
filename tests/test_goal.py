from datetime import datetime
import pytest
from planning import Goal, PlanningError


@pytest.mark.parametrize("target", ["", "   ", "\t\n"])
def test_blank_goal_target_is_rejected(target):
    with pytest.raises(PlanningError, match="Goal target"):
        Goal("find", target, 1, datetime(2026, 8, 26))


def test_nonempty_target_is_preserved():
    goal = Goal("find", " cup_001 ", 1, datetime(2026, 8, 26))
    assert goal.target_object == " cup_001 "
