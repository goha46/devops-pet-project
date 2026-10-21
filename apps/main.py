import os
import re
import subprocess
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy.orm import Session

from apps.database import SessionLocal, init_db
from apps.models import Post
from apps.schemas import PostCreate, PostOut


def get_app_version():
    try:
        subject = subprocess.check_output(
            ["git", "log", "-1", "--pretty=%s"],
            stderr=subprocess.DEVNULL,
            text=True,
            cwd=os.getcwd(),
        ).strip()

        match = re.search(r"Version\s+\d+\.\d+", subject)
        if match:
            return match.group(0)
        return "unknown"
    except Exception:
        return "unknown"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)
app.state.app_version = get_app_version()

Instrumentator().instrument(app).expose(app)
app.mount(
    "/ui",
    StaticFiles(directory=Path(__file__).resolve().parent.parent / "frontend", html=True),
    name="ui",
)


@app.get("/")
async def read_root():
    start = time.perf_counter()
    result = {
        "app_version": app.state.app_version,
        "response_time_ms": 0,
    }
    elapsed_ms = (time.perf_counter() - start) * 1000
    result["response_time_ms"] = round(elapsed_ms, 3)
    return result


@app.get("/health")
async def read_health():
    return {"status": "ok"}


@app.get("/posts", response_model=list[PostOut])
async def read_posts(limit: Annotated[int, Query(ge=1, le=100)] = 10):
    db: Session = SessionLocal()
    try:
        posts = db.query(Post).order_by(Post.id.desc()).limit(limit).all()
        return [
            PostOut(
                id=item.id,
                title=item.title,
                content=item.content,
                created_at=item.created_at,
            )
            for item in posts
        ]
    finally:
        db.close()


@app.post("/posts", response_model=PostOut, status_code=201)
async def create_post(post: PostCreate):
    db: Session = SessionLocal()
    try:
        db_post = Post(title=post.title, content=post.content)
        db.add(db_post)
        db.commit()
        db.refresh(db_post)
        return PostOut(
            id=db_post.id,
            title=db_post.title,
            content=db_post.content,
            created_at=db_post.created_at,
        )
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create post: {exc}") from exc
    finally:
        db.close()
