from typing import Generic, List, Optional, Type, TypeVar
from unicodedata import category
from twitter_scrapping.base_crud import BaseCRUD
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Model, Prefetch, query
from fastapi import Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from .models import Tweet
from .schemas import TweetBase, CreateTweet, UpdateTweet

class TweetCRUD(BaseCRUD[Tweet, CreateTweet, UpdateTweet]):
    """
    CRUD Operation for blog Tweets
    """

    def get(self, twitter_id: str) -> Optional[Tweet]:
        """
        Get a single blog Tweet.
        """
        try:
            query = Tweet.objects.get(twitter_id=twitter_id)
            return query
        except ObjectDoesNotExist:
            raise HTTPException(status_code=404, detail="This Tweet does not exists.")

    def get_multiple(self, limit:int = 100, offset: int = 0) -> List[Tweet]:
        """
        Get multiple Tweets using a query limit and offset flag.
        """
        query = Tweet.objects.all()[offset:offset+limit]
        if not query:
            raise HTTPException(status_code=404, detail="There are no Tweets.")

        return list(query)

tweet = TweetCRUD(Tweet)
    # def create(self, obj_in: CreateTweet) -> Tweet:
    #     """
    #     Create a Tweet.
    #     """
    #     slug = unique_slug_generator(obj_in.title)
    #     Tweet = Tweet.objects.filter(slug=slug)

    #     if not Tweet:
    #         slug = unique_slug_generator(obj_in.title, new_slug=True)
    #         obj_in = jsonable_encoder(obj_in)
    #         query = Tweet.objects.create(**obj_in)
    #     return query

    # def update(self, obj_in: UpdateTweet, slug: SLUGTYPE) -> Tweet:
    #     """
    #     Update an item.
    #     """
    #     self.get(slug=slug)
    #     if not isinstance(obj_in, list):
    #         obj_in = jsonable_encoder(obj_in)
    #     return Tweet.objects.filter(slug=slug).update(**obj_in)

    # def delete(self, slug: SLUGTYPE) -> Tweet:
    #     """Delete an item."""
    #     self.model.objects.filter(slug=slug).delete()
    #     return {"detail": "Successfully deleted!"}