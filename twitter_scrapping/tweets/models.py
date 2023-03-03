from django.db import models
from django.utils.text import Truncator
from django_extensions.db.models import TimeStampedModel 


class TwitterUser(TimeStampedModel):
    twitter_id = models.CharField(max_length=30, unique=True)
    username = models.CharField(max_length=50)
    display_name = models.CharField(max_length=50)
    description = models.CharField(max_length=300)
    account_created_at = models.DateTimeField('Twitter account creation date')
    location = models.CharField(max_length=50, blank=True)
    followers_count = models.IntegerField(default=0)
    
    # Apagar e recriar migrations
    following_count = models.IntegerField(default=0)
    tweet_count = models.IntegerField(default=0)
    listed_count = models.IntegerField(default=0)
    
    def __repr__(self) -> str:
        return f'<Tweet: id={self.id}, username={self.username}, twitter_id={self.twitter_id}>'
    
    def __str__(self) -> str:
        return self.username
    


class Tweet(TimeStampedModel):
    twitter_id = models.CharField(max_length=30, unique=True)
    content = models.CharField(max_length=300)
    published_at = models.DateTimeField('tweet publish date')
    in_reply_to = models.CharField(max_length=30, null=True, blank=True)
    user = models.ForeignKey(TwitterUser, on_delete=models.CASCADE, related_name='tweet_user')
    reply_count = models.IntegerField(default=0)
    retweet_count = models.IntegerField(default=0)
    like_count = models.IntegerField(default=0)
    quote_count = models.IntegerField(default=0)

    def __repr__(self) -> str:
        return f'<Tweet: id={self.id}, user={self.user}, content=\'{Truncator(self.content).chars(16)}\', twitter_id={self.twitter_id}>'
    
    def __str__(self) -> str:
        return Truncator(self.content).chars(16)
    
    def is_reply(self):
        return bool(self.in_reply_to)