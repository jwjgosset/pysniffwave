from datetime import datetime
from pysniffwave.nagios.store import LatestArrivalWorker
from pysniffwave.nagios.models import NagiosRange, NagiosOutputCode


def check_fresh_arrival(
    worker: LatestArrivalWorker,
    current_time: datetime,
    crit_range: str,
    warn_range: str
) -> NagiosOutputCode:
    stale_channels = 0
    for channel in worker.channels:
        channel_age = current_time - (worker.channels[channel]).start_time
        if channel_age.total_seconds() > 3600:
            stale_channels += 1

    if NagiosRange(crit_range).in_range(stale_channels):
        state = NagiosOutputCode.critical
    elif NagiosRange(warn_range).in_range(stale_channels):
        state = NagiosOutputCode.warning
    else:
        state = NagiosOutputCode.ok

    return state
