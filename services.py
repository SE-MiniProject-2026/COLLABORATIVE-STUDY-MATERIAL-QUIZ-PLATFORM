import os
import json
from database import get_db, UPLOAD_DIR, TEST_DIR

# --- Study Materials ---

"""
@description: This function handles the uploading of study materials. It saves the uploaded file to the server and records its metadata in the database. It ensures that both title and subject are provided,
and it uses the provided filename or defaults to the original filename of the uploaded file.

@input title: str - The title of the material
@input subject: str - The subject of the material
@input description: str - A brief description of the material
@input file_obj: file-like object - The uploaded file object
@input uploader_id: int - The ID of the user uploading the material
@input filename: str (optional) - The name of the file to save as; if not provided, the original filename will be used

@output: bool - Returns True if the upload was successful, raises ValueError if title or subject is empty
"""
def upload_material(title, subject, description, file_obj, uploader_id, filename=None):
    filename = os.path.basename(filename or file_obj.name)
    if not title.strip() or not subject.strip():
        raise ValueError("Title and subject are required")
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(file_obj.read())
        
    conn = get_db()
    conn.execute("INSERT INTO materials (title, subject, description, filename, uploader_id) VALUES (?, ?, ?, ?, ?)",
                 (title, subject, description, filename, uploader_id))
    conn.commit()
    conn.close()
    return True


"""
@description: This function deletes a study material from the database and removes its associated file from the server. It first checks if the material exists, and if so, it deletes the file and the database record.

@input material_id: int - The ID of the material to delete

@output: bool - Returns True if the deletion was successful, False if the material does not
    exist.
"""
def delete_material(material_id):
    conn = get_db()
    material = conn.execute(
        "SELECT filename FROM materials WHERE id = ?", (material_id,)
    ).fetchone()
    if not material:
        conn.close()
        return False
    filepath = os.path.join(UPLOAD_DIR, material["filename"])
    if os.path.exists(filepath):
        os.remove(filepath)
    conn.execute("DELETE FROM materials WHERE id = ?", (material_id,))
    conn.commit()
    conn.close()
    return True

"""
@description: This function retrieves the file path of a study material based on its ID. It queries the database for the filename and constructs the full path to the file on the server. If the material does not exist or the file is missing, it returns None.

@input material_id: int - The ID of the material to retrieve

@output: str or None - Returns the file path if the material exists and the file is
    present, otherwise returns None.
"""

def get_material_path(material_id):
    conn = get_db()
    material = conn.execute(
        "SELECT filename FROM materials WHERE id = ?", (material_id,)
    ).fetchone()
    conn.close()
    if not material:
        return None
    filepath = os.path.join(UPLOAD_DIR, material["filename"])
    return filepath if os.path.isfile(filepath) else None


"""
@description: This function searches for study materials in the database based on a query string. It looks for matches in the title, subject, or description fields of the materials. The search is case-insensitive and uses SQL LIKE syntax to find partial matches.

@input query: str - The search query string

@output: list of dict - Returns a list of dictionaries, each representing a material that matches the search criteria. Each dictionary contains the material's details such as id, title, subject, description, filename, and uploader_id.
"""

def search_materials(query=""):
    conn = get_db()
    q = f"%{query}%"
    rows = conn.execute("SELECT * FROM materials WHERE title LIKE ? OR subject LIKE ? OR description LIKE ?", (q, q, q)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# --- Question Bank & Quizzes ---
"""
@description: This function creates a new question in the database. It takes the question text, options, correct answer, topic, and the ID of the creator as inputs. The question is then inserted into the 'questions' table.

@input text: str - The text of the question
@input options: list - A list of possible answer options for the question
@input correct_answer: str - The correct answer for the question
@input topic: str - The topic or category of the question
@input creator_id: int - The ID of the user creating the question

@output: None - The function does not return any value, but it inserts the question into
"""
def create_question(text, options, correct_answer, topic, creator_id):
    conn = get_db()
    conn.execute("INSERT INTO questions (question_text, options, correct_answer, topic, creator_id) VALUES (?, ?, ?, ?, ?)",
                 (text, options, correct_answer, topic, creator_id))
    conn.commit()
    conn.close()

"""
@description: This function creates a new quiz in the database. It takes the quiz title, instructions, a list of question IDs, and the ID of the creator as inputs. The quiz is inserted into the 'quizzes' table, and each question ID is associated with the quiz in the 'quiz_questions' table.

@input title: str - The title of the quiz
@input instructions: str - Instructions for the quiz
@input question_ids: list - A list of question IDs to be included in the quiz
@input creator_id: int - The ID of the user creating the quiz

@output: None - The function does not return any value, but it inserts the quiz and its associated questions into the database.
"""

def create_quiz(title, instructions, question_ids, creator_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO quizzes (title, instructions, creator_id) VALUES (?, ?, ?)", (title, instructions, creator_id))
    quiz_id = cursor.lastrowid
    for q_id in question_ids:
        cursor.execute("INSERT INTO quiz_questions (quiz_id, question_id) VALUES (?, ?)", (quiz_id, q_id))
    conn.commit()
    conn.close()
    
    
"""
@description: This function creates a new test in the database. It takes the test title, instructions, a list of questions (each with its own options and correct answer), and the ID of the creator as inputs. The test is inserted into the 'quizzes' table, and the questions are saved in a JSON file associated with the test.

@input title: str - The title of the test
@input instructions: str - Instructions for the test
@input questions: list - A list of dictionaries, each representing a question with its text, options, and correct answer
@input creator_id: int - The ID of the user creating the test

@output: int - Returns the ID of the newly created test
"""

def create_test(title, instructions, questions, creator_id):
    title = (title or "").strip()
    instructions = (instructions or "").strip()
    if not title or not isinstance(questions, list) or not questions:
        raise ValueError("A test requires a title and at least one question")
    for question in questions:
        if (
            not isinstance(question, dict)
            or not question.get("question")
            or not isinstance(question.get("options"), list)
            or len(question["options"]) < 2
            or question.get("answer") not in question["options"]
        ):
            raise ValueError("Each question needs text, options, and a valid answer")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO quizzes (title, instructions, is_published, creator_id) VALUES (?, ?, 1, ?)",
        (title, instructions, creator_id),
    )
    test_id = cursor.lastrowid
    with open(os.path.join(TEST_DIR, f"{test_id}.json"), "w", encoding="utf-8") as file:
        json.dump(
            {"id": test_id, "title": title, "instructions": instructions,
             "questions": questions},
            file,
            indent=2,
        )
    conn.commit()
    conn.close()
    return test_id


"""
@description: This function retrieves all published tests from the database. It queries the 'quizzes' table for tests that are marked as published and then reads the associated JSON files for each test to return their details.

@output: list of dict - Returns a list of dictionaries, each representing a published test with its details such as id, title, instructions, and questions.
"""

def get_tests():
    conn = get_db()
    rows = conn.execute(
        "SELECT id, title, instructions FROM quizzes WHERE is_published = 1 ORDER BY id DESC"
    ).fetchall()
    conn.close()
    tests = []
    for row in rows:
        path = os.path.join(TEST_DIR, f"{row['id']}.json")
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as file:
                tests.append(json.load(file))
    return tests

"""
@description: This function deletes a test from the database and removes its associated JSON file from the server. It first deletes any related quiz questions and then removes the test record from the 'quizzes' table. Finally, it checks for the existence of the JSON file and deletes it if present.

@input test_id: int - The ID of the test to delete

@output: None - The function does not return any value, but it deletes the test and its associated data from the database and server.
"""

def delete_test(test_id):
    conn = get_db()
    conn.execute("DELETE FROM quiz_questions WHERE quiz_id = ?", (test_id,))
    conn.execute("DELETE FROM quizzes WHERE id = ?", (test_id,))
    conn.commit()
    conn.close()
    path = os.path.join(TEST_DIR, f"{test_id}.json")
    if os.path.isfile(path):
        os.remove(path)

"""
@description: This function retrieves the results of a specific test from the database. It queries the 'attempts' table for all attempts made on the specified test, joining with the 'users' table to get the usernames of the students who took the test. The results are ordered by submission time in descending order.

@input test_id: int - The ID of the test for which to retrieve results

@output: list of dict - Returns a list of dictionaries, each representing an attempt on the test with details such as score, submission time, and username of the student.
"""

def get_test_results(test_id):
    conn = get_db()
    rows = conn.execute(
        """SELECT attempts.score, attempts.submission_time, users.username
           FROM attempts JOIN users ON users.id = attempts.student_id
           WHERE attempts.quiz_id = ? ORDER BY attempts.submission_time DESC""",
        (test_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]

# --- Evaluation & Analytics ---

"""
@description: This function processes a student's quiz attempt by comparing their submitted answers with the correct answers stored in the database or in a JSON file for tests. It calculates the score as a percentage of correct answers, records the attempt in the 'attempts' table, and returns the calculated score.

@input student_id: int - The ID of the student submitting the attempt
@input quiz_id: int - The ID of the quiz being attempted
@input student_answers: dict - A dictionary mapping question IDs to the student's submitted answers

@output: float - Returns the score as a percentage of correct answers
"""
def submit_quiz_attempt(student_id, quiz_id, student_answers):
    conn = get_db()
    test_path = os.path.join(TEST_DIR, f"{quiz_id}.json")
    if os.path.isfile(test_path):
        with open(test_path, encoding="utf-8") as file:
            questions = json.load(file)["questions"]
        correct_answers = {
            str(index): question["answer"]
            for index, question in enumerate(questions)
        }
    else:
        rows = conn.execute("""
            SELECT q.id, q.correct_answer FROM questions q
            JOIN quiz_questions qq ON q.id = qq.question_id
            WHERE qq.quiz_id = ?
        """, (quiz_id,)).fetchall()
        correct_answers = {str(row["id"]): row["correct_answer"] for row in rows}

    score = 0
    total = len(correct_answers)
    for question_id, correct_answer in correct_answers.items():
        if student_answers.get(question_id) == correct_answer:
            score += 1
            
    percentage = (score / total) * 100 if total > 0 else 0
    
    conn.execute("INSERT INTO attempts (student_id, quiz_id, score, answers) VALUES (?, ?, ?, ?)",
                 (student_id, quiz_id, percentage, str(student_answers)))
    conn.commit()
    conn.close()
    return percentage

"""
@description: This function retrieves a summary of a student's performance across all their quiz attempts. It calculates the average score and total number of attempts, and also provides a history of all attempts made by the student.

@input student_id: int - The ID of the student for whom to retrieve the performance summary

@output: dict - Returns a dictionary containing the average score, total number of attempts, and a history of all attempts made by the student. The history is a list of dictionaries, each representing an attempt with details such as score and submission time.
"""


def get_performance_summary(student_id):
    conn = get_db()
    attempts = conn.execute("SELECT * FROM attempts WHERE student_id = ?", (student_id,)).fetchall()
    conn.close()
    if not attempts:
        return {"avg_score": 0, "total_attempts": 0}
    scores = [a["score"] for a in attempts]
    return {
        "avg_score": sum(scores) / len(scores),
        "total_attempts": len(attempts),
        "history": [dict(a) for a in attempts]
    }
