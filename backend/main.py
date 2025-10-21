import os
import sqlalchemy
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from databases import Database

# --- Directory for Retrieved Files ---
# Create a directory to store files retrieved from the database
RETRIEVED_FILES_DIR = "retrieved_files"
os.makedirs(RETRIEVED_FILES_DIR, exist_ok=True)

# --- Database Configuration ---
# Replace with your actual PostgreSQL connection details
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://postgres:pillsgap@localhost:5432/postgres"
)

# SQLAlchemy setup
database = Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

# Define the table schema for storing files
files_table = sqlalchemy.Table(
    "files",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("filename", sqlalchemy.String(255), nullable=False),
    sqlalchemy.Column("data", sqlalchemy.LargeBinary, nullable=False),
)

# Create an SQLAlchemy engine to create the table if it doesn't exist
engine = sqlalchemy.create_engine(DATABASE_URL.replace("+asyncpg", ""))
metadata.create_all(engine)


# --- Lifespan Event Handler ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events for the application.
    Connects to the database on startup and disconnects on shutdown.
    """
    await database.connect()
    print("Database connection established.")
    yield
    await database.disconnect()
    print("Database connection closed.")


# --- FastAPI Application ---
app = FastAPI(lifespan=lifespan)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:9000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- API Endpoints ---
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Handles file uploads by reading the file content and storing it in the database.
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    try:
        content = await file.read()
        query = files_table.insert().values(filename=file.filename, data=content)
        file_id = await database.execute(query)
        return {
            "message": f"File '{file.filename}' uploaded successfully",
            "file_id": file_id,
            "filename": file.filename,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.get("/file/{file_id}")
async def get_file(file_id: int):
    """
    Retrieves a file from the database by its ID and returns it for browser download.
    """
    try:
        query = files_table.select().where(files_table.c.id == file_id)
        result = await database.fetch_one(query)
        if not result:
            raise HTTPException(status_code=404, detail="File not found")
        return Response(
            content=result["data"],
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={result['filename']}"
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# --- NEW ENDPOINT TO RETRIEVE FILE TO SERVER DISK ---
@app.get("/retrieve/{file_id}")
async def retrieve_file(file_id: int):
    """
    Retrieves a file from the database and saves it to the server's local filesystem.
    """
    try:
        # Step 1: Query the database to find the file by its ID
        query = files_table.select().where(files_table.c.id == file_id)
        result = await database.fetch_one(query)

        if not result:
            raise HTTPException(status_code=404, detail="File not found in database")

        # Step 2: Extract filename and binary data
        filename = result["filename"]
        file_data = result["data"]

        # Step 3: Define the full path to save the file
        save_path = os.path.join(RETRIEVED_FILES_DIR, filename)

        # Step 4: Write the binary data to a new file on the server
        # 'wb' mode is crucial: it writes in binary mode, ensuring data integrity.
        with open(save_path, "wb") as f:
            f.write(file_data)

        print(f"File '{filename}' successfully retrieved and saved to '{save_path}'")

        # Step 5: Return a success response
        return {
            "message": "File retrieved from database and saved locally",
            "file_id": file_id,
            "filename": filename,
            "saved_path": save_path,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An error occurred during retrieval: {str(e)}"
        )
