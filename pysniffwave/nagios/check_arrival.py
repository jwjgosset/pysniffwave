from datetime import datetime
from typing import List
from pysniffwave.nagios.arrival_metrics import LatestArrivalWorker, \
    StaleResults, TimelyResults
from dataclasses import dataclass
from pysniffwave.nagios.models import NagiosOutputCode, NagiosPerformance, \
    NagiosRange, NagiosResult, NagiosVerbose


@dataclass
class ArrivalThresholds:
    crit_range: str
    warn_range: str
    crit_time: str
    warn_time: str
    crit_count: str
    warn_count: str


def get_arrival_performance(
    stale_results: StaleResults,
    timely_results: TimelyResults,
    thresholds: ArrivalThresholds
) -> List[NagiosPerformance]:
    '''
    Assemble check results into performance data for Nagios XI

    Parameters
    ----------
    stale_results: StaleResults
        Object containing results of the check for stale channels

    timely_results: TimelyResults
        Object containing results of the check for timely arrival

    thresholds: ArrivalThresholds
        Object containing the various thresholds for the stale and timely
        arrival checks

    Returns
    -------
    List[NagiosPerformance]: Performance data in Nagios's standard format
    '''
    performances: List[NagiosPerformance] = []

    performances.append(NagiosPerformance(
        label='stale',
        value=stale_results.count,
        warning=float(thresholds.warn_range.strip(':')),
        critical=float(thresholds.crit_range.strip(':'))
    ))

    performances.append(NagiosPerformance(
        label='critical latency',
        value=timely_results.critical,
        critical=float(thresholds.crit_count)
    ))

    performances.append(NagiosPerformance(
        label='warning latency',
        value=timely_results.warning,
        warning=float(thresholds.warn_count)
    ))

    return performances


def get_details(
    arrival_stats: LatestArrivalWorker
) -> str:
    '''
    Extract the data from a LatestArrivalWorker and assembles it in a sorted
    string, to use as the details in a multiline NagiosCheckResult

    Parameters
    ----------

    arrival_stats: LatestArrivalWorker
        The object to extract data from
    '''
    stat_list = arrival_stats.sort_list()

    details = ''

    for stats in stat_list:
        details += f"{str(stats)}\n"

    return details


def get_arrival_results(
    current_time: datetime,
    thresholds: ArrivalThresholds,
    arrival_stats: LatestArrivalWorker
) -> NagiosResult:
    '''
    Takes arrival statistics and compares them to a set of thresholds to come
    up with a Nagios Check Result

    One threshold that is checked is the number of channels that are over an
    hour without a fresh packet. Each channel is also checked against a
    warning latency threshold and critical latency threshold, and those counts
    are compared to a threshold.

    Of these checks, the most elevated state is used for the Nagios Result
    '''
    stale_results = check_fresh_arrival(
        arrival_stats=arrival_stats,
        current_time=current_time,
        thresholds=thresholds
    )
    timely_results = check_timely_arrival(
        arrival_stats=arrival_stats,
        thresholds=thresholds
    )

    performances = get_arrival_performance(
        stale_results=stale_results,
        timely_results=timely_results,
        thresholds=thresholds
    )

    statuscode = stale_results.code

    if timely_results.code.value > statuscode.value:
        statuscode = timely_results.code

    if statuscode.value == 0:
        status = "OK"
    elif statuscode.value == 1:
        status = "WARNING"
    elif statuscode.value == 2:
        status = "CRITICAL"
    else:
        status = "UNKNOWN"

    summary = (f'{status} - {stale_results.count} channels stale,' +
               f'{timely_results.warning} channels with latency above' +
               f' {thresholds.warn_time}s, {timely_results.critical} ' +
               f'channels with latency above {thresholds.crit_time}s')

    details = get_details(arrival_stats=arrival_stats)

    return NagiosResult(
        summary=summary,
        verbose=NagiosVerbose.multiline,
        status=statuscode,
        performances=performances,
        details=details
    )


def check_fresh_arrival(
        arrival_stats: LatestArrivalWorker,
        current_time: datetime,
        thresholds: ArrivalThresholds
) -> StaleResults:
    '''
    Check the number of stale (older than 1 hour) channels

    Parameters
    ----------
    current_time: datetime
        The time to compare the start timestamps against

    crit_range: str
        The number of stale channels required to return a CRITICAL state

    warn_range: str
        The number of stale channels required to return a WARNING state

    Returns
    -------
    StaleResults: Object containing the resulting NagiosOutputCode and the
    count of stale channels
    '''
    stale_channels = 0
    for channel in arrival_stats:
        channel_age = current_time - (arrival_stats[channel]).start_time
        if channel_age.total_seconds() > 3600:
            stale_channels += 1

    if NagiosRange(thresholds.crit_range).in_range(stale_channels):
        state = NagiosOutputCode.critical
    elif NagiosRange(thresholds.warn_range).in_range(stale_channels):
        state = NagiosOutputCode.warning
    else:
        state = NagiosOutputCode.ok

    return StaleResults(
        code=state,
        count=stale_channels
        )


def check_timely_arrival(
        arrival_stats: LatestArrivalWorker,
        thresholds: ArrivalThresholds
) -> TimelyResults:
    '''
    Parameters
    ----------
    crit_time: float
        The limit on latency in seconds before a channel is considered for
        the critical threshold

    warn_time: float
        The limit on latency in seconds before a channel is considered for
        the warning threshold

    crit_count: str
        The number of required channels with latency above the crit_time
        threshold for the check to return a critical state

    warn_count: str
        The number of required channels with latency above the warn_time
        threshold for the check to return a warning state

    Returns
    -------
    TimelyResults: Object containing the resulting NagiosOutputCode and
    counts of the critical and warning channels
    '''
    critical = 0
    warning = 0

    # Count the channels in the critical and warning latency thresholds
    for channel in arrival_stats:
        if NagiosRange(thresholds.crit_time).in_range(
                arrival_stats[channel].total_latency()):
            critical += 1
        if NagiosRange(thresholds.warn_time).in_range(
                arrival_stats[channel].total_latency()):
            warning += 1

    # Decide on the state
    if NagiosRange(thresholds.crit_count).in_range(critical):
        state = NagiosOutputCode.critical
    elif NagiosRange(thresholds.warn_count).in_range(warning):
        state = NagiosOutputCode.warning
    else:
        state = NagiosOutputCode.ok

    return TimelyResults(
        code=state,
        critical=critical,
        warning=warning)
