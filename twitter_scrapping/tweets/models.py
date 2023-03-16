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
        return f'<TwitterUser: id={self.id}, username={self.username}, twitter_id={self.twitter_id}>'
    
    def __str__(self) -> str:
        return self.username
    


class Tweet(TimeStampedModel):
    twitter_id = models.CharField(max_length=30, unique=True)
    content = models.CharField(max_length=300)
    published_at = models.DateTimeField('tweet publish date')
    in_reply_to_id = models.CharField(max_length=30, null=True, blank=True)
    in_reply_to_tweet = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, related_name='tweet_replies_set')
    conversation_id = models.CharField(max_length=30, null=True, blank=True)
    conversation_tweet = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, related_name='conversation_tweets_set')
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
        return bool(self.in_reply_to_id)
    
    def get_in_reply_to_tweet(self, scrape=False):
        if self.in_reply_to_tweet:
            return self.in_reply_to_tweet
        try:
            tweet = Tweet.objects.get(twitter_id=self.in_reply_to_id)
            self.in_reply_to_tweet = tweet
            self.save()
            return tweet
        except Tweet.DoesNotExist:
            if scrape:
                raise NotImplementedError
            else:
                return None
            
    def get_conversation_tweet(self, scrape=False):
        if self.conversation_tweet:
            return self.conversation_tweet
        try:
            tweet = Tweet.objects.get(twitter_id=self.conversation_id)
            self.conversation_tweet = tweet
            self.save()
            return tweet
        except Tweet.DoesNotExist:
            if scrape:
                raise NotImplementedError
            else:
                return None
        
        