import reflex as rx
from rag_project.style import upload_button, text_input, send_button, action_bar_style


class State(rx.State):
    text: str = ""

    def set_text(self, value: str):
        self.text = value

    def upload_file(self, files):
        print("Uploaded files:", files)


def action_bar() -> rx.Component:
    return rx.box(
        rx.hstack(
            # Hidden file input
            rx.input(
                type="file",
                id="file-upload",
                multiple=False,
                accept=".txt,.png,.jpg",
                style={"display": "none"},
                # on_change=State.upload_file,
            ),
            # Upload button
            rx.button(
                rx.icon("arrow-up"),
                on_click=rx.call_script(
                    """
                    const input = document.getElementById('file-upload');
                    input.click();
                    input.onchange = async () => {
                        const file = input.files[0];
                        const formData = new FormData();
                        formData.append('file', file);

                        const response = await fetch('http://localhost:9000/upload', {
                            method: 'POST',
                            body: formData
                        });

                        const result = await response.json();
                        console.log("Uploaded:", result);
                        alert("Uploaded: " + result.filename);
                    };
                """
                ),
                style=upload_button,
            ),
            # Text input
            rx.input(
                placeholder="Type something...",
                value=State.text,
                on_change=State.set_text,
                style=text_input,
            ),
            rx.button(
                rx.icon("send-horizontal"),
                style=send_button,
            ),
            spacing="3",
            align="center",
            width="min(95%, 860px)",
            margin_x="auto",
        ),
        **action_bar_style
    )


def index() -> rx.Component:
    return rx.box(
        rx.vstack(
            action_bar(),
            align="center",
        ),
        width="100%",
        height="100vh",
        bg_color="#14101FF8",
    )


app = rx.App()
app.add_page(index)
