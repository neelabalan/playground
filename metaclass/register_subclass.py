from typing import Dict
import abc
import inspect

class StrategyMeta(abc.ABCMeta):
    """
    We keep a mapping of externally used names to classes.
    """
    registry: Dict[str, 'Strategy'] = {}

    def __new__(cls, name, bases, namespace):
        new_cls = super().__new__(cls, name, bases, namespace)

        # We register each concrete class
        if not inspect.isabstract(new_cls):
            cls.registry[new_cls.name] = new_cls

        return new_cls 


class Strategy(metaclass=StrategyMeta):
    @property
    @abc.abstractmethod
    def name(self):
        pass

    @abc.abstractmethod
    def validate_credentials(self, login: str, password: str) -> bool:
        pass

    @classmethod
    def for_name(cls, name: str) -> 'Strategy':
        # We use registry to build a better class
        return StrategyMeta.registry[name]()


class AlwaysOk(Strategy):
    name = 'always_ok'

    def validate_credentials(self, login: str, password: str) -> bool:
        # Imma YESman!
        return True

# example
Strategy.for_name('always_ok').validate_credentials('john', 'x')