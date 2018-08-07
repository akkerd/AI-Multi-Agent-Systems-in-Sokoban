import argparse
import memory
from clients.main import main

parser = argparse.ArgumentParser(description='Simple client based on state-space graph search.')
parser.add_argument('--max_memory', metavar='<MB>', type=float, default=2048.0,
                    help='The maximum memory usage allowed in MB (soft limit, default 512).')
parser.add_argument('-s', '--strategy', type=str, default='BFS',
                    help='The strategy to use for the algorithm (default BFS)')
parser.add_argument('-g', '--subgoals', action='store', default=False, const="default", nargs="?",
                    help="Whether to use sub-goal separation, and which version of it or not.")
parser.add_argument('-d', '--debug', action='store_true',
                    help="If the flag is not present, the exceptions will be caught by the client, if it"
                         "is present, they will be shown in the terminal.")
args = parser.parse_args()

# Set max memory usage allowed (soft limit).
memory.max_usage = args.max_memory

# Run client.
main(**vars(args))
