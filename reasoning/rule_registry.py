"""Registry for independently replaceable inference rules."""

from .exceptions import RuleRegistrationError
from .rule import Rule


class RuleRegistry:
    """Own the ordered collection of registered rules."""

    def __init__(self) -> None:
        self._rules: list[Rule] = []

    def register(self, rule: Rule) -> None:
        """Register one rule for subsequent inference."""
        if not isinstance(rule, Rule):
            raise RuleRegistrationError("Registered rules must implement Rule")
        self._rules.append(rule)

    def all_rules(self) -> list[Rule]:
        """Return registered rules in registration order."""
        return list(self._rules)
