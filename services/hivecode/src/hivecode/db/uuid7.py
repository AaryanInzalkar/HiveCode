"""UUIDv7 generation utility."""

import os
import time
from uuid import UUID

# Custom UUIDv7 implementation (time-ordered)
# Format: 48-bit unix_ts_ms | 4-bit ver | 12-bit rand_a | 2-bit var | 62-bit rand_b

_last_timestamp = 0
_last_counter = 0


def uuid7() -> UUID:
    """Generate a UUIDv7 (time-ordered)."""
    global _last_timestamp, _last_counter

    timestamp_ms = int(time.time() * 1000)

    if timestamp_ms == _last_timestamp:
        _last_counter = (_last_counter + 1) & 0xFFF  # 12-bit counter
    else:
        _last_timestamp = timestamp_ms
        _last_counter = int.from_bytes(os.urandom(2), "big") & 0xFFF

    # 48-bit timestamp
    ts = timestamp_ms & 0xFFFFFFFFFFFF

    # 12-bit counter with random high bit
    rand_a = (0x8000 | _last_counter) & 0xFFFF

    # 62-bit random
    rand_b = int.from_bytes(os.urandom(8), "big") & 0x3FFFFFFFFFFFFFFF

    # Compose: ts(48) | ver(4)=0111 | rand_a(12) | var(2)=10 | rand_b(62)
    value = (ts << 80) | (0x7 << 76) | (rand_a << 64) | (0x2 << 62) | rand_b

    return UUID(int=value)
