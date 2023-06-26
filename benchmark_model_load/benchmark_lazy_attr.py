import argparse
import timeit
from functools import lru_cache
from typing import Any, Dict, List, Tuple

import pandas as pd
import xgboost as xgb
from sklearn import datasets
from sklearn.model_selection import train_test_split


class ModelWithoutCache:
    _model: xgb.XGBClassifier = None

    @property
    def model(self) -> xgb.XGBClassifier:
        if self._model is None:
            self._model = self.train_model()
        return self._model

    def fetch_data(self) -> Tuple[Any, Any]:
        iris = datasets.load_iris()
        X = iris.data
        y = iris.target
        return X, y

    def train_model(self) -> xgb.XGBClassifier:
        X, y = self.fetch_data()
        X_train, _, y_train, _ = train_test_split(
            X, y, test_size=0.2, random_state=123
        )
        model = xgb.XGBClassifier(use_label_encoder=False)
        model.fit(X_train, y_train)
        return model

    def save_model(self) -> None:
        self.model.save_model('model.joblib')


class ModelWithCache(ModelWithoutCache):
    @property
    @lru_cache(maxsize=1)
    def model(self) -> xgb.XGBClassifier:
        return super().model


def benchmark(iteration: int) -> None:

    results: List[Dict[str, float]] = []
    without_cache = ModelWithoutCache()
    with_cache = ModelWithCache()

    for i in range(iteration):
        start = timeit.default_timer()
        without_cache.model
        end = timeit.default_timer()
        time_without_cache = end - start

        start = timeit.default_timer()
        with_cache.model
        end = timeit.default_timer()
        time_with_cache = end - start
        results.append(
            {
                "run": i + 1,
                "without_lru_cache": time_without_cache,
                "with_lru_cache": time_with_cache,
            }
        )

    df = pd.DataFrame(results)
    df.to_csv("benchmark_results.csv", index=False)
    df[["without_lru_cache", "with_lru_cache"]][10:].plot().figure.savefig(
        "benchmark_results.png"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Benchmark the usage of lru_cache in Python."
    )
    parser.add_argument(
        "-i",
        "--iteration",
        type=int,
        default=100,
        help="Number of times to run the benchmark",
    )
    args = parser.parse_args()

    benchmark(args.iteration)
