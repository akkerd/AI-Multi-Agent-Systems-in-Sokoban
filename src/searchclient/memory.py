'''
    Author: Mathias Kaas-Olsen
    Date:   2016-02-11
'''


from math import inf
import psutil


max_usage = inf
_process = psutil.Process()


def get_usage() -> 'float':
    ''' Returns memory usage of current process in MB. '''
    global _process
    return _process.memory_info().rss / (1024*1024)

