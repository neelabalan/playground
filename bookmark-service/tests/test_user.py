import subprocess

import requests

# import psycopg2
from loguru import logger

# conn = psycopg2.connect(database="bookmark", user="bm_user", password="pass", host="db")


url = "http://bookmark:5000"


def create_and_tear(func):
    def wrapper(*args, **kwargs):
        subprocess.run("python /home/app/bookmark/manage.py create_db", shell=True)
        return func(*args, **kwargs)

    return wrapper


@create_and_tear
def test_create_user():
    response = requests.post(
        url=f"{url}/users", json={"username": "test", "email": "test@test.com", "password": "pass123"}
    ).json()
    logger.info(response)
    assert response["username"] == "test"
    assert response["email"] == "test@test.com"
