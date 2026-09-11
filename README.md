# FaceGate AI

A face-recognition attendance system: employees sign up with a photo, then
log in and check in/out by scanning their face — no passwords needed at
the door. Built with FastAPI (backend) and Streamlit (frontend).

## How it works

- Each employee's face encoding is stored **inside the `users` table**
  itself (an `encoding` BLOB column) — not in a separate file. That's the
  single source of truth: there's no second file that can drift out of
  sync with who's actually registered.
- A `KNeighborsClassifier` (KNN) is trained directly from that table and
  used to recognize faces at login, check-in, and check-out. It's
  retrained automatically every time a new employee signs up.
- Attendance (check-in / check-out times) is stored per employee, per day,
  in an `attendance` table.

## Project structure

```
main.py     FastAPI backend — auth, signup, check-in/out, attendance endpoints
app.py      Streamlit frontend — sign up, face login, check-in/out, profile, attendance file
```

## Setup

```bash
pip install -r requirements.txt
```

> `face_recognition` depends on `dlib`, which needs `cmake` and a C++
> compiler to build. On Windows, installing a prebuilt `dlib` wheel is
> usually easier than building from source.

## Running it

Start the backend:

```bash
uvicorn main:app --reload
```

In a separate terminal, start the frontend:

```bash
streamlit run app.py
```

The Streamlit app's sidebar lets you set the backend URL (defaults to
`http://127.0.0.1:8000`).

## API endpoints

| Method | Path                          | Purpose                                   |
|--------|-------------------------------|--------------------------------------------|
| POST   | `/signup`                     | Register a new employee (photo + details) |
| POST   | `/login`                      | Log in by face photo                      |
| POST   | `/attendance/check-in`        | Check in by face photo                    |
| POST   | `/attendance/check-out`       | Check out by face photo                   |
| GET    | `/attendance/user/{username}` | One employee's attendance history         |
| GET    | `/attendance/all`             | Company-wide attendance records           |
| POST   | `/retrain-model`              | Manually retrain the KNN model from the DB|
| GET    | `/debug/status`               | Compare DB users vs. trained KNN labels   |

## Notes

- `attendance_app.db` and `knn_model.pkl` are generated at runtime and are
  git-ignored — each environment builds its own.
- `DATASET_DIR` in `main.py` points at a local folder for optionally
  bulk-importing an existing employee photo set on first run; update or
  remove it for your own setup.
