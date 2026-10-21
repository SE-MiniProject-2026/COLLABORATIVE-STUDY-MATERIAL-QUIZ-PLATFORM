import os
import json
from database import get_db, UPLOAD_DIR, TEST_DIR

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