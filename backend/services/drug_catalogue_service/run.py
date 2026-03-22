import uvicorn
from fastapi import FastAPI
from app.controllers.drug_controller import router

# Initialize FastAPI
app = FastAPI(
    title="Drug Catalogue Service",
    description="Atomic microservice for managing drug inventory"
)

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)