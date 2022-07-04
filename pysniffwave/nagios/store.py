import pathlib
from pysniffwave.sniffwave.parser import Channel
import logging
from typing import List, Union


def get_arrival_file(
    directory: str = '/data/sniffwave',
    filename: str = 'latest_arrival.txt'
) -> pathlib.Path:
    file_path = pathlib.Path(directory).joinpath(filename)

    # Create the file if it doesn't exist
    if not file_path.exists():
        file_path.touch(mode=0o644)
        logging.warning(f"File {str(file_path)} did not exist, created")
    # Open the file in read/write mode
    return file_path


def store_latest_timestamp(
    file_path: pathlib.Path,
    channel_stats: Union[List[Channel], Channel]
):
    # Assemble data in string format

    # Ensure that channel_stats is iterable
    if isinstance(channel_stats, Channel):
        channel_stats = [channel_stats]

    with open(file_path, mode='r') as file:
        # Read existing lines from file
        lines = file.readlines()
        for channel in channel_stats:
            # Convert scnl to string
            scnl = (f"{channel['network']}.{channel['station']}." +
                    f"{channel['location']}.{channel['channel']}")
            # Add timestamp to string
            new_line = f"{scnl},{channel['start_time']}\n"

            logging.debug(new_line)

            # If a line already exists with the same scnl, replace it
            scnl_found = False
            for i in range(len(lines)):
                if scnl in lines[i]:
                    lines[i] = new_line
                    scnl_found = True
                    logging.debug(f"Found matching line: {lines[i]}")
                    break

            # If the scnl is not in file, append a new line
            if not scnl_found:
                lines.append(new_line)
                logging.debug("Appending new line")

    # Write the updated lines to the file
    with open(file_path, mode='w') as file:
        file.write(''.join(lines))
