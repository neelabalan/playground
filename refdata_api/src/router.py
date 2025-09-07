import pandas as pd
from fastapi import Request
from fastapi import APIRouter
from model import Query
from functools import cache
from model import ReferenceDataStore
import json


api = APIRouter()
reference_data_store = ReferenceDataStore()
reference_data_store.initialize()

@cache
def get_reference_data(reference_data):
    df_list = reference_data_store.trait_get(reference_data).values()
    df = list(df_list)[0]
    print(df.head())
    return df

@api.post('/reference/{reference_data}')
async def api_reference(reference_data, request: Query):
    df = get_reference_data(reference_data)
    return df.query(request.query).to_dict('records')

@api.get('/reference_list/{reference_data}')
async def api_reference_list(reference_data):
    df = get_reference_data(reference_data)
    df = pd.DataFrame({'column':df.dtypes.index, 'type':df.dtypes.values})
    return json.loads(df.to_json(default_handler=str, orient='records'))


@api.get('/reference')
async def api_get(request: Request):
    config = []
    with open('config.json') as file:
        config = json.load(file)
    return [val.get('endpoint') for val in config]
