from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Response
import os
import uuid
import json
from http import HTTPStatus
from pydantic import BaseModel
import tasks.celery_task as celeryTask
from celery.result import AsyncResult
import shutil
import pandas as pd

TEXT_FOLDER = "text_files"
os.makedirs(TEXT_FOLDER, exist_ok=True)

JSON_FOLDER = "json_files"
os.makedirs(JSON_FOLDER, exist_ok=True)

EXCEL_FOLDER = "excel_files"
os.makedirs(EXCEL_FOLDER, exist_ok=True)

IMAGE_FOLDER = "image_files"
os.makedirs(IMAGE_FOLDER, exist_ok=True)

class ResearchInput(BaseModel):
    topic: str
    style: str
    current_year: str | None = None
    language: str | None = None

class ResearchStatus(BaseModel):
    task_id: str
    status: str
    result: dict | str | None = None
    error: str | None = None

app = FastAPI()
@app.post("/test")
async def test():
    # Simulate research process
    return {"message": "Research completed successfully."}

@app.post("/research")
async def research(researchInput: ResearchInput):
    task = celeryTask.research.delay(researchInput.topic, researchInput.style)
    return {"task_id": task.id}

@app.post("/market_research")
async def market_research(researchInput: ResearchInput):
    task = celeryTask.market_research.delay(researchInput.topic, researchInput.style, researchInput.current_year)
    return {"task_id": task.id}

@app.post("/system_analyst")
async def system_analyst(researchInput: ResearchInput):
    task = celeryTask.system_analyst.delay(researchInput.topic, researchInput.style)
    return {"task_id": task.id}

@app.post("/development")
async def development(researchInput: ResearchInput):
    task = celeryTask.development.delay(researchInput.topic, researchInput.language)
    return {"task_id": task.id}

@app.post("/txt_file_analyzer")
async def txt_file_analyzer(file: UploadFile = File(...)):
    if file.content_type != "text/plain":
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Only text files are allowed.")
    
    file_extension = os.path.splitext(file.filename)[1] or ".txt"
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(TEXT_FOLDER, unique_filename)

    content = await file.read()

    with open(file_path, "wb") as f:
        f.write(content)

    task = celeryTask.txt_file_analyzer.delay(file_path)
    return {"task_id": task.id, "file_path": file_path}

@app.post("/json_file_analyzer")
async def json_file_analyzer(file: UploadFile = File(...)):
    if file.content_type != "application/json":
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Only JSON files are allowed.")

    file_extension = os.path.splitext(file.filename)[1] or ".json"
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(JSON_FOLDER, unique_filename)

    content = await file.read()

    with open(file_path, "wb") as f:
        f.write(content)

    task = celeryTask.json_file_analyzer.delay(file_path)
    return {"task_id": task.id, "file_path": file_path}

@app.post("/excel_file_analyzer")
async def excel_file_analyzer(file: UploadFile = File(...)):
    if file.content_type != "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Only Excel files are allowed.")

    file_extension = os.path.splitext(file.filename)[1] or ".xlsx"
    file_extension = ".csv"
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(EXCEL_FOLDER, unique_filename)

    # content = await file.read()

    # with open(file_path, "wb") as f:
    #     f.write(content)

    # with open(file_path, "wb") as buffer:
    #     shutil.copyfileobj(file.file, buffer)

    df = pd.read_excel(file.file)

    # Clean if needed
    df = df.dropna(how="all")

    # Save to CSV
    df.to_csv(file_path, index=False)

    task = celeryTask.excel_file_analyzer.delay(file_path)
    return {"task_id": task.id, "file_path": file_path}

@app.post("/anomaly_detection")
async def anomaly_detection(file: UploadFile = File(...)):
    if file.content_type != "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Only Excel files are allowed.")

    file_extension = os.path.splitext(file.filename)[1] or ".xlsx"
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(EXCEL_FOLDER, unique_filename)

    content = await file.read()

    with open(file_path, "wb") as f:
        f.write(content)

    task = celeryTask.anomaly_detection.delay(file_path)
    return {"task_id": task.id, "file_path": file_path}

@app.post("/forecast_report")
async def forecast_report(file: UploadFile = File(...)):
    """
    Upload a file and immediately trigger the Prophet analysis.
    The filename is handled dynamically.
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Invalid format. Please upload an Excel file.")

    # Generate a unique file path to avoid conflicts and ensure the worker can access it
    file_extension = os.path.splitext(file.filename)[1] or ".xlsx"  # Default to .xlsx if no extension
    unique_filename = f"{uuid.uuid4()}{file_extension}"

    # Define the dynamic file path
    file_path = os.path.join(EXCEL_FOLDER, unique_filename)
    absolute_file_path = os.path.abspath(file_path)

    try:
        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Trigger Celery task with the dynamic filename
        # We pass the path so the worker knows exactly where it is
        task = celeryTask.forecast_report.delay(absolute_file_path)
        
        return {
            "task_id": task.id, 
            "status": "Started", 
            "filename": file.filename,
            "unique_filename": unique_filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/helmet_detection")
async def helmet_detection(file: UploadFile = File(...)):
    if not file.filename.endswith(('.jpg', '.jpeg', '.png')):
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Only image files (jpg, jpeg, png) are allowed.")

    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(IMAGE_FOLDER, unique_filename)

    content = await file.read()

    with open(file_path, "wb") as f:
        f.write(content)

    task = celeryTask.helmet_detection.delay(file_path)
    return {"task_id": task.id, "file_path": file_path}

@app.get("/status/{task_id}", response_model=ResearchStatus)
async def get_status(task_id: str):
    task_result = celeryTask.celery_app.AsyncResult(task_id)
    if task_result.state == "PENDING":
        return ResearchStatus(task_id=task_id, status="PENDING")
    elif task_result.state == "RUNNING":
        return ResearchStatus(task_id=task_id, status="RUNNING")
    elif task_result.state == "SUCCESS":
        # if (isinstance(task_result.result, str)):
        #     try:
        #         result = json.loads(task_result.result)
        #     except Exception as e:
        #         result = task_result.result
        # else:
        #     result = task_result.result
        return ResearchStatus(task_id=task_id, status="SUCCESS", result=task_result.result)
    elif task_result.state == "FAILURE":
        return ResearchStatus(task_id=task_id, status="FAILURE", error=str(task_result.result))
    else:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Unknown task state")