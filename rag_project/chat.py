import reflex as rx
from rag_project.style import input_box, upload_button, send_buttom, action_bar


def chat_input_area() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.input(
                    placeholder="Type something...",
                    class_name=input_box,
                ),
                class_name="w-full",
            ),
            rx.el.div(
                rx.button(
                    rx.icon("paperclip", class_name="h-4 w-4"),
                    "Attach",
                    class_name=upload_button,
                    on_click=rx.call_script(
                        """
                        const input = document.createElement('input');
                        input.type = 'file';
                        input.accept = '.pdf, .txt';

                        input.onchange = () => {
                            const file = input.files[0];
                            if (!file) return;

                            const formData = new FormData();
                            formData.append('file', file);

                            fetch('http://localhost:9000/upload', {
                                method: 'POST',
                                body: formData
                            })
                            .then(response => response.json())
                            .then(data => {
                                alert('Upload successful: ' + data.filename);
                            })
                            .catch(error => {
                                console.error('Upload failed:', error);
                                alert('Upload failed');
                            });
                        };

                        input.click();
                    """
                    ),
                ),
                rx.el.button(
                    rx.icon("arrow-up", class_name="h-4 w-4"),
                    type="button",
                    on_click=rx.toast("This is a UI demonstration", duration=3000),
                    class_name=send_buttom,
                ),
                class_name="flex items-center justify-between w-full mt-2",
            ),
            class_name="w-full",
        ),
        class_name=action_bar,
    )
