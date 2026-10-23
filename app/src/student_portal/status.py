"""Статус студента (вимога Р-18)."""

from enum import StrEnum

from student_portal.exceptions import InvalidTransitionError


class Status(StrEnum):
    ACTIVE = "навчається"
    ON_LEAVE = "академвідпустка"
    EXPELLED = "відрахований"
    GRADUATED = "випускник"


class Event(StrEnum):
    TAKE_LEAVE = "надати академвідпустку"
    RETURN = "повернути з академвідпустки"
    EXPEL = "відрахувати"
    REINSTATE = "поновити"
    GRADUATE = "випустити"


TRANSITIONS: dict[tuple[Status, Event], Status] = {
    (Status.ACTIVE, Event.TAKE_LEAVE): Status.ON_LEAVE,
    (Status.ACTIVE, Event.GRADUATE): Status.GRADUATED,
    (Status.ON_LEAVE, Event.RETURN): Status.ACTIVE,
    (Status.EXPELLED, Event.REINSTATE): Status.ACTIVE,
}


def next_status(current: Status, event: Event, *, has_debts: bool = False) -> Status:
    """Повертає новий статус або відхиляє неможливу подію."""
    if event is Event.EXPEL and current is not Status.EXPELLED:
        return Status.EXPELLED
    if event is Event.GRADUATE and has_debts:
        raise InvalidTransitionError("не можна випустити студента з оцінками Fx")
    try:
        return TRANSITIONS[current, event]
    except KeyError:
        raise InvalidTransitionError(
            f"подія «{event}» неможлива для статусу «{current}»"
        ) from None
