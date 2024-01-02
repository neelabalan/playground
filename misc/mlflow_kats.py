import json
import os
from sys import version_info

import matplotlib.pyplot as plt
import mlflow.pyfunc
import pandas as pd
from kats.consts import TimeSeriesData
from kats.models.sarima import SARIMAModel
from kats.models.sarima import SARIMAParams
from loguru import logger

os.environ['MLFLOW_TRACKING_URI'] = 'http://0.0.0.0:5000'
os.environ['MLFLOW_TRACKING_USERNAME'] = 'mlflow_user'
os.environ['MLFLOW_TRACKING_PASSWORD'] = 'mlflow_pass'

PYTHON_VERSION = f'{version_info.major}.{version_info.minor}.{version_info.micro}'

data = []
with open('data.json') as file:
    data = json.load(file)

reg_model_name = 'SARIMA'


class SARIMA_MLFlowModel(mlflow.pyfunc.PythonModel):
    def __init__(self, tsd, param, steps=60):
        super().__init__()
        self.model = SARIMAModel(tsd, param)
        self.steps = steps
        self.tsd = tsd
        self.model.fit()

    def predict(self, context, model_input):
        return [context, model_input]


def run():
    model_path = 'mlflow_artifacts'
    tsd = TimeSeriesData(pd.DataFrame(data[0]))
    model = SARIMA_MLFlowModel(tsd, SARIMAParams(p=1, d=1, q=1))
    with mlflow.start_run(run_name='SARIMA_MODEL') as run:
        model_path = f'{model_path}-{run.info.run__uuid}'
        mlflow.log_params('model', 'sarima')
        mlflow.log_metric('MAE', 0.0011)
        tsd.plot()
        plt.savefig('fig.png')
        mlflow.log_artifact('fig.png')
        mlflow.pyfunc.save_model(path=model_path, python_model=model)

    mlflow.pyfunc.log_model(
        artifact_path=model_path,
        python_model=model,
        registered_model_name=reg_model_name,
    )


def forecast():
    df = pd.DataFrame(data[0])
    global reg_model_name
    model_uri = 'models:/SARIMA/1'
    loaded_model = mlflow.pyfunc.load_model(model_uri)
    logger.info(loaded_model.predict(50))


if __name__ == '__main__':
    run()
