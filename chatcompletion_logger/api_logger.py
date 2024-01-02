import abc
import json
import logging
import pathlib
import time
from typing import Dict
from typing import Literal

import httpx
from typing_extensions import Self

log = logging.getLogger(__name__)


class OpenAIPricingCalculator:
    PRICING_DATA: Dict[str, Dict] = {}

    def calculate_token_cost(self, model: str, token_count: int, token_type: Literal['input', 'output']) -> float:
        price_per_token = self.PRICING_DATA[model][token_type]
        total_cost = price_per_token * (token_count / 1000)
        return total_cost

    def load_pricing_data(self, path: str) -> Self:
        try:
            with open(path, 'r') as file:
                self.PRICING_DATA = json.load(file)
        except FileNotFoundError:
            log.error('Pricing data file not found. Please run `python pricing_data.py` to generate it.')
        return self


class AbstractHttpLogger(abc.ABC):
    @abc.abstractmethod
    def log_request(self, request):
        pass

    @abc.abstractmethod
    def log_response(self, response):
        pass


class ChatCompletionHttpLogger(AbstractHttpLogger):
    pricing_calculator = OpenAIPricingCalculator().load_pricing_data('model_pricing.json')

    def __init__(self, log_directory: str | pathlib.Path):
        self.log_directory = log_directory
        pathlib.Path(self.log_directory).mkdir(parents=True, exist_ok=True)

    def log_request(self, request):
        request.extensions['start_time'] = time.time()

    def log_response(self, response):
        response.read()
        end_time = time.time()
        response_json = response.json()
        start_time = response.request.extensions['start_time']
        model = response_json['model']
        prompt_token_cost = self.pricing_calculator.calculate_token_cost(
            model=model, token_count=response_json['usage']['prompt_tokens'], token_type='input'
        )
        completion_token_cost = self.pricing_calculator.calculate_token_cost(
            model=model, token_count=response_json['usage']['completion_tokens'], token_type='output'
        )
        with open(f'{self.log_directory}/{end_time}.json', 'w') as file:
            json.dump(
                {
                    'status_code': str(response.status_code),
                    'url': str(response.url),
                    'start_time': start_time,
                    'end_time': end_time,
                    'latency_ms': (end_time - start_time) * 1000,
                    'request_body': json.loads(response.request.content.decode()) if response.request.content else None,
                    'response_body': response.json(),
                    'prompt_token_cost': prompt_token_cost,
                    'completion_token_cost': completion_token_cost,
                    'total_token_cost': prompt_token_cost + completion_token_cost,
                },
                file,
                indent=4,
            )


def create_http_client(logger: AbstractHttpLogger, timeout=600.0, connect_timeout=5.0, max_redirects=20):
    return httpx.Client(
        event_hooks={'request': [logger.log_request], 'response': [logger.log_response]},
        timeout=httpx.Timeout(timeout=timeout, connect=connect_timeout),
        max_redirects=max_redirects,
    )
