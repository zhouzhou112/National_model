"""Chronological full-year blocking without temporal sampling."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TimeBlock:
    block_id: int
    hour_start: int
    hour_stop: int

    @property
    def hours(self) -> int:
        return self.hour_stop - self.hour_start


def make_time_blocks(total_hours: int, block_hours: int) -> list[TimeBlock]:
    if total_hours <= 0 or block_hours <= 0:
        raise ValueError("total_hours and block_hours must be positive")
    blocks = [
        TimeBlock(block_id=i, hour_start=start, hour_stop=min(start + block_hours, total_hours))
        for i, start in enumerate(range(0, total_hours, block_hours))
    ]
    covered = [hour for block in blocks for hour in range(block.hour_start, block.hour_stop)]
    if covered != list(range(total_hours)):
        raise AssertionError("Time blocks must cover every hour exactly once and in order")
    return blocks
