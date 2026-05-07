from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Response, Request
import os
import uuid
import json
from http import HTTPStatus
from pydantic import BaseModel
import tasks.celery_task as celeryTask
from celery.result import AsyncResult
import shutil
import pandas as pd
import httpx
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from contextlib import asynccontextmanager
import logging

TOKEN=os.getenv("TELEGRAM_BOT_API_KEY")
WEBHOOK_URL=os.getenv("WEBHOOK_URL")

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

ptb = (
    Application.builder()
    .updater(None)
    .token(TOKEN)
    .read_timeout(7)
    .get_updates_read_timeout(42)
    .build()
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await ptb.bot.set_webhook(WEBHOOK_URL)
    async with ptb:
        await ptb.start()
        yield
    await ptb.stop()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your research assistant bot.")
    await update.message.reply_text("I will gladly help you with your research needs. Please let me know what topic you're interested in and how I can assist you.")

ptb.add_handler(CommandHandler("start", start_command))

async def image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_size = update.message.photo[-1]
    file_id = photo_size.file_id
    file_unique_id = photo_size.file_unique_id
    width = photo_size.width
    height = photo_size.height
    file_size = photo_size.file_size

    reply_text = (
        f"<b>Received Image Metadata</b>:\n"
        f"File ID: {file_id}\n"
        f"File Unique ID: {file_unique_id}\n"
        f"Width: {width}\n"
        f"Height: {height}\n"
        f"File Size: {file_size}\n"
    )
    await update.message.reply_text(reply_text, parse_mode="HTML")

ptb.add_handler(MessageHandler(filters.PHOTO, image_handler))

async def bot_research(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please provide a research topic after the command. For example: /research AI in healthcare", parse_mode="HTML")
        return
    
    input_data = ResearchInput(topic=" ".join(context.args), style="detailed")
    task = celeryTask.research.delay(input_data.topic, input_data.style)
    await update.message.chat.send_action(action="typing")
    await update.message.reply_text(f"Research task started with ID: {task.id}")

ptb.add_handler(CommandHandler("research", bot_research))

async def bot_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please provide a task ID after the command. For example: /status task_id", parse_mode="HTML")
        return
    
    task_id = context.args[0]
    task_result = AsyncResult(task_id, app=celeryTask.celery_app)

    if task_result.state == "PENDING":
        await update.message.reply_text(f"Task {task_id} is pending.")
    elif task_result.state == "RUNNING":
        await update.message.reply_text(f"Task {task_id} is running.")
    elif task_result.state == "SUCCESS":
        result = task_result.result
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except Exception:
                pass
        await update.message.reply_text(f"Task {task_id} completed successfully. Result: ")

        for part in split_long_message(str(result)):
            await update.message.chat.send_action(action="typing")
            await update.message.reply_text(part)
    elif task_result.state == "FAILURE":
        await update.message.reply_text(f"Task {task_id} failed with error: {str(task_result.result)}")
    else:
        await update.message.reply_text(f"Task {task_id} is in an unknown state: {task_result.state}")

ptb.add_handler(CommandHandler("status", bot_status))

def split_long_message(text: str, max_len:int = 300):
    parts = []
    while len(text) > max_len:
        split_index = text.rfind("\n", 0, max_len)
        if split_index == -1:
            split_index = max_len
        parts.append(text[:split_index])
        text = text[split_index:].lstrip()

    parts.append(text)
    return parts

app = FastAPI(lifespan=lifespan)

@app.post("/webhook")
async def telegram_webhook(request: Request):
    req_json = await request.json()
    update = Update.de_json(req_json, ptb.bot)
    await ptb.process_update(update)

    return Response(status_code=HTTPStatus.OK)
    
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