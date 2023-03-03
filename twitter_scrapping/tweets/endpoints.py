from typing import Any, List
from fastapi import APIRouter
from .api_crud import tweet
from .schemas import (TweetBase, CreateTweet, UpdateTweet, TweetOut)

router = APIRouter()


@router.get("/", response_model=List[TweetOut])
def get_multiple_tweets(offset: int = 0, limit: int = 10) -> Any:
	"""
	Endpoint to get multiple tweets based on offset and limit values.
	"""
	return tweet.get_multiple(offset=offset, limit=limit)

@router.get("/{twitter_id}/", response_model=TweetOut)
def get_tweet(twitter_id: str) -> Any:
	"""Get a single blog tweet."""
	return tweet.get(twitter_id=twitter_id)


# @router.get("/tags/{slug}/", response_model=List[PostByCategoryList])
# def get_posts_by_category(slug: str) -> Any:
# 	"""
# 	Get all posts belonging to a particular category
# 	"""
# 	query = post.get_posts_by_category(slug=slug)
# 	return list(query)

# @router.put("/posts/{slug}/", response_model=SinglePost)
# def update_post(slug: str, request: UpdatePost) -> Any:
# 	"""
# 	Update a single blog post.
# 	"""
# 	return post.update(slug=slug, obj_in=request)

# @router.put("/tags/{slug}/", response_model=CategoryOut)
# def update_category(slug: str, request: UpdateCategory) -> Any:
# 	"""
# 	Update a single blog category.
# 	"""
# 	return category.update(slug=slug, obj_in=request)

# @router.delete("/posts/{slug}/")
# def delete_post(slug: str) -> Any:
# 	"""
# 	Delete a single blog post.
# 	"""
# 	return post.delete(slug=slug)

# @router.delete("/tags/{slug}/", response_model=CategoryOut)
# def delete_category(slug: str) -> Any:
# 	"""
# 	Delete a single blog category.
# 	"""
# 	return category.delete(slug=slug)