## Benchmark read/write in SQLite vs simple file storage

### Observations

In the first run, writing to SQLite took approximately 4.43 seconds, while writing to the file system took about 2.74 seconds. In subsequent runs, the time taken to write to SQLite decreased to around 3.76 seconds, while the time taken to write to the file system remained relatively constant at around 2.7 seconds. This suggests that SQLite's performance improves with repeated use, possibly due to caching or other optimization mechanisms.

The read operations from the file system were initially slower than from SQLite, taking about 2.24 seconds compared to SQLite's 1.48 seconds. However, in subsequent runs, the time taken to read from the file system decreased dramatically to around 0.43 seconds, while the time taken to read from SQLite remained relatively constant at around 1.2 seconds. This suggests that the file system also employs some form of caching, which significantly improves read performance after the first access.

While SQLite provides faster write operations, especially for bulk inserts, the file system can provide faster read operations after initial access, likely due to caching mechanisms. The choice between the two would therefore depend on the specific requirements of the application, such as whether it performs more write or read operations, and whether it can benefit from the bulk insert capabilities of SQLite's `executemany()` function.

> Note: The text file provided here is from this [wikipedia page](https://en.wikipedia.org/wiki/India)

```
Model Name: MacBook Air
Chip: Apple M2
Total Number of Cores: 8 (4 performance and 4 efficiency)
Memory: 8 GB
OS Loader Version: 10151.101.3

❯ python benchmark.py --iterations=10000 --filename=text
write_file_system took 2.743858814239502 seconds
read_file_system took 2.236079216003418 seconds
write_sqlite took 4.433104038238525 seconds
read_sqlite took 1.4777662754058838 seconds
Cleaning up files

❯ python benchmark.py --iterations=10000 --filename=text
write_file_system took 2.6941733360290527 seconds
read_file_system took 0.43399596214294434 seconds
write_sqlite took 3.7641801834106445 seconds
read_sqlite took 1.1609210968017578 seconds
Cleaning up files

❯ python benchmark.py --iterations=10000 --filename=text
write_file_system took 2.742851972579956 seconds
read_file_system took 0.47078585624694824 seconds
write_sqlite took 3.8059799671173096 seconds
read_sqlite took 1.5623891353607178 seconds
Cleaning up files

❯ python benchmark.py --iterations=10000 --filename=text
write_file_system took 2.7235238552093506 seconds
read_file_system took 0.4649050235748291 seconds
write_sqlite took 3.938897132873535 seconds
read_sqlite took 1.2644450664520264 seconds
Cleaning up files
```