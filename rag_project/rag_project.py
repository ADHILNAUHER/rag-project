import reflex as rx
from rag_project.chat import chat_input_area, chat_area


def index() -> rx.Component:
    """The main page displaying the chat UI."""
    return rx.el.div(
        chat_area(),
        chat_input_area(),
        class_name="flex flex-col h-screen bg-[#14101F] text-white font-['Montserrat']",
    )


app = rx.App(
    theme=rx.theme(appearance="dark", accent_color="pink"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(rel="preconnect", href="https://fonts.gstatic.com", cross_origin=""),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap",
            rel="stylesheet",
        ),
    ],
)
app.add_page(index, title="RAG UI Demo")