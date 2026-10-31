import asyncio
import os
from contextlib import asynccontextmanager
from datetime import date
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from app.auth import authenticate, create_employee, get_user_from_token, init_auth_db, issue_token, list_employees
from app.rag import load_rag_chain


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_auth_db()
    try:
        print("Loading RAG chain...")
        app.state.rag_chain = load_rag_chain()
        print("RAG chain loaded successfully")
    except Exception as e:
        print(f"Failed to load RAG: {e}")
        # 即使知识库尚未配置，也允许使用账号管理功能。
        app.state.rag_error = str(e)
    yield
    print("Shutting down...")


app = FastAPI(title="AI Support Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)


class EmployeeCreateRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=12, max_length=200)
    display_name: str = Field(min_length=1, max_length=120)
    department: str = Field(min_length=1, max_length=120)
    job_level: str = Field(min_length=1, max_length=80)
    position: str = Field(min_length=1, max_length=120)
    hire_date: date


bearer = HTTPBearer(auto_error=False)


async def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Please log in.")
    user = get_user_from_token(credentials.credentials)
    if user is None:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")
    return user


async def admin_user(user=Depends(current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Administrator access required.")
    return user


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "rag_loaded": hasattr(app.state, "rag_chain"),
        "rag_error": getattr(app.state, "rag_error", None),
    }


@app.post("/auth/login")
async def login(req: LoginRequest):
    user = authenticate(req.username, req.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    return {"access_token": issue_token(user), "token_type": "bearer", "user": user}


@app.get("/auth/me")
async def get_me(user=Depends(current_user)):
    return {"user": user}


@app.get("/employees")
async def get_employees(_admin=Depends(admin_user)):
    return {"employees": list_employees()}


@app.post("/employees", status_code=201)
async def add_employee(req: EmployeeCreateRequest, _admin=Depends(admin_user)):
    try:
        user = create_employee(
            username=req.username,
            password=req.password,
            display_name=req.display_name,
            department=req.department,
            job_level=req.job_level,
            position=req.position,
            hire_date=req.hire_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"user": user}


@app.post("/ask")
async def ask(req: AskRequest, _user=Depends(current_user)):
    if not hasattr(app.state, "rag_chain"):
        raise HTTPException(503, "Knowledge base is not ready. Add PDFs and build the vector index first.")

    print(f"Received question: {req.question}")

    try:
        print("Starting chain invocation...")
        result = await app.state.rag_chain.ainvoke({
            "messages": [{"role": "user", "content": req.question}]
        }, config={"recursion_limit": 8})
        messages = result.get("messages", [])
        answer = messages[-1].content if messages else ""
        if isinstance(answer, list):
            answer = "".join(part.get("text", "") for part in answer if isinstance(part, dict))
        tools_used = list(dict.fromkeys(
            message.name for message in messages
            if getattr(message, "type", None) == "tool" and getattr(message, "name", None)
        ))
        print(f"Agent returned: {answer[:200]}...")  # 日志中仅显示前 200 个字符。
        return {"answer": answer.strip(), "tools_used": tools_used}
    except (TimeoutError, asyncio.TimeoutError):
        print("RAG execution timed out (Ollama unresponsive)")
        raise HTTPException(504, "AI model timed out. Please try again later.")
    except Exception as e:
        import traceback
        print("\n" + "═" * 80)
        print("RAG EXECUTION FAILED:")
        traceback.print_exc()
        print("═" * 80 + "\n")
        raise HTTPException(500, f"Backend processing error: {str(e)}")
