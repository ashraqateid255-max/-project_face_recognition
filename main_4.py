import io
import os
import pickle
import sqlite3
from datetime import date, datetime

import cv2
import face_recognition
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from PIL import Image
from sklearn.neighbors import KNeighborsClassifier

app = FastAPI(title="Face Attendance & Auth System API (KNN Powered)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATASET_DIR = r"C:\Users\AYA\Downloads\data set"
KNN_MODEL_PATH = "knn_model.pkl"
DB_PATH = "attendance_app.db"

# ------------------------------------------------------------------
# Currently, each employee's face encoding is stored inside the 'users'
# table (in the 'encoding' BLOB column below), right alongside their username.
# It is no longer kept in a separate pickle file. This serves as the single
# source of truth: no second file exists that can drift out of sync with 
# what is actually in the database.
# The KNN model is simply a "trained cache" of this column, which gets retrained
# directly from the database whenever a new user registers (signup).
# ------------------------------------------------------------------


# 1. Initialize Database Tables
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            title TEXT NOT NULL,
            encoding BLOB
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            full_name TEXT NOT NULL,
            check_in TEXT,
            check_out TEXT,
            date TEXT NOT NULL
        )
    """)

    # Migration: If the "users" table existed prior to this feature,
    # the CREATE TABLE IF NOT EXISTS line above won't add the new column automatically.
    # We add it manually here if missing.
    cursor.execute("PRAGMA table_info(users)")
    existing_cols = [row[1] for row in cursor.fetchall()]
    if "encoding" not in existing_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN encoding BLOB")

    conn.commit()
    conn.close()


def encoding_to_blob(encoding):
    return np.asarray(encoding, dtype=np.float64).tobytes()


def blob_to_encoding(blob):
    return np.frombuffer(blob, dtype=np.float64)


# 2. Safely Process Initial Dataset (Optional bulk import path —
#    Runs only once if DATASET_DIR contains photos and no users exist in the DB)
def process_initial_dataset():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    has_users = cursor.fetchone()[0] > 0
    conn.close()

    if has_users or not os.path.exists(DATASET_DIR):
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for person_name in os.listdir(DATASET_DIR):
        person_dir = os.path.join(DATASET_DIR, person_name)
        if not os.path.isdir(person_dir) or person_name.endswith("_cropped"):
            continue

        username = person_name.lower().replace(" ", "_")
        encoding_blob = None

        for img_name in os.listdir(person_dir):
            if img_name.lower().endswith((".png", ".jpg", ".jpeg")):
                try:
                    img_path = os.path.join(person_dir, img_name)
                    image = face_recognition.load_image_file(img_path)
                    encs = face_recognition.face_encodings(image)
                    if len(encs) > 0:
                        encoding_blob = encoding_to_blob(encs[0])
                        break  # One good picture is enough to register the person
                except Exception:
                    continue

        if encoding_blob is None:
            continue

        try:
            cursor.execute(
                "INSERT INTO users (username, password, full_name, title, encoding) VALUES (?, ?, ?, ?, ?)",
                (username, "123456", person_name, "Employee", encoding_blob),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            pass

    conn.close()


# 3. Train KNN model directly from the users table.
#    This is the only place where the model is built — invoke it after any user registration,
#    ensuring it never mismatches the database.
def train_knn_from_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT username, encoding FROM users WHERE encoding IS NOT NULL"
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return None

    X = [blob_to_encoding(blob) for _, blob in rows]
    y = [username for username, _ in rows]

    clf = KNeighborsClassifier(n_neighbors=1)
    clf.fit(X, y)

    with open(KNN_MODEL_PATH, "wb") as f:
        pickle.dump(clf, f)

    return clf


init_db()
process_initial_dataset()
knn_clf = train_knn_from_db()


def match_face(face_encoding, threshold=0.4):
    """The single source of truth for 'who owns this face'"""
    if knn_clf is None:
        return None
    try:
        distances, _ = knn_clf.kneighbors([face_encoding], n_neighbors=1)
        if distances[0][0] < threshold:
            return str(knn_clf.predict([face_encoding])[0])
    except Exception:
        pass
    return None
# ------------------------------------------------------------------
# LIVENESS CHECK / ANTI-SPOOFING
#
# All the logic above only answers "who owns this face?" — it doesn't verify
# whether the camera sees a live person or a printed photo/phone screen.
# This function handles the liveness verification so any endpoint receiving
# a face image can apply the check consistently.
#
# Note: This is a lightweight heuristic (image sharpness + reflection analysis
# via OpenCV), not a fully trained anti-spoofing ML model. It will catch low-quality
# printed photos or screen glare, but high-quality prints or high-res screen playbacks
# might bypass it.
# For production-grade security, consider replacing this function body with a model like:
#   - Silent-Face-Anti-Spoofing (https://github.com/minivision-ai/Silent-Face-Anti-Spoofing)
#   - DeepFace with anti_spoofing=True (https://github.com/serengil/deepface)
# Endpoints calling this function won't need to change if you upgrade the internal logic.
# ------------------------------------------------------------------
def is_real_face(
    rgb_img, face_location, blur_threshold=60.0, glare_ratio_threshold=0.03
):
    """Basic best-effort liveness check. Returns True if the cropped face looks
    like a live capture, and False if it appears to be a printed photo or screen.
    face_location is expected as (top, right, bottom, left) from face_recognition.
    """
    try:
        top, right, bottom, left = face_location
        top, left = max(top, 0), max(left, 0)
        face_crop = rgb_img[top:bottom, left:right]
        if face_crop.size == 0:
            return False

        gray = cv2.cvtColor(face_crop, cv2.COLOR_RGB2GRAY)

        # 1) Printed photos and low-end screen playbacks lose high-frequency details (skin pores, micro-textures).
        #    A live face captured at a reasonable distance retains higher detail, resulting in a higher Laplacian variance (edges).
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        if laplacian_var < blur_threshold:
            return False

        # 2) Mobile or tablet screens held in front of the camera often create small, blown-out bright spots (glare),
        #    which typically doesn't happen on a real face under normal room lighting.
        _, bright_mask = cv2.threshold(gray, 245, 255, cv2.THRESH_BINARY)
        glare_ratio = float(np.count_nonzero(bright_mask)) / gray.size
        if glare_ratio > glare_ratio_threshold:
            return False

        return True
    except Exception:
        # If the liveness check itself throws an exception, fail closed (fail safely)
        # by treating it as non-live rather than letting the request bypass security.
        return False


@app.get("/")
def root():
    return {
        "status": "online",
        "message": "Face Attendance System API with KNN is running.",
    }


# 4. User Registration Endpoint (Sign Up)
@app.post("/signup")
async def signup(
    username: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...),
):
    global knn_clf

    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        rgb_img = np.array(image)
        face_locs = face_recognition.face_locations(rgb_img)
        face_encs = face_recognition.face_encodings(rgb_img, face_locs)
    except Exception:
        return {"status": "error", "message": "Invalid image format."}

    if not face_encs:
        return {"status": "error", "message": "No face detected in photo."}

    if not is_real_face(rgb_img, face_locs[0]):
        return {
            "status": "spoof_detected",
            "message": "The photo does not appear to be live (it might be a printout or a screen). Please take a real live photo.",
        }

    encoding_blob = encoding_to_blob(face_encs[0])

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password, full_name, title, encoding) VALUES (?, ?, ?, ?, ?)",
            (username, password, full_name, title, encoding_blob),
        )
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError:
        return {
            "status": "error",
            "message": f"Username '{username}' already taken.",
        }

    # The new user's face is now in the database — retrain the KNN model
    # immediately so they can log in / check in right away.
    knn_clf = train_knn_from_db()

    return {
        "status": "success",
        "message": f"Account created successfully for {full_name}!",
        "user_info": {
            "username": username,
            "full_name": full_name,
            "title": title,
        },
    }


# 5. Face Login Endpoint (receives photo only, no password required)
@app.post("/login")
async def login(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        rgb_img = np.array(image)
        face_locs = face_recognition.face_locations(rgb_img)
        face_encs = face_recognition.face_encodings(rgb_img, face_locs)
    except Exception:
        return {"status": "error", "message": "Could not read that photo."}

    if not face_encs:
        return {"status": "error", "message": "No face detected in the photo."}

    if not is_real_face(rgb_img, face_locs[0]):
        return {
            "status": "spoof_detected",
            "message": "The photo does not appear to be live. Please take a real live photo.",
        }

    matched_user = match_face(face_encs[0])

    if not matched_user:
        return {
            "status": "error",
            "message": "Face not recognized. Sign up first, or try a clearer photo.",
        }

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT username, full_name, title FROM users WHERE username = ?",
        (matched_user,),
    )
    user = cursor.fetchone()
    conn.close()

    # Since KNN is trained directly from the database table, this case should be
    # impossible, but it is kept here as a fallback safety net.
    if not user:
        return {
            "status": "error",
            "message": f"Face matched '{matched_user}', but that user no longer exists. Try /retrain-model.",
        }

    return {
        "status": "success",
        "message": f"Welcome back, {user[1]}!",
        "user_info": {
            "username": user[0],
            "full_name": user[1],
            "title": user[2],
        },
    }


# 6. Check-In Endpoint
#
# expected_username must originate from the authenticated session of the user
# currently logged in on the device/page — it should never be left empty or trusted
# blindly from an unauthenticated form field, otherwise the check is useless.
# The endpoint verifies two things before accepting check-in:
# (1) whether the face is live, and (2) whether the face matches the logged-in account (expected_username).
# Previously, it only checked 'who is this face' and recorded attendance under that user name,
# allowing anyone to check in on behalf of a colleague.
@app.post("/attendance/check-in")
async def check_in(
    expected_username: str = Form(...), file: UploadFile = File(...)
):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        rgb_img = np.array(image)
        face_locs = face_recognition.face_locations(rgb_img)
        face_encs = face_recognition.face_encodings(rgb_img, face_locs)
    except Exception:
        return {"status": "error", "message": "Failed to read image."}

    if not face_encs:
        return {"status": "error", "message": "No face detected in image."}

    if not is_real_face(rgb_img, face_locs[0]):
        return {
            "status": "spoof_detected",
            "message": "The photo does not appear to be live (it might be a printout or a screen).",
        }

    matched_user = match_face(face_encs[0])

    if not matched_user:
        return {"status": "unknown_person", "message": "Face not recognized."}

    # Identity check: detected face must strictly match the logged-in user (expected_username).
    # Reject request if they differ, even if the detected face belongs to another registered employee.
    if matched_user != expected_username:
        return {
            "status": "identity_mismatch",
            "message": "The face in the photo does not match the currently logged-in account.",
        }

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT full_name, title FROM users WHERE username = ?", (matched_user,)
    )
    user_data = cursor.fetchone()

    full_name = user_data[0] if user_data else matched_user
    title = user_data[1] if user_data else "Employee"

    today_date = date.today().strftime("%Y-%m-%d")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "SELECT check_in FROM attendance WHERE username = ? AND date = ?",
        (matched_user, today_date),
    )
    already_marked = cursor.fetchone()

    if already_marked and already_marked[0]:
        conn.close()
        return {
            "status": "already_marked",
            "message": f"Welcome {full_name}, check-in already marked today!",
            "check_in_time": already_marked[0],
            "user_info": {"full_name": full_name, "title": title},
        }

    cursor.execute(
        "INSERT INTO attendance (username, full_name, check_in, date) VALUES (?, ?, ?, ?)",
        (matched_user, full_name, now_str, today_date),
    )
    conn.commit()
    conn.close()

    return {
        "status": "success",
        "message": f"Welcome {full_name}! Check-in recorded successfully.",
        "check_in_time": now_str,
        "user_info": {"full_name": full_name, "title": title},
    }


# 7. Check-Out Endpoint — applies the same expected_username / liveness protections as check-in.
@app.post("/attendance/check-out")
async def check_out(
    expected_username: str = Form(...), file: UploadFile = File(...)
):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        rgb_img = np.array(image)
        face_locs = face_recognition.face_locations(rgb_img)
        face_encs = face_recognition.face_encodings(rgb_img, face_locs)
    except Exception:
        return {"status": "error", "message": "Failed to read image."}

    if not face_encs:
        return {"status": "error", "message": "No face detected."}

    if not is_real_face(rgb_img, face_locs[0]):
        return {
            "status": "spoof_detected",
            "message": "The photo does not appear to be live (it might be a printout or a screen).",
        }

    matched_user = match_face(face_encs[0])

    if not matched_user:
        return {"status": "unknown_person", "message": "Face not recognized."}

    # Identity check: must match the logged-in account.
    if matched_user != expected_username:
        return {
            "status": "identity_mismatch",
            "message": "The face in the photo does not match the currently logged-in account.",
        }

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    today_date = date.today().strftime("%Y-%m-%d")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "SELECT id, check_out FROM attendance WHERE username = ? AND date = ?",
        (matched_user, today_date),
    )
    record = cursor.fetchone()

    if not record:
        conn.close()
        return {
            "status": "error",
            "message": "No check-in record found for today!",
        }

    if record[1]:
        conn.close()
        return {
            "status": "already_marked",
            "message": "Already checked out today!",
            "check_out_time": record[1],
        }

    cursor.execute(
        "UPDATE attendance SET check_out = ? WHERE id = ?", (now_str, record[0])
    )
    conn.commit()

    cursor.execute(
        "SELECT full_name, title FROM users WHERE username = ?", (matched_user,)
    )
    user_data = cursor.fetchone()
    conn.close()

    return {
        "status": "success",
        "message": f"Goodbye {user_data[0]}! Check-out successful.",
        "check_out_time": now_str,
        "user_info": {"full_name": user_data[0], "title": user_data[1]},
    }


# 8. Retrain KNN model on-demand from database — rarely needed in typical usage
#    (as signup triggers it automatically), but available for emergency manual database edits.
@app.post("/retrain-model")
def retrain_model():
    global knn_clf
    knn_clf = train_knn_from_db()
    return {
        "status": "success",
        "message": "KNN model retrained from the users table.",
        "knn_loaded": knn_clf is not None,
        "known_faces": len(knn_clf.classes_) if knn_clf is not None else 0,
    }


# Maintained as an alias to /retrain-model for backwards compatibility.
@app.post("/reload-model")
def reload_model():
    return retrain_model()


# 9. Diagnostic Endpoint — shows exactly who the KNN model is trained on.
#    Should strictly match the database users table.
@app.get("/debug/status")
def debug_status():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users")
    db_usernames = sorted(set(r[0] for r in cursor.fetchall()))
    cursor.execute("SELECT username FROM users WHERE encoding IS NULL")
    missing_encoding = sorted(set(r[0] for r in cursor.fetchall()))
    conn.close()

    knn_labels = (
        sorted(set(str(c) for c in knn_clf.classes_))
        if knn_clf is not None
        else []
    )

    return {
        "status": "success",
        "database_usernames": db_usernames,
        "knn_model_labels": knn_labels,
        "knn_loaded": knn_clf is not None,
        "users_missing_a_face_encoding": missing_encoding,
    }


# 10. Fetch Attendance History for a Single User (used by profile page)
@app.get("/attendance/user/{username}")
def get_user_attendance(username: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT full_name, title FROM users WHERE username = ?", (username,)
    )
    user_row = cursor.fetchone()

    if not user_row:
        conn.close()
        return {"status": "error", "message": "User not found."}

    full_name, title = user_row

    cursor.execute(
        "SELECT date, check_in, check_out FROM attendance WHERE username = ? ORDER BY date DESC",
        (username,),
    )
    rows = cursor.fetchall()
    conn.close()

    records = [
        {"date": r[0], "check_in": r[1], "check_out": r[2]} for r in rows
    ]

    return {
        "status": "success",
        "user_info": {
            "username": username,
            "full_name": full_name,
            "title": title,
        },
        "records": records,
    }


# 11. Fetch Complete Attendance Log for All Employees (company-wide log)
@app.get("/attendance/all")
def get_all_attendance():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.date, a.username, u.full_name, u.title, a.check_in, a.check_out
        FROM attendance a
        LEFT JOIN users u ON u.username = a.username
        ORDER BY a.date DESC, a.check_in DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    records = [
        {
            "date": r[0],
            "username": r[1],
            "full_name": r[2] if r[2] else r[1],
            "title": r[3] if r[3] else "Employee",
            "check_in": r[4],
            "check_out": r[5],
        }
        for r in rows
    ]

    return {"status": "success", "records": records}
