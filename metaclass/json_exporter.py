# source
# https://breadcrumbscollector.tech/when-to-use-metaclasses-in-python-5-interesting-use-cases/
import inspect
import abc


class JsonExporterMeta(abc.ABCMeta):
    _filenames = set()

    def __new__(cls, name, bases, namespace):
        # first execute abc logic
        new_cls = super().__new__(cls, name, bases, namespace)

        # There is no need to run validations against abstract class
        if inspect.isabstract(new_cls):  # 2
            return new_cls

        # Validate if _filename is a string
        if not isinstance(namespace["_filename"], str):
            raise TypeError(f"_filename attribute of {name} class has to be string!")

        # Validate if a _filename has a .json extension
        if not namespace["_filename"].endswith(".json"):
            raise ValueError(
                f'_filename attribute of {name} class has to end with ".json"!'
            )

        # Validate uniqueness of _filename among other subclasses.
        # This uses a metaclass attribute _filenames - a set of strings
        # to remember all _filenames of subclasses
        if namespace["_filename"] in cls._filenames:
            raise ValueError(f"_filename attribute of {name} class is not unique!")

        cls._filenames.add(namespace["_filename"])

        return new_cls


class JsonExporter(metaclass=JsonExporterMeta):
    pass  # The rest of the class remains unchanged, so I skipped it


class BadExporter(JsonExporter):
    _filename = 0x1233  # That's going to fail one of the checks

    def _build_row_from_raw_data(self, raw_data):
        return {"invoice_uuid": raw_data[0]}
