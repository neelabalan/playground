import os
import datetime


def time_delta(t1, t2):
    time_format = '%a %d %b %Y %H:%M:%S %z'
    return str(
        int(
            abs(
                (datetime.datetime.strptime(t1, time_format) - 
                datetime.datetime.strptime(t2, time_format)).total_seconds())
            )
    )

if __name__ == '__main__':
    t = int(input())
    for t_itr in range(t):
        t1 = input()
        t2 = input()
        delta = time_delta(t1, t2)
        print(delta + '\n')
