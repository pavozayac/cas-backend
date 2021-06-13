from fastapi import FastAPI

app = FastAPI()

@app.get('/{id}')
async def root(id: int):
    return {'Returned id': id}
