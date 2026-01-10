from fastapi import FastAPI

app = FastAPI(
    title="Parallel U MVP",
    version="0.1.0",
    description="Backend for Parallel U: preferences -> explore -> condensed intelligence",
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": "Parallel U backend is running"}
