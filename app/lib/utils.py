# pyright: reportExplicitAny=false
from typing import Any, final, override


@final
class _MissingSentinel:
    __slots__ = ()

    @override
    def __eq__(self, other: object) -> bool:
        return False

    def __bool__(self) -> bool:
        return False

    @override
    def __hash__(self) -> int:
        return 0

    @override
    def __repr__(self):
        return "..."


MISSING: Any = _MissingSentinel()
