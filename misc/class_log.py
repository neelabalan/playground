import json
import logging
from datetime import datetime


class ClassStateLoggingHandler(logging.Handler):
    def __init__(self, filename: str, roll_over: int = -1):
        super().__init__()
        self.filename = filename
        self.data_list = []
        self.roll_over = roll_over

    def _get_attrs(self, obj, ignore_dunders: bool = True):
        if ignore_dunders:
            return {k: v for k, v in obj.__dict__.items() if not k.startswith('__') and not callable(v)}
        else:
            return obj.__dict__

    def _roll_over(self):
        if self.roll_over > 0 and len(self.data_list) > self.roll_over:
            self.data_list = self.data_list[-self.roll_over :]

    def emit(self, record: logging.LogRecord):
        obj = record.msg
        if not hasattr(obj, '__dict__'):
            return
        # Serialize class and instance attributes
        combined_attributes = {**self._get_attrs(type(obj)), **self._get_attrs(obj)}
        combined_attributes['_timestamp'] = str(datetime.now())  # Add _timestamp field
        self.data_list.append(combined_attributes)
        self._roll_over()

        # Write serialized data to the file
        with open(self.filename, 'w') as _file:
            json.dump(self.data_list, _file, indent=4, default=str)


# %%
# Usage
logger = logging.getLogger('class_state_logger')
logger.setLevel(logging.INFO)
handler = ClassStateLoggingHandler('logfile.log')
logger.addHandler(handler)
stream_handler = logging.StreamHandler()
logger.addHandler(stream_handler)


class Sample:
    def test(self):
        print('Hello world')


class MyClass:
    a = 1
    b = 2

    def __init__(self):
        self.sample = Sample()
        self.m = {'var1': 'test', 'var2': 'test2'}


logger.info('hey there')

logger.info(MyClass())

logger.info(Sample)

logger.info(MyClass)

logger.info(f'This is my class {MyClass()}')
