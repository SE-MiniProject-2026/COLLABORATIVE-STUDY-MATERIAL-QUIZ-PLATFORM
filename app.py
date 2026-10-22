import io

from nicegui import ui

from auth import authenticate_user, register_student
from database import init_db, get_db
from services import (
    create_test,
    delete_material,
    delete_test,
    get_material_path,
    get_performance_summary,
    get_test_results,
    get_tests,
    search_materials,
    submit_quiz_attempt,
    upload_material,
)

init_db()
current_user = {"user": None}


def refresh_page():
    ui.navigate.to("/")


@ui.page("/")
def main_page():
    ui.label("Collaborative Study Material & Quiz Platform").classes(
        "text-2xl font-bold mb-4"
    )

    if not current_user["user"]:
        with ui.card().classes("w-96 mx-auto p-6"):
            ui.label("Login to CSMQ").classes("text-xl mb-2")
            username = ui.input("Username")
            password = ui.input("Password", password=True)

            def login():
                user = authenticate_user(username.value, password.value)
                if user:
                    current_user["user"] = user
                    refresh_page()
                else:
                    ui.notify("Invalid credentials or deactivated account.", type="negative")

            ui.button("Login", on_click=login).classes("w-full")

            ui.separator()
            ui.label("New students can register below.")
            register_username = ui.input("New username")
            register_password = ui.input("New password", password=True)

            def register():
                if register_student(register_username.value, register_password.value):
                    ui.notify("Registration successful. You are now logged in.", type="positive")
                    current_user["user"] = authenticate_user(
                        register_username.value, register_password.value
                    )
                    refresh_page()
                else:
                    ui.notify("Username may already exist or fields are empty.", type="negative")

            ui.button("Register as Student", on_click=register).classes("w-full")
            
    return

    user = current_user["user"]
    ui.label(f"Welcome, {user['username']} ({user['role']})").classes("text-lg")
    ui.button(
        "Logout",
        on_click=lambda: (current_user.update({"user": None}), refresh_page()),
    ).classes("bg-red-500 text-white")

    with ui.tabs().classes("w-full mt-4") as tabs:
        materials_tab = ui.tab("Shared Materials")
        tests_tab = ui.tab("Tests")
        if user["role"] == "Admin":
            admin_tab = ui.tab("Admin Management")
            admin_results_tab = ui.tab("Test Results")
        if user["role"] == "Student":
            scores_tab = ui.tab("My Results")

    with ui.tab_panels(tabs, value=materials_tab).classes("w-full"):
        with ui.tab_panel(materials_tab):
            ui.label("All users share this material library.").classes("font-bold")
            search = ui.input("Search by title, subject, or description")
            material_list = ui.column()

            def render_materials():
                material_list.clear()
                with material_list:
                    for material in search_materials(search.value or ""):
                        with ui.row().classes("items-center"):
                            ui.label(
                                f"{material['title']} [{material['subject']}] - "
                                f"{material['description'] or ''}"
                            )
                            path = get_material_path(material["id"])
                            if path:
                                ui.button(
                                    "Download",
                                    on_click=lambda path=path: ui.download(path),
                                )
                            if user["role"] == "Admin":
                                ui.button(
                                    "Delete",
                                    on_click=lambda material_id=material["id"]: (
                                        delete_material(material_id),
                                        render_materials(),
                                    ),
                                ).props("color=negative")

            search.on("update:model-value", render_materials)
            render_materials()

            ui.label("Add a file to the shared library").classes("font-bold mt-4")
            title = ui.input("Title")
            subject = ui.input("Subject")
            description = ui.input("Description")

            async def handle_upload(event):
                try:
                    file_data = await event.file.read()
                    upload_material(
                        title.value,
                        subject.value,
                        description.value,
                        io.BytesIO(file_data),
                        user["id"],
                        event.file.name,
                    )
                    ui.notify("File uploaded.", type="positive")
                    render_materials()
                except (OSError, ValueError) as error:
                    ui.notify(str(error), type="negative")

            ui.upload(on_upload=handle_upload, auto_upload=True)

        with ui.tab_panel(tests_tab):
            ui.label("Published multiple-choice tests").classes("font-bold")
            for test_number, test in enumerate(get_tests(), start=1):
                with ui.card().classes("w-full"):
                    ui.label(f"Test {test_number}: {test['title']}").classes(
                        "text-lg font-bold"
                    )
                    ui.label(test.get("instructions", ""))
                    answers = {}
                    for index, question in enumerate(test["questions"]):
                        ui.label(question["question"]).classes("font-semibold")
                        answers[str(index)] = ui.radio(question["options"])

                    def submit(test=test, answers=answers):
                        selected = {key: value.value for key, value in answers.items()}
                        score = submit_quiz_attempt(user["id"], test["id"], selected)
                        ui.notify(f"Your score is {score:.2f}%.", type="positive")

                    ui.button("Submit Test", on_click=submit)

        if user["role"] == "Student":
            with ui.tab_panel(scores_tab):
                summary = get_performance_summary(user["id"])
                ui.label(f"Average score: {summary['avg_score']:.2f}%")
                ui.label(f"Tests attempted: {summary['total_attempts']}")
                for result in summary.get("history", []):
                    ui.label(
                        f"Test #{result['quiz_id']}: {result['score']:.2f}% "
                        f"({result['submission_time']})"
                    )

        if user["role"] == "Admin":
            with ui.tab_panel(admin_tab):
                ui.label("Create a multiple-choice test").classes("font-bold")
                test_title = ui.input("Test title")
                test_instructions = ui.input("Instructions")
                question_list = []
                question_container = ui.column().classes("w-full")

                def add_question():
                    with question_container:
                        with ui.card().classes("w-full"):
                            question_number = len(question_list) + 1
                            ui.label(f"Question {question_number}").classes(
                                "font-semibold"
                            )
                            question_text = ui.input("Question text").classes("w-full")
                            option_inputs = [
                                ui.input(f"Option {index}").classes("w-full")
                                for index in range(1, 5)
                            ]
                            ui.label("Correct option:")
                            correct_option = ui.radio(
                                ["Option 1", "Option 2", "Option 3", "Option 4"],
                                value="Option 1",
                            )
                            question_list.append(
                                (question_text, option_inputs, correct_option)
                            )

                add_question()
                ui.button("Add another question", on_click=add_question)

                def save_test():
                    try:
                        questions = []
                        for question_text, option_inputs, correct_option in question_list:
                            options = [option.value.strip() for option in option_inputs]
                            if not question_text.value.strip():
                                raise ValueError("Every question needs question text")
                            if any(not option for option in options):
                                raise ValueError("Every question needs four options")
                            correct_index = int(correct_option.value.split()[-1]) - 1
                            questions.append(
                                {
                                    "question": question_text.value.strip(),
                                    "options": options,
                                    "answer": options[correct_index],
                                }
                            )
                        test_id = create_test(
                            test_title.value,
                            test_instructions.value,
                            questions,
                            user["id"],
                        )
                        ui.notify(f"Test #{test_id} published.", type="positive")
                        refresh_page()
                    except (TypeError, ValueError, OSError) as error:
                        ui.notify(f"Unable to publish test: {error}", type="negative")

                ui.button("Publish Test", on_click=save_test)
                ui.label("Existing tests and results").classes("font-bold mt-4")
                for test in get_tests():
                    with ui.row().classes("items-center"):
                        ui.label(test["title"])
                        ui.button(
                            "Check results",
                            on_click=lambda test_id=test["id"]: show_results(test_id),
                        )
                        ui.button(
                            "Delete",
                            on_click=lambda test_id=test["id"]: (
                                delete_test(test_id),
                                refresh_page(),
                            ),
                        ).props("color=negative")

            with ui.tab_panel(admin_results_tab):
                ui.label("Test Results").classes("text-xl font-bold")
                results_title = ui.label("Select a test from Admin Management.")
                results_table = ui.table(
                    columns=[
                        {"name": "username", "label": "Student", "field": "username"},
                        {"name": "score", "label": "Score", "field": "score"},
                        {
                            "name": "submission_time",
                            "label": "Submitted",
                            "field": "submission_time",
                        },
                    ],
                    rows=[],
                    row_key="username",
                ).classes("w-full")

                def show_results(test_id):
                    selected_test = next(
                        (test for test in get_tests() if test["id"] == test_id), None
                    )
                    results_title.set_text(
                        selected_test["title"] if selected_test else "Test Results"
                    )
                    rows = [
                        {
                            "username": result["username"],
                            "score": f"{result['score']:.2f}%",
                            "submission_time": result["submission_time"],
                        }
                        for result in get_test_results(test_id)
                    ]
                    results_table.rows = rows
                    results_table.update()
                    tabs.value = admin_results_tab


ui.run(port=8080)        