from datetime import datetime
import click
import logging
from pysniffwave.config import LogLevels
from pysniffwave.nagios.arrival_metrics import LatestArrivalWorker
from pysniffwave.nagios.check_arrival import ArrivalThresholds, \
    get_arrival_results
import sys


@click.command()
@click.option(
    '--critical-stale',
    help=("The number of channels that must be stale to trigger a " +
          "critical state")
)
@click.option(
    '--warning-stale',
    help=("The number of channels that must be stale to trigger a " +
          "warning state")
)
@click.option(
    '--critical-latency',
    help=("The latency threshold a channel must exceed to contribute to " +
          "the count of critical channels")
)
@click.option(
    '--warning-latency',
    help=("The latency threshold a channel must exceed to contribute to " +
          "the count of warning channels")
)
@click.option(
    '--critical-count',
    help=("The number of channels abover the critical latency threshold to " +
          "trigger a critical state")
)
@click.option(
    '--warning-count',
    help=("The number of channels abover the warning latency threshold to " +
          "trigger a warning state")
)
@click.option(
    '--arrival-file',
    help=("Path to the file containing the latest arrival statistics")
)
@click.option(
    '--log-levels',
    type=click.Choice([v.value for v in LogLevels]),
    help="Log level",
    default=LogLevels.WARNING
)
def main(
    critical_stale: str,
    warning_stale: str,
    critical_latency: str,
    warning_latency: str,
    critical_count: str,
    warning_count: str,
    arrival_file: str,
    log_level: str
):
    # Set up logging format
    logging.basicConfig(
            format='%(asctime)s:%(levelname)s:%(message)s',
            datefmt="%Y-%m-%d %H:%M:%S",
            level=log_level)

    # Initialize thresholds
    thresholds = ArrivalThresholds(
        crit_range=critical_stale,
        warn_range=warning_stale,
        crit_time=critical_latency,
        warn_time=warning_latency,
        crit_count=critical_count,
        warn_count=warning_count
    )

    # Load in arrival stats
    arrival_stats = LatestArrivalWorker(
        filepath=arrival_file,
        changes=-1
    )
    current_time = datetime.now()

    # Check the arrival stats against the threshold
    results = get_arrival_results(
        current_time=current_time,
        thresholds=thresholds,
        arrival_stats=arrival_stats
    )

    # Print the results
    print(results)

    # Exit with nagios output code
    sys.exit(results.status.value)


if __name__ == '__main__':
    main()
