# Collaborative Study Material & Quiz Platform (CSMQ)

A web-based collaborative platform built with **Python**, **NiceGUI**, and **SQLite** that enables students, contributors, and administrators to share study materials, publish multiple-choice tests, and track quiz performance.

---

## Features

- **Authentication & Role-Based Access Control**
  - Secure password hashing with `bcrypt` (`passlib`).
  - Student self-registration and login from the landing page.
  - Supports `Admin`, `Contributor`, and `Student` roles with account status checks (`Active` / `Deactivated`).
- **Shared Study Material Library**
  - Upload study materials with title, subject, and description (stored in `files/` and indexed in SQLite).
  - Live search across title, subject, and description.
  - Download shared materials; administrators can delete materials.
- **Multiple-Choice Tests & Grading**
  - Administrators can create and publish 4-option multiple-choice tests with custom instructions (stored as JSON in `tests/` and tracked in SQLite).
  - Students can attempt published tests and receive immediate percentage scores upon submission.
  - Administrators can delete existing tests.
- **Performance & Results Tracking**
  - **Student View (`My Results`)**: Displays average score, total tests attempted, and submission history.
  - **Admin View (`Test Results`)**: Displays a table of student usernames, scores, and submission timestamps for any selected test.

---

## Tech Stack

- **Frontend / Web Framework:** [NiceGUI](https://nicegui.io/) (`nicegui==3.18.0`)
- **Backend / API Layer:** Python, FastAPI / Uvicorn (via NiceGUI)
- **Database:** SQLite (`csmq.db`)
- **Security:** `passlib[bcrypt]` (`bcrypt==4.0.1`)
- **Testing:** `unittest`, `pytest`, `coverage`

---

## Project Structure

```text
.
├── app.py              # NiceGUI web application entry point (runs on port 8080)
├── auth.py             # User authentication, bcrypt hashing, and student registration
├── database.py         # SQLite connection, schema initialization, and admin seeding
├── services.py         # Material management, test creation/grading, and analytics
├── tests.py            # Core unit tests for auth, RBAC, and quiz evaluation
├── coverage.py         # Extended test suite covering database, auth, services, and app
├── clean.sh            # Resets generated files (files/*, tests/*, and csmq.db)
├── requirements.txt    # Python dependencies
├── Documents/          # SRS, SAD, STP, IEEE test docs, and coverage reports
├── files/              # Uploaded study materials directory
└── tests/              # Published test JSON files directory
```

---

## Setup & Installation

1. **Create and activate a virtual environment:**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**

   ```bash
   python app.py
   ```

   The application starts on **`http://localhost:8080`**. On first run, `init_db()` automatically creates `csmq.db`, the `files/` and `tests/` directories, and a default Admin account.

---

## Configuration

The default administrator credentials can be customized via environment variables before starting the app:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `CSMQ_ADMIN_USERNAME` | `admin` | Default administrator username |
| `CSMQ_ADMIN_PASSWORD` | `admin123` | Default administrator password |

---

## Running Tests

Run the extended test suite (uses an isolated temporary directory so `csmq.db`, `files/`, and `tests/` are not modified):

```bash
python -m unittest coverage.py
```

Run the basic unit tests:

```bash
python -m unittest tests.py
```

---

## Resetting Local Data

To remove all uploaded files, test JSON files, and the SQLite database (`csmq.db`):

```bash
bash clean.sh
```
