from datetime import date, datetime
from typing import Any, Generic, List, Optional, Type, Union
from pydantic import BaseModel, validator
from .models import Tweet


def confirm_twitter_id(value: str) -> str:
    if not value:
        raise ValueError('twitter_id is mandatory.')
    return value


class TweetBase(BaseModel):
    """
    Base fields for Tweet
    """
    twitter_id: str
    content: str
    published_at: datetime
    in_reply_to: Optional[str] = None
    username: str
    user_id: str
    _confirm_twitter_id = validator("twitter_id", allow_reuse=True)(confirm_twitter_id)


class CreateTweet(TweetBase):
    ...
    
class UpdateTweet(TweetBase):
    ...
    
class TweetOut(TweetBase):
    class Config:
        orm_mode = True
