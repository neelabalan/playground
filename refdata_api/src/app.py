import uvicorn
from fastapi import FastAPI
from router import api

app = FastAPI()
app.include_router(api)

if __name__ == '__main__':
    uvicorn.run(app='app:app', reload=True, debug=True)
