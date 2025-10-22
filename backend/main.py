import os
import sqlalchemy
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from databases import Database

# --- Directory for Retrieved Files ---
RETRIEVED_FILES_DIR = "retrieved_files"
os.makedirs(RETRIEVED_FILES_DIR, exist_ok=True)

# --- Database Configuration ---
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:pillsgap@localhost:5432/postgres",
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

# Create an SQLAlchemy engine to create the table
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
    Handles file uploads.
    It will REPLACE any existing file in the database to ensure only one file is
    stored at a time.
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    try:
        # Read the new file's content and name
        content = await file.read()
        filename = file.filename

        # --- NEW "REPLACE" LOGIC ---

        # 1. Check if a file already exists in the table.
        select_query = files_table.select().limit(1)
        existing_file = await database.fetch_one(select_query)

        message: str
        file_id: int

        if existing_file:
            # 2. If a file exists, UPDATE it
            print(f"Existing file found (ID: {existing_file['id']}). Replacing it...")

            update_query = (
                files_table.update()
                .where(files_table.c.id == existing_file["id"])
                .values(filename=filename, data=content)
            )
            await database.execute(update_query)

            file_id = existing_file["id"]
            message = f"File '{filename}' successfully replaced the previous file."

        else:
            # 3. If no file exists, INSERT a new one
            print("No existing file found. Creating new record...")

            insert_query = files_table.insert().values(filename=filename, data=content)
            file_id = await database.execute(insert_query)

            message = f"File '{filename}' successfully uploaded."

        # 4. Return the response
        return {"message": message, "file_id": file_id, "filename": filename}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.get("/file/{file_id}")
async def get_file(file_id: int):
    """
    Retrieves a file from the database by its ID and returns it for browser download.
    (Note: With the new logic, this will almost always be the same single file).
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


@app.get("/retrieve/{file_id}")
async def retrieve_file(file_id: int):
    """
    Retrieves a file from the database and saves it to the server's local filesystem.
    """
    try:
        query = files_table.select().where(files_table.c.id == file_id)
        result = await database.fetch_one(query)
        if not result:
            raise HTTPException(status_code=404, detail="File not found in database")

        filename = result["filename"]
        file_data = result["data"]
        save_path = os.path.join(RETRIEVED_FILES_DIR, filename)

        with open(save_path, "wb") as f:
            f.write(file_data)

        print(f"File '{filename}' successfully retrieved and saved to '{save_path}'")
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


@app.delete("/file/{file_id}")
async def delete_file(file_id: int):
    """
    Deletes a file from the database by its ID.
    """
    try:
        query = files_table.select().where(files_table.c.id == file_id)
        result = await database.fetch_one(query)
        if not result:
            raise HTTPException(status_code=404, detail="File not found")

        delete_query = files_table.delete().where(files_table.c.id == file_id)
        await database.execute(delete_query)

        return {
            "message": f"File '{result['filename']}' successfully deleted from database"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
