import os
import sqlalchemy
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from databases import Database
from dotenv import load_dotenv
from pathlib import Path
from pydantic import BaseModel
from typing import Optional
from backend.ingestion import ingest_document, delete_vectors
from backend.retreival import get_streaming_answer

load_dotenv()


from backend.ingestion import ingest_document, delete_vectors

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
# Note: Use the non-async driver for table creation
engine_url = DATABASE_URL.replace("+asyncpg", "")
if "postgresql://" in engine_url:
    # psycopg2 is the default sync driver
    pass
elif "mysql" in engine_url:
    engine_url = engine_url.replace("+asyncmy", "+pymysql")
elif "sqlite" in engine_url:
    engine_url = engine_url.replace("+aiosqlite", "")

try:
    engine = sqlalchemy.create_engine(engine_url)
    metadata.create_all(engine)
    print("Database tables checked/created.")
except Exception as e:
    print(f"Error creating database engine or tables: {e}")
    print("Please ensure your database is running and DATABASE_URL is correct.")


# --- Lifespan Event Handler ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events for the application.
    Connects to the database on startup and disconnects on shutdown.
    """
    try:
        await database.connect()
        print("Database connection established.")
    except Exception as e:
        print(f"Error connecting to database: {e}")
    yield
    if database.is_connected:
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
    1. Replaces any existing file in the PostgreSQL database.
    2. Deletes the old file's vectors from Pinecone.
    3. Ingests the new file's vectors into Pinecone.
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    try:
        # Read the new file's content and name ONCE
        content = await file.read()
        filename = file.filename

        # 1. Check if a file already exists in the table.
        select_query = files_table.select().limit(1)
        existing_file = await database.fetch_one(select_query)

        message: str
        file_id: int

        if existing_file:
            # 2a. If a file exists, DELETE its old vectors from Pinecone
            print(
                f"Existing file found (ID: {existing_file['id']}). Deleting old vectors..."
            )
            try:
                await delete_vectors(file_id=str(existing_file["id"]))
            except Exception as e:
                print(f"Warning: Could not delete old vectors: {e}")
                # Continue anyway, as we are replacing the file

            # 2b. UPDATE the file in PostgreSQL
            print(f"Updating file in database...")
            update_query = (
                files_table.update()
                .where(files_table.c.id == existing_file["id"])
                .values(filename=filename, data=content)
            )
            await database.execute(update_query)
            file_id = existing_file["id"]
            message = f"File '{filename}' successfully replaced the previous file."

        else:
            # 3. If no file exists, INSERT a new one into PostgreSQL
            print("No existing file found. Creating new record...")
            insert_query = files_table.insert().values(filename=filename, data=content)
            file_id = await database.execute(insert_query)
            message = f"File '{filename}' successfully uploaded."

        # 4. INGEST the new file's vectors into Pinecone
        print(f"Starting vector ingestion for file_id: {file_id}...")
        try:
            await ingest_document(
                file_content=content,  # <-- Use the "pass-the-bytes" method
                file_id=str(file_id),
                filename=filename,
            )
            print(f"Successfully ingested vectors for file_id: {file_id}")
        except Exception as e:
            # If ingestion fails, the file is in the DB but Pinecone is out of sync.
            # This is a critical error.
            raise HTTPException(
                status_code=500,
                detail=f"File saved to DB, but Pinecone ingestion failed: {str(e)}",
            )

        # 5. Return the success response
        return {"message": message, "file_id": file_id, "filename": filename}

    except Exception as e:
        # Catch any other unexpected errors
        print(f"An error occurred during upload: {e}")
        if isinstance(e, HTTPException):
            raise  # Re-raise HTTPException if it's one we threw
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.get("/retrieve/{file_id}")
async def retrieve_file(file_id: int):
    """
    Retrieves a file from the database and saves it to the server's local filesystem.
    (Kept for your file quality checks)
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
    Deletes a file from the PostgreSQL database AND its associated vectors
    from Pinecone.
    """
    try:
        # 1. Check if file exists in PostgreSQL
        query = files_table.select().where(files_table.c.id == file_id)
        result = await database.fetch_one(query)
        if not result:
            raise HTTPException(status_code=404, detail="File not found in database")

        # 2. Delete file from PostgreSQL
        print(f"Deleting file {file_id} from PostgreSQL...")
        delete_query = files_table.delete().where(files_table.c.id == file_id)
        await database.execute(delete_query)
        print("Deleted from PostgreSQL.")

        # 3. Delete vectors from Pinecone
        print(f"Deleting vectors for file_id {file_id} from Pinecone...")
        await delete_vectors(file_id=str(file_id))
        print("Deleted vectors from Pinecone.")

        return {
            "message": f"File '{result['filename']}' and its vectors successfully deleted"
        }
    except Exception as e:
        print(f"An error occurred during deletion: {e}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.get("/current-file")
async def get_current_file():
    """
    Returns the filename of the single file currently in the database.
    This is for the Reflex UI to fetch on page load.
    """
    try:
        query = files_table.select().limit(1)
        result = await database.fetch_one(query)

        if result:
            # A file exists, return its name and ID
            return {"filename": result["filename"], "file_id": result["id"]}
        else:
            # No file in the database
            return {"filename": None, "file_id": None}

    except Exception as e:
        print(f"Error fetching current file: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


class QueryRequest(BaseModel):
    query: str
    file_id: Optional[int] = None


@app.post("/process-query")
async def process_query(request: QueryRequest = Body(...)):
    """
    Receives a query and file_id from the frontend,
    calls the RAG pipeline, and *streams* the response.
    """
    try:
        print(f"Processing query: '{request.query}' for file_id: {request.file_id}")
        file_id_str = str(request.file_id) if request.file_id is not None else None

        # 1. Get the generator from our retrieval logic
        answer_generator = get_streaming_answer(
            query=request.query, file_id=file_id_str
        )

        # 2. Return a StreamingResponse that yields from the generator
        return StreamingResponse(answer_generator, media_type="text/event-stream")

    except Exception as e:
        print(f"Error processing query: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
