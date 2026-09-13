from dataclasses import dataclass


@dataclass(frozen=True)
class RemediationDecision:
    enter_skill_id: object | None = None
    enter_reason: str | None = None
    exit_to_target: bool = False
