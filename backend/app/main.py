from fastapi import FastAPI

app = FastAPI(
    title="AI Settlement Controller",
    description="AI-powered settlement drift detection and financial control system",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}