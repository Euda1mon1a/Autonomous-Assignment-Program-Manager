import enum


class LeaveStatus(str, enum.Enum):
    ANTICIPATED = "anticipated"
    CONFIRMED = "confirmed"
    DENIED = "denied"
