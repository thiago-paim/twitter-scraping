from django.db import models
from django.utils.text import Truncator


class Tweet(models.Model):
    created_at = models.DateTimeField('instance creation date', auto_now_add=True)
    updated_at = models.DateTimeField('instance creation date', auto_now=True)
    twitter_id = models.CharField(max_length=30, unique=True)
    content = models.CharField(max_length=300)
    published_at = models.DateTimeField('tweet publish date')
    in_reply_to = models.CharField(max_length=30, blank=True)
    username = models.CharField(max_length=50)
    user_id = models.CharField(max_length=30)
    reply_count = models.IntegerField(default=0)
    retweet_count = models.IntegerField(default=0)
    like_count = models.IntegerField(default=0)
    quote_count = models.IntegerField(default=0)

    def __repr__(self) -> str:
        return f'<Tweet: id={self.id}, username={self.username}, content=\'{Truncator(self.content).chars(16)}\', twitter_id={self.twitter_id}>'
    
    def is_reply(self):
        return bool(self.in_reply_to)