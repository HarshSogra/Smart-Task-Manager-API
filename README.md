# Smart Task Manager API 🚀

A backend Task Management API built using FastAPI.

This project allows users to register, login, and manage their personal tasks with authentication.

## Features

- User Registration
- User Login with JWT Authentication
- Create Tasks
- Update Tasks
- Delete Tasks
- View Tasks
- Task Priority
- Task Deadline
- Overdue Tasks Endpoint
- Task Statistics Endpoint

## Tech Stack

- FastAPI
- Python
- SQLAlchemy
- SQLite
- JWT Authentication
- Passlib (Password Hashing)

## API Endpoints

### Auth

POST /register  
POST /login  

### Tasks

POST /task  
GET /tasks  
GET /task/{id}  
PUT /task/{id}  
DELETE /task/{id}

### Analytics

GET /tasks/overdue  
GET /tasks/stats  

## Run Locally

Clone the repository

git clone https://github.com/yourusername/smart-task-manager-api.git

Install dependencies

pip install -r requirements.txt

Run server

uvicorn main:app --reload

Then open

http://127.0.0.1:8000/docs

## Future Improvements

- PostgreSQL database
- Docker support
- Frontend integration
- Deployment
