import json
import pandas as pd
from pydantic import BaseModel
from traits.api import Constant, HasTraits


class Query(BaseModel):
    query: str


class ReferenceDataStore(HasTraits):
    @staticmethod
    def initialize():
        config = []
        with open("config.json", "r") as file:
            config = json.load(file)
        for val in config:
            ReferenceDataStore.add_class_trait(
                val.get("endpoint"), Constant(pd.read_csv(val.get("path")))
            )
