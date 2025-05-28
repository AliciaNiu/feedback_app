# app/main.py

import os
from dotenv import load_dotenv
import json
import psycopg2
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

app = FastAPI()
security = HTTPBasic()


load_dotenv(dotenv_path=".env.feedback")
USERNAME = os.getenv("BASIC_AUTH_USERNAME")
PASSWORD = os.getenv("BASIC_AUTH_PASSWORD")

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, USERNAME)
    correct_password = secrets.compare_digest(credentials.password, PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


# Build DB connection string from env
def connect_db():
    conn = psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST"),
        port="5432"
    )
    return conn


@app.post("/api/feedback")
async def receive_feedback(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(authenticate)
    ):
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON format"})

    # Basic validation
    if not data:
        error_message = "No data received"
        return JSONResponse(status_code=400, content={"error": error_message})

    missing_fields = []
    required_fields = ["page_context", "action"]
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
    
    if missing_fields:
        error_message = f"Missing fields: {', '.join(missing_fields)}"
        return JSONResponse(status_code=400, content={"error": error_message})
    
    # assume received page_context from the frontend shoule be a JSON object - need to confirm
    if not isinstance(data["page_context"], dict):
        return JSONResponse(status_code=400, content={"error": "received page content must be a JSON object"})
    
    action_fields = ["thumbs_up", "thumbs_down"]
    if data["action"] not in action_fields:
        error_message = f"Invalid action data: {data['action']}. It should be one of {action_fields}"
        print(error_message)
        return JSONResponse(status_code=400, content={"error": error_message})
    

    try:
        conn = connect_db()
        cursor = conn.cursor()
        # Insert into DB, if no session_id, will insert NULL
        cursor.execute(
            "INSERT INTO feedback (session_id, page_context, action) VALUES (%s, %s, %s)",
            (data.get("session_id"), json.dumps(data["page_context"]), data["action"]),
        )
        conn.commit()
        cursor.close()
        conn.close()
        return JSONResponse(status_code=200, content={"message": "Feedback successfully saved"})
    
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "Internal server error"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
