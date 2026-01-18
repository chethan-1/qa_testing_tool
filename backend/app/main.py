from fastapi import FastAPI

app = FastAPI(title="QA Tool")

@app.get("/health")
def health():
    return {"status": "ok"}