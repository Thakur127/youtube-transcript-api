import asyncio
from fastapi import APIRouter, HTTPException, Query, status, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Annotated, List
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
)
import threading

router = APIRouter()

# Global token bucket
total_tokens = 5  # Total tokens available initially
BUCKET_CAPACITY = 25
TOKEN_REFILL_RATE = 0.5  # Token refill interval in seconds
token_lock = threading.Lock()  # Lock for thread safety


def tokens_available() -> bool:
    with token_lock:
        return total_tokens > 0


def add_token():
    async def _refill():
        await asyncio.sleep(TOKEN_REFILL_RATE)
        with token_lock:
            global total_tokens
            if total_tokens < BUCKET_CAPACITY:
                total_tokens += 1

    asyncio.run(_refill())


@router.get("/youtube-transcription")
def youtube_transcription(
    video_id: str = ...,
    lang: Annotated[List[str], Query()] = ["en"],
    token_available: bool = Depends(tokens_available),
    background_tasks: BackgroundTasks = None,
):
    if token_available:
        try:
            response = YouTubeTranscriptApi.get_transcript(
                video_id=video_id,
                languages=lang,
                proxies=[
                    "http://185.95.186.143:60606",
                    "http://116.125.141.115:80",
                    "http://219.65.73.81:80",
                ],
            )

            # Use the lock to ensure thread safety when modifying the token bucket
            with token_lock:
                global total_tokens
                total_tokens -= 1  # Consume a token

            background_tasks.add_task(add_token)  # Refill the token in the background
            return JSONResponse(content=response, status_code=status.HTTP_200_OK)

        except NoTranscriptFound as e:
            raise HTTPException(
                detail=f"No transcription found for languages: {lang}",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        except TranscriptsDisabled as e:
            raise HTTPException(
                detail=f"Failed to retrieve transcription for the video: {video_id}",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            raise HTTPException(
                detail=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    raise HTTPException(
        detail="Too many requests", status_code=status.HTTP_429_TOO_MANY_REQUESTS
    )
