from __future__ import annotations

from .stack_sizes import get_stack_size

SHULKER_SLOTS = 27


def format_quantity(amount: int, item_name: str) -> str:
    if amount <= 0:
        return "0"

    stack_size = get_stack_size(item_name)
    shulker_size = SHULKER_SLOTS * stack_size

    shulkers, remainder = divmod(amount, shulker_size)
    stacks, items = divmod(remainder, stack_size)

    parts = []
    if shulkers:
        parts.append(f"{shulkers} shulker" + ("s" if shulkers != 1 else ""))
    if stacks:
        parts.append(f"{stacks} stack" + ("s" if stacks != 1 else ""))
    if items or not parts:
        parts.append(f"{items} item" + ("s" if items != 1 else ""))

    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " and " + parts[-1]


def format_int(n: int) -> str:
    return f"{n:,}"
