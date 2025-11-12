import reflex as rx
from typing import TypedDict, Optional
import asyncio
import logging
import httpx


class UploadedFile(TypedDict):
    filename: str
    file_id: int


class Message(TypedDict):
    role: str
    content: str
    attached_files: list[UploadedFile] | None


class RAGState(rx.State):
    """The state for the RAG application."""

    messages: list[Message] = []
    is_processing: bool = False
    uploaded_files: list[UploadedFile] = []

    @rx.event
    async def handle_upload(self, files: list[rx.UploadFile]):
        """Handle the upload of files by sending them to the FastAPI backend."""
        if not files:
            yield rx.toast.error("No files selected to upload.")
            return
        for file in files:
            try:
                upload_data = await file.read()
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        "http://localhost:9000/upload",
                        files={"file": (file.name, upload_data, file.content_type)},
                    )
                    response.raise_for_status()
                    response_data = response.json()
                    message = response_data.get(
                        "message", f"File '{file.name}' processed."
                    )
                    self.uploaded_files.clear()
                    self.uploaded_files.append(
                        {
                            "filename": response_data["filename"],
                            "file_id": response_data["file_id"],
                        }
                    )
                    yield rx.toast.success(message)
            except httpx.RequestError as e:
                logging.exception(f"Backend connection error during upload: {e}")
                yield rx.toast.error(
                    "Error: Could not connect to the backend to upload file."
                )
            except Exception as e:
                logging.exception(f"An error occurred during file upload: {e}")
                yield rx.toast.error(f"An unexpected error occurred: {str(e)}")

    @rx.event(background=True)
    async def remove_file(self, file_id: int):
        """Remove a file from the database and the uploaded files list."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(f"http://localhost:9000/file/{file_id}")
                response.raise_for_status()
                response_data = response.json()
            async with self:
                filename_to_remove = ""
                for f in self.uploaded_files:
                    if f["file_id"] == file_id:
                        filename_to_remove = f["filename"]
                        break
                self.uploaded_files = [
                    f for f in self.uploaded_files if f["file_id"] != file_id
                ]
                for i in range(len(self.messages)):
                    if self.messages[i]["attached_files"]:
                        self.messages[i]["attached_files"] = [
                            f
                            for f in self.messages[i]["attached_files"]
                            if f["file_id"] != file_id
                        ]
            yield rx.toast.success(
                response_data.get("message", f"Removed file: {filename_to_remove}")
            )
        except httpx.RequestError as e:
            logging.exception(f"Backend connection error during file deletion: {e}")
            yield rx.toast.error(
                "Error: Could not connect to the backend to delete file."
            )
        except httpx.HTTPStatusError as e:
            logging.exception(f"Error deleting file: {e}")
            yield rx.toast.error(
                f"Error deleting file: {e.response.json().get('detail', e.response.text)}"
            )
        except Exception as e:
            logging.exception(f"An unexpected error occurred during file deletion: {e}")
            yield rx.toast.error(f"An unexpected error occurred: {str(e)}")

    @rx.event
    def submit_query(self, form_data: dict):
        """Handle the submission of a user query."""
        query = form_data.get("query", "").strip()
        if not query and (not self.uploaded_files):
            return rx.toast.warning("Query cannot be empty.")
        attached_files = self.uploaded_files
        self.uploaded_files = []
        self.messages.append(
            {
                "role": "user",
                "content": query or "Sent files",
                "attached_files": attached_files if attached_files else None,
            }
        )
        self.is_processing = True
        yield RAGState.get_backend_response

    @rx.event(background=True)
    async def get_backend_response(self):
        """Get a response from the backend RAG model."""
        async with self:
            last_message = self.messages[-1]
            query = last_message["content"]
            file_id = (
                last_message["attached_files"][0]["file_id"]
                if last_message["attached_files"]
                else None
            )
            payload = {"query": query, "file_id": file_id}

        async with self:
            self.messages.append(
                {
                    "role": "assistant",
                    "content": "",
                    "attached_files": None,
                }
            )

        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST", "http://localhost:9000/process-query", json=payload
                ) as response:

                    if response.status_code != 200:
                        async with self:
                            self.messages[-1][
                                "content"
                            ] = f"Error: {response.status_code} - Could not get response."
                        return  # Stop

                    async for chunk in response.aiter_text():
                        if chunk:
                            async with self:
                                self.messages[-1]["content"] += chunk

        except httpx.RequestError as e:
            logging.exception(f"Backend connection error: {e}")
            async with self:
                self.messages[-1][
                    "content"
                ] = "Error: Could not connect to the backend."
        except Exception as e:
            logging.exception(f"An error occurred while getting response: {e}")
            async with self:
                self.messages[-1]["content"] = f"An unexpected error occurred: {str(e)}"
        finally:
            async with self:
                self.is_processing = False