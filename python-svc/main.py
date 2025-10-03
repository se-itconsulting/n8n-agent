from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
from sqlalchemy import create_engine, text
from datetime import datetime

app = FastAPI(title="n8n-agent Python Service")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://n8n:n8n@localhost:5432/n8n")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)


class Track(BaseModel):
    id: Optional[int] = None
    title: str
    artist: str
    bpm: Optional[float] = None
    source: Optional[str] = None


class BeatportTrack(BaseModel):
    rank: int
    title: str
    artist: str
    bpm: Optional[float] = None
    genre: Optional[str] = None
    source: str = "beatport"


class RatingIn(BaseModel):
    track_id: int
    rating: int
    user_name: Optional[str] = None
    comment: Optional[str] = None


@app.get("/")
async def root():
    return {"status": "ok", "service": "n8n-agent-python-svc"}


@app.get("/healthz")
async def healthz():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tracks", response_model=Track)
async def create_track(track: Track):
    query = text(
        """
        INSERT INTO gen_tracks(title, artist, bpm, source)
        VALUES (:title, :artist, :bpm, :source)
        RETURNING id, title, artist, bpm, source
        """
    )
    try:
        with engine.begin() as conn:
            row = conn.execute(
                query, dict(title=track.title, artist=track.artist, bpm=track.bpm, source=track.source)
            ).mappings().first()
        return Track(**row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tracks", response_model=List[Track])
async def list_tracks(limit: int = 50):
    query = text("SELECT id, title, artist, bpm, source FROM gen_tracks ORDER BY id DESC LIMIT :limit")
    try:
        with engine.connect() as conn:
            rows = conn.execute(query, {"limit": limit}).mappings().all()
        return [Track(**row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/beatport/top100", response_model=List[BeatportTrack])
async def beatport_top100(genre: str = "hard-techno", limit: int = 10):
    # Placeholder implementation. Replace with real Beatport integration if available.
    sample = [
        BeatportTrack(rank=i + 1, title=f"Track {i+1}", artist="Various", bpm=140.0, genre=genre)
        for i in range(min(max(limit, 1), 100))
    ]
    return sample


@app.post("/ratings")
async def create_rating(payload: RatingIn):
    if not (1 <= payload.rating <= 5):
        raise HTTPException(status_code=400, detail="rating must be between 1 and 5")
    query = text(
        """
        INSERT INTO ratings(track_id, rating, user_name, comment, created_at)
        VALUES (:track_id, :rating, :user_name, :comment, :created_at)
        RETURNING id
        """
    )
    try:
        with engine.begin() as conn:
            row = conn.execute(
                query,
                dict(
                    track_id=payload.track_id,
                    rating=payload.rating,
                    user_name=payload.user_name,
                    comment=payload.comment,
                    created_at=datetime.utcnow(),
                ),
            ).mappings().first()
        return {"ok": True, "id": row["id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
