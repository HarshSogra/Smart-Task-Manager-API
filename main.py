from fastapi import FastAPI, status, HTTPException, Depends,Query
from pydantic import BaseModel,EmailStr
from database import engine, SessionLocal
from sqlalchemy.orm import Session
import models
from datetime import date,datetime,timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError,jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import SECRET_KEY
from fastapi.middleware.cors import CORSMiddleware


models.Base.metadata.create_all(bind=engine)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://smart-task-manager-api-wine.vercel.app",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Model user sends (NO id)
class TaskCreate(BaseModel):
    title: str
    completed: bool = False
    priority: str | None = None
    deadline: date | None = None

class TaskResponse(BaseModel):
    id: int
    title: str
    completed: bool
    priority: Optional[str]
    deadline: Optional[date]

    class Config:
        from_attributes = True

# Model stored internally (WITH id)
class Task(TaskCreate):
    id: int

#create function to get current user from token
security = HTTPBearer()
def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
            raise HTTPException(status_code=404, detail="User not found")
    return user


#add pass hashing funtion
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def hash_password(password: str):
    return pwd_context.hash(password)

#create token function
def create_access_token(data: dict):
    to_encode = data.copy()
    expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expires})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

#password verification
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


#user input
class UserCreate(BaseModel):
    email: EmailStr
    password: str

@app.get("/")
def home():
    return {"message": "Server is working"}


# ✅ Create Task
@app.post("/task")
def add_task(
        task: TaskCreate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):

    new_task = models.Task(
        title=task.title,
        completed=task.completed,
        priority=task.priority,
        deadline=task.deadline,
        user_id=current_user.id
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task


# {✅ Get All Tasks
@app.get("/tasks",response_model=list[TaskResponse])
def get_tasks(
        priority: Optional[str]=None,
        completed: Optional[bool]=None,
        limit: int =10,
        skip: int = 0,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Task).filter(
        models.Task.user_id == current_user.id
    )

    if priority:
        query = query.filter(models.Task.priority == priority)

    if completed is not None:
        query = query.filter(models.Task.completed == completed)

    tasks = query.offset(skip).limit(limit).all()
    return tasks



# ✅ Get Single Task
@app.get("/task/{task_id}",response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):

    task = db.query(models.Task).filter(models.Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


# ✅ Delete Task (ID based)
@app.delete("/task/{task_id}", )
def delete_task(task_id: int, db: Session = Depends(get_db)):

    task = db.query(models.Task).filter(models.Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"message": "Task deleted"}


# ✅ Update Task (ID based)
@app.put("/task/{task_id}", )
def update_task(task_id: int, updated_task: TaskCreate,
                db: Session = Depends(get_db)):

    task = db.query(models.Task).filter(models.Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.title = updated_task.title
    task.completed = updated_task.completed
    task.priority = updated_task.priority
    task.deadline = updated_task.deadline

    db.commit()
    db.refresh(task)

    return task

#Endpoint
@app.get("/tasks/overdue")
def get_overdue_tasks(db: Session = Depends(get_db)):

    today = date.today()

    overdue_tasks = db.query(models.Task).filter(
        models.Task.deadline < today,
        models.Task.completed == False
    ).all()
    return overdue_tasks

#stats endpoint
@app.get("/tasks/stats")
def task_stats(db: Session = Depends(get_db)):

    total = db.query(models.Task).count()

    completed = db.query(models.Task).filter(
        models.Task.completed == True
    ).count()

    pending = db.query(models.Task).filter(
        models.Task.completed == False
    ).count()

    high_priority = db.query(models.Task).filter(
        models.Task.priority.ilike("high")
    ).count()

    return {
        "total_tasks": total,
        "completed_tasks": completed,
        "pending_tasks": pending,
        "high_priority_tasks": high_priority
    }

@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = hash_password(user.password)
    new_user = models.User(
        email=user.email,
        password = hashed_password,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully"}

#login endpoint
@app.post("/login")
def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    if not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    token = create_access_token(data={"sub": db_user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
    }
