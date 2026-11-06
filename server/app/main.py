from fastapi import FastAPI


app = FastAPI(title="Todo List API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

