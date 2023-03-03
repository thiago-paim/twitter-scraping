from tweets.endpoints import router as tweet_router
from fastapi import APIRouter

router = APIRouter()

router.include_router(tweet_router, prefix="/tweets", tags=["Tweets"])