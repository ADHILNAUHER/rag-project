import reflex as rx
from rag_project.state import RAGState, Message
from rag_project.file_card import uploaded_file_card
from rag_project.style import *


def message_bubble(message: Message, index: int) -> rx.Component:
    """A message bubble component for the chat."""
    is_user = message["role"] == "user"
    bubble_style = rx.cond(
        is_user, "flex flex-col items-end gap-2", "flex items-start gap-3"
    )
    icon_style = "h-8 w-8 rounded-full flex-shrink-0"
    text_bg = rx.cond(is_user, "bg-[#6F3F7A]", "bg-[#4f3a69]")

    def render_message_content() -> rx.Component:
        return rx.el.div(
            rx.cond(
                message["attached_files"],
                rx.el.div(
                    rx.foreach(
                        message["attached_files"],
                        lambda file_info: uploaded_file_card(
                            file_info=file_info, #key=file_info["file_id"]
                        ),
                    ),
                    class_name="flex flex-wrap items-center gap-2 p-2 mb-2",
                ),
            ),
            rx.el.p(message["content"], class_name="text-white/90"),
            class_name=rx.cond(
                is_user, "p-3 rounded-2xl bg-[#6F3F7A]", "p-3 rounded-2xl bg-[#4f3a69]"
            ),
        )

    def user_message() -> rx.Component:
        return rx.el.div(
            render_message_content(),
            rx.icon("user", class_name=f"{icon_style} p-1.5 bg-[#6F3F7A] text-white"),
            class_name="flex items-start gap-3 justify-end w-[50%]",
        )

    def assistant_message() -> rx.Component:
        return rx.el.div(
            rx.icon(
                "bot-message-square",
                class_name=f"{icon_style} p-1.5 bg-[#4f3a69] text-white",
            ),
            render_message_content(),
            class_name="flex items-start gap-3",
        )

    return rx.el.div(
        rx.cond(is_user, user_message(), assistant_message()), class_name=bubble_style
    )


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
                    name="query", placeholder="Type something...", class_name=input_box
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
                        "application/pdf": [".pdf"],
                        "text/plain": [".txt"],
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [
                            ".docx"
                        ],
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
    return rx.el.div(
        rx.cond(
            RAGState.messages.length() == 0,
            rx.el.div(
                rx.icon(
                    "bot-message-square", class_name="h-24 w-24 text-[#4f3a69] mb-6"
                ),
                rx.el.h2(
                    "Welcome to your RAG assistant",
                    class_name="text-2xl font-semibold text-[#baa7d1]",
                ),
                rx.el.p(
                    "Upload a document and ask questions to get started.",
                    class_name="text-[#baa7d1] font-medium mt-2",
                ),
                class_name="flex flex-col items-center justify-center text-center h-full",
            ),
            rx.el.div(
                rx.foreach(RAGState.messages, message_bubble),
                rx.cond(
                    RAGState.is_processing,
                    rx.el.div(
                        rx.icon(
                            "bot-message-square",
                            class_name="h-8 w-8 rounded-full p-1.5 bg-[#4f3a69] text-white animate-pulse",
                        ),
                        class_name="flex items-start gap-3",
                    ),
                ),
                padding_bottom="7.2rem",
                class_name="w-full max-w-4xl space-y-4 p-4",
            ),
        ),
        class_name="flex flex-col flex-grow w-full items-center overflow-y-auto p-4",
        id="chat-display",
    )