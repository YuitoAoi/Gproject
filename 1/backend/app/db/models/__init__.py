from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.session import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"

class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ModelStatus(str, enum.Enum):
    UNLOADED = "unloaded"
    LOADING = "loading"
    ACTIVE = "active"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系
    datasets = relationship("Dataset", back_populates="owner")
    training_tasks = relationship("TrainingTask", back_populates="owner")
    trained_models = relationship("TrainedModel", back_populates="owner")

class Dataset(Base):
    __tablename__ = "datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    format = Column(String(50), nullable=False)
    total_records = Column(Integer, default=0)
    status = Column(String(50), default="pending", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 外键
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 关系
    owner = relationship("User", back_populates="datasets")
    training_tasks = relationship("TrainingTask", back_populates="dataset")

class TrainingTask(Base):
    __tablename__ = "training_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    model_name = Column(String(100), nullable=False)
    dataset_config = Column(Text, nullable=False)
    training_config = Column(Text, nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    progress = Column(Integer, default=0)
    log_path = Column(String(500))
    output_path = Column(String(500))
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 外键
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    
    # 关系
    owner = relationship("User", back_populates="training_tasks")
    dataset = relationship("Dataset", back_populates="training_tasks")
    trained_model = relationship("TrainedModel", back_populates="training_task", uselist=False)

class TrainedModel(Base):
    __tablename__ = "trained_models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    model_path = Column(String(500), nullable=False)
    model_size = Column(Integer, default=0)
    performance_metrics = Column(Text)
    status = Column(Enum(ModelStatus), default=ModelStatus.UNLOADED, nullable=False)
    last_used_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 外键
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    training_task_id = Column(Integer, ForeignKey("training_tasks.id"), nullable=False)
    
    # 关系
    owner = relationship("User", back_populates="trained_models")
    training_task = relationship("TrainingTask", back_populates="trained_model")