
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "FastAPI works"}

@app.get("/health")
def health():
    return {"status": "ok"}
