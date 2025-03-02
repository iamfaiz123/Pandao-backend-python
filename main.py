from app import load_server
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin_routes import admin_routes
from app.api.manifest_routes import transaction_manifest_routes





app = FastAPI(
    title="Pan-dao Backed API - only for internal use / need not to be shared publicly",
    description="PandaDAO is a decentralized autonomous organization (DAO) platform built on the Radix blockchain. It aims to provide tools and infrastructure for communities to organize, govern, and manage shared resources in a transparent and efficient manner. Leveraging Radix's unique architecture, PandaDAO seeks to offer enhanced security, scalability, and user experience for DAO operations",
    version="1.0.0",
    terms_of_service="not defined",
    contact={
        "name": "API Support",
        "url": "http://example.com/contact/",
        "email": "support@example.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://pandao-admin.vercel.app","https://pandao.live"],  # Allow all origins
    allow_credentials=False,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers

)



transaction_manifest_routes(app)
admin_routes(app)
load_server(app)
