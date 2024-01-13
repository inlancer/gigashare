from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime,func,BigInteger
from sqlalchemy.orm import relationship,Session

from database import Base,engine 


class Devices(Base):
    __tablename__ = "devices"

    id          =   Column(Integer, primary_key=True, index=True)
    device_id   =   Column(String(255), unique=True, index=True)  
    
    # filesr       =   relationship("FileModel", back_populates="device_id")



    # def get_device_info(db, device_id: str):
    #     return db.query(Devices).filter(Devices.device_id == device_id).first()




class FileModel(Base):
    __tablename__ = "files"

    id                  = Column(Integer, primary_key=True, index=True)
    device_id           = Column(Integer, ForeignKey("devices.id"))
    name                = Column(String(500), index=True)
    unique_name         = Column(String(500), index=True)
    size                = Column(Integer)
    chunk_size          = Column(Integer)
    total_chunks        = Column(Integer)
    uploaded_chunks     = Column(Integer)
    merged_chunks       = Column(Integer)
    upload_start_time   = Column(BigInteger)
    upload_end_time     = Column(BigInteger) 
    merge_process_time  = Column(Integer)
    mimetype            = Column(String(255), default=None)
    lastmodified        = Column(BigInteger) 
    created_at          = Column(DateTime, server_default=func.now()) 
    updated_at          = Column(DateTime, onupdate=func.now(),default=None)
    deleted_at          = Column(DateTime, default=None) 

 
    # device          = relationship("Devices", back_populates="filesr")

Base.metadata.create_all(bind=engine)
