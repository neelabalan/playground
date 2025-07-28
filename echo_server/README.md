### Without `epoll`

```
❯ uvx python3.11 bench.py --port=8080 --connections=20

Benchmark Results:
total_requests: 82755
mean_time: 0.0024099716758005465
median_time: 0.0008744130000195582
p95_time: 0.0010825259998455295
p99_time: 0.0011999826003375347
min_time: 0.00044339299984130776
max_time: 14.288082373999714
requests_per_second: 8275.5
```


### With `epoll` enabled

```
❯ uvx python3.11 bench.py --port=8080 --connections=20

Benchmark Results:
total_requests: 93111
mean_time: 0.0017249472171289835
median_time: 0.001673906000178249
p95_time: 0.0021413255997686067
p99_time: 0.0024433410802885192
min_time: 0.0008527019999746699
max_time: 0.005380378999689128
requests_per_second: 9311.1
```