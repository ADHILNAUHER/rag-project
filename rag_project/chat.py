import reflex as rx
from rag_project.state import RAGState
from rag_project.file_card import uploaded_file_card
from rag_project.style import *


def chat_input_area() -> rx.Component:
    """The chat input area with file upload and send button."""
    return rx.el.div(
        rx.cond(
            RAGState.uploaded_files.length() > 0,
            rx.el.div(
                rx.foreach(RAGState.uploaded_files, uploaded_file_card),
                class_name="flex flex-wrap items-center gap-2 p-2",
            ),
        ),
        rx.el.form(
            rx.el.div(
                rx.el.input(
                    name="query",
                    placeholder="Type something...",
                    class_name=input_box,
                ),
                class_name="w-full",
            ),
            rx.el.div(
                rx.upload.root(
                    rx.el.button(
                        rx.icon("paperclip", class_name="h-4 w-4"),
                        "Attach",
                        type="button",
                        class_name=upload_button,
                    ),
                    id="file_upload",
                    multiple=False,
                    accept={
                        "pdf": [".pdf"],
                        "plain": [".txt"],
                        "msword": [".doc"],
                        "image": [".png"],
                    },
                    on_drop=RAGState.handle_upload(
                        rx.upload_files(upload_id="file_upload")
                    ),
                    class_name="flex",
                ),
                rx.el.button(
                    rx.icon("arrow-up", class_name="h-4 w-4"),
                    type="submit",
                    disabled=RAGState.is_processing,
                    class_name=send_buttom,
                ),
                class_name="flex items-center justify-between w-full mt-2",
            ),
            on_submit=RAGState.submit_query,
            reset_on_submit=True,
            class_name="w-full",
        ),
        class_name=action_bar,
    )


def chat_area() -> rx.Component:
    return (
        rx.el.div(
            rx.icon("bot-message-square", class_name="h-25 w-25 text-[#4f3a69] mb-6"),
            rx.el.h2(
                "Welcome to your RAG assistant",
                class_name="text-2xl font-semibold text-[#baa7d1]",
            ),
            rx.el.p(
                "Upload documents and ask questions to get started.",
                class_name="text-[#baa7d1] font-medium mt-2",
            ),
            class_name="flex flex-col items-center justify-center text-center h-full",
        ),
    )
