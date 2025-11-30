from locust import HttpUser
from locust import task


class ReferenceDataUser(HttpUser):
    @task
    def test_post(self):
        self.client.post('/reference/nasdaq', json={'query': "Symbol=='AAPL'"})
