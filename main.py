from app import load_server
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.manifest_routes import transaction_manifest_routes

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["pandao.live"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

transaction_manifest_routes(app)
load_server(app)
