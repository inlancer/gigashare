from typing import Union
import os, hashlib,shutil
from dotenv import load_dotenv

BASEDIR = os.path.abspath(os.path.dirname(__file__))

from datetime import datetime

from fastapi import FastAPI, Request, File, UploadFile, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


from pydantic import BaseModel

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


from sqlalchemy.orm import Session
from models import *
from database import SessionLocal, engine


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# HOME PAGE FOR FILE SHARING
@app.get("/", response_class=HTMLResponse)
async def file_sharing_page(request: Request):
    load_dotenv(os.path.join(BASEDIR, 'config.env')) 
    return templates.TemplateResponse(
        request=request, name="index.html", context={"base_url": os.getenv("BASE_URL")}
    )


# DEVICE REGISTRATION FOR FILE UNIQUENESS OF RESUMABLE UPLOADS
@app.post("/register-device")
async def register_device(device_id: str = Form(...), db: Session = Depends(get_db)):

    return_device_id = 0
    device = db.query(Devices).filter(Devices.device_id == device_id).first()
    if device != None:
        return_device_id = device.id
    else:
        db_device = Devices(device_id=device_id)
        db.add(db_device)
        db.commit()
        db.refresh(db_device)
        return_device_id = db_device.id

    return {"device_id": return_device_id}


# HANDSHAKE for file storing and sharing last chunk id in case of already half uploaded file
@app.post("/file-handshake/")
async def handshake_file(
    name: str = Form(...),
    total_chunks: int = Form(...),
    chunksize: int = Form(...),
    size: int = Form(...),
    device_id: int = Form(...),
    lastModified: int = Form(...),
    type: str = Form(...),
    db: Session = Depends(get_db),
):
    load_dotenv(os.path.join(BASEDIR, 'config.env'))
    upload_path = os.path.abspath("static/uploads/chunks")
    storage_path = os.path.abspath("static/uploads/final")

    if not os.path.exists(upload_path):
        os.makedirs(upload_path, 0o777, exist_ok=True)
    if not os.path.exists(storage_path):
        os.makedirs(storage_path, 0o777, exist_ok=True)

    file_exists = (
        db.query(FileModel)
        .filter(
            FileModel.name == name,
            FileModel.size == size,
            FileModel.mimetype == type,
            FileModel.device_id == device_id,
            FileModel.lastmodified == lastModified,
            FileModel.deleted_at.is_(None),
        )
        .first()
    )
    if file_exists:
        db.close()
        nextChunk=file_exists.uploaded_chunks if file_exists.uploaded_chunks!=None else 1
        
        if file_exists.total_chunks==file_exists.merged_chunks:
            return {
                'status'    : 500,
                'message'   : 'File already uploaded',
                'file_url'  : os.getenv("BASE_URL"),
            }

        return {
            "status": 200,
            "id": file_exists.id,
            "next_chunk": nextChunk,
            "message": "File exists",
        }

    unique_name = hashlib.md5(name.encode()).hexdigest()
    new_file = FileModel(
        name=name,
        device_id=device_id,
        unique_name=unique_name,
        total_chunks=total_chunks,
        chunk_size=chunksize,
        size=size,
        lastmodified=lastModified,
        mimetype=type,
        upload_start_time=int(datetime.now().timestamp()),
    )
    db.add(new_file)
    db.commit()

    return {
        "status": 200,
        "id": new_file.id,
        "next_chunk": 1,
        "message": "File initiated",
    }


@app.post("/upload-chunk")
async def file_upload(
	    chunk: UploadFile = Form(...),
	    id: int = Form(...),
	    name: str = Form(...),
	    current_chunk: int = Form(...),
	    total_chunks: int = Form(...),
	    db: Session = Depends(get_db),
	):

    url = '' ;
    upload_path = os.path.abspath("static/uploads/chunks")
    storage_path = os.path.abspath("static/uploads/final")

    file = db.query(FileModel).filter(FileModel.id == id).first()
    if file == None:
        return {"status": 500, "message": "Invalid file"}
    else:
        fileTempName = file.unique_name
        url = 'static/uploads/final/'+fileTempName+'/'+name
        upload_path = os.path.join(upload_path, fileTempName)
        storage_path = os.path.join(storage_path, fileTempName)
        if not os.path.exists(upload_path):
        	os.makedirs(upload_path, 0o777, exist_ok=True) 
        if not os.path.exists(storage_path):
            os.makedirs(storage_path, 0o777, exist_ok=True) 

        chunk.file.seek(0)
        with open(os.path.join(upload_path, f"{name}.part{current_chunk}"), "wb") as f:
            f.write(chunk.file.read())

        db.query(FileModel).filter(FileModel.id==id).update({'uploaded_chunks' : current_chunk})
        db.commit()
        
        buffer_size = 8192
        assembled_file_path = os.path.join(storage_path,name)

        if current_chunk==total_chunks:
        	db.query(FileModel).filter(FileModel.id==id).update({'upload_end_time' : int(datetime.now().timestamp())})
        
        if current_chunk==total_chunks: 
            with open(assembled_file_path,'wb') as assembled_file:
                for i in range(1,(total_chunks+1)):
                    chunk_path=os.path.join(upload_path,f"{name}.part{i}")
                    with open(chunk_path,'rb') as chunk_file:
                        while True:
                            chunk_data = chunk_file.read(2*1024*1024)
                            if not chunk_data:
                                break
                            assembled_file.seek(0,2)
                            assembled_file.write(chunk_data) 
                        db.query(FileModel).filter(FileModel.id==id).update({'merged_chunks' : i})
                        db.commit()

    return {
        'status':200,
        'message':'RECORDD FERCHED',
        'urlss'   : url  
    }