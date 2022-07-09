from datetime import datetime
from typing import List
from pysniffwave.nagios.arrival_metrics import LatestArrivalWorker, \
    StaleResults, TimelyResults
from dataclasses import dataclass
from pysniffwave.nagios.models import NagiosPerformance, NagiosResult, \
    NagiosVerbose


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
    current_time = datetime.now()
    stale_results = arrival_stats.check_fresh_arrival(
        current_time=current_time,
        thresholds=thresholds
    )
    timely_results = arrival_stats.check_timely_arrival(
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
