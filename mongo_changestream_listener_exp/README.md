For running the oplog tailer

`go run ./oplog_monitor/monitor.go --mongo-uri="mongodb://192.168.0.117:27017/?directConnection=true" --database="test_db" --collection="test_collection"`

For running data dump

`go run ./data_op/data_operations.go --mongo-uri="mongodb://192.168.0.117:27017/?directConnection=true" --operation=write --num-docs=10000 --continuous --interval=2  --bulk`

For running the change stream listener

`python change_stream_listener.py --mongo-uri="mongodb://192.168.0.117:27017/?directConnection=true"`