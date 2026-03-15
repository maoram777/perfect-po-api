"""
Keepa timestamp conversion to Unix epoch.

Keepa returns timestamps as minutes since 2011-01-01 00:00:00 UTC.
Unix epoch is seconds since 1970-01-01 00:00:00 UTC.
Offset from Unix epoch to Keepa epoch: 21564000 minutes.

  epoch_seconds = (keepa_minutes + 21564000) * 60
  epoch_milliseconds = (keepa_minutes + 21564000) * 60000
"""
import datetime
from typing import Optional

# Minutes from Unix epoch (1970-01-01) to Keepa epoch (2011-01-01 00:00:00 UTC)
KEEPA_EPOCH_OFFSET_MINUTES = 21564000


def keepa_minutes_to_epoch_seconds(keepa_minutes: Optional[int]) -> Optional[int]:
    """Convert Keepa time (minutes since 2011-01-01) to Unix epoch seconds."""
    if keepa_minutes is None:
        return None
    return (int(keepa_minutes) + KEEPA_EPOCH_OFFSET_MINUTES) * 60


def keepa_minutes_to_epoch_milliseconds(keepa_minutes: Optional[int]) -> Optional[int]:
    """Convert Keepa time (minutes since 2011-01-01) to Unix epoch milliseconds."""
    if keepa_minutes is None:
        return None
    return (int(keepa_minutes) + KEEPA_EPOCH_OFFSET_MINUTES) * 60000


if __name__ == "__main__":
    # Example Keepa Time in Minutes value
    keepa_time_minutes = 26000000
    epoch_seconds = keepa_minutes_to_epoch_seconds(keepa_time_minutes)
    epoch_milliseconds = keepa_minutes_to_epoch_milliseconds(keepa_time_minutes)
    human_readable_date = datetime.datetime.fromtimestamp(epoch_seconds)
    print(f"Keepa Time: {keepa_time_minutes}")
    print(f"Epoch Seconds: {epoch_seconds}")
    print(f"Epoch Milliseconds: {epoch_milliseconds}")
    print(f"Human Readable Date: {human_readable_date}")
