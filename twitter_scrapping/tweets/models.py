import re
from datetime import datetime
from django.db import models
from django.utils import timezone
from django.utils.text import Truncator
from django_extensions.db.models import TimeStampedModel
from .values import BAD_WORDS


class ScrappingRequest(TimeStampedModel):
    TASK_STATUS_CHOICES = [
        ("created", "Created"),
        ("started", "Started"),
        ("finished", "Finished"),
        ("interrupted", "Interrupted"),
    ]
    username = models.CharField(max_length=50, null=True, blank=True)
    since = models.DateTimeField(null=True, blank=True)
    until = models.DateTimeField(null=True, blank=True)
    recurse = models.BooleanField(default=False)
    include_replies = models.BooleanField(default=True)
    started = models.DateTimeField(null=True, blank=True)
    finished = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=12, choices=TASK_STATUS_CHOICES, default="created"
    )

    @property
    def duration(self):
        if self.started and self.finished:
            return self.finished - self.started
        return None

    def create_scrapping_task(self):
        from .tasks import scrape_tweets_and_replies

        if self.status != "created":
            return
        scrape_tweets_and_replies.delay(self.id)

    def start(self):
        self.status = "started"
        self.started = timezone.now()
        self.save()

    def finish(self):
        self.status = "finished"
        self.finished = timezone.now()
        self.save()

    def interrupt(self):
        self.status = "interrupted"
        self.finished = timezone.now()
        self.save()


class TwitterUser(TimeStampedModel):
    twitter_id = models.CharField(max_length=30, unique=True)
    username = models.CharField(max_length=50)
    display_name = models.CharField(max_length=50)
    description = models.CharField(max_length=300)
    account_created_at = models.DateTimeField("Twitter account creation date")
    location = models.CharField(max_length=50, blank=True)
    followers_count = models.IntegerField(default=0)
    following_count = models.IntegerField(default=0)
    tweet_count = models.IntegerField(default=0)
    listed_count = models.IntegerField(default=0)

    def __repr__(self) -> str:
        return f"<TwitterUser: id={self.id}, username={self.username}, twitter_id={self.twitter_id}>"

    def __str__(self) -> str:
        return self.username


class TweetManager(models.Manager):
    def contains_hate_words(self):
        regex = r"\b(?:{})\b".format("|".join(BAD_WORDS))
        return self.filter(content__iregex=regex)

    def politician_tweets(self):
        from django.db.models import Q
        from tweets.values import TOTAL_SP_STATE_DEP, SCRAPPING_PERIODS

        or_conditions = Q()
        for dep in TOTAL_SP_STATE_DEP:
            or_conditions.add(Q(conversation_tweet__user__username__iexact=dep), Q.OR)

        since = min([period["since"] for period in SCRAPPING_PERIODS])
        until = max([period["until"] for period in SCRAPPING_PERIODS])
        since = timezone.make_aware(datetime.strptime(since, "%Y-%m-%d"))
        until = timezone.make_aware(datetime.strptime(until, "%Y-%m-%d"))

        return self.filter(published_at__gte=since, published_at__lte=until).filter(
            or_conditions
        )


class Tweet(TimeStampedModel):
    twitter_id = models.CharField(max_length=30, unique=True)
    content = models.CharField(max_length=300)
    published_at = models.DateTimeField("tweet publish date")
    in_reply_to_id = models.CharField(max_length=30, null=True, blank=True)
    in_reply_to_tweet = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, related_name="tweet_replies_set"
    )
    conversation_id = models.CharField(max_length=30, null=True, blank=True)
    conversation_tweet = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        related_name="conversation_tweets_set",
    )
    user = models.ForeignKey(
        TwitterUser, on_delete=models.CASCADE, related_name="tweet_user"
    )
    reply_count = models.IntegerField(default=0)
    retweet_count = models.IntegerField(default=0)
    like_count = models.IntegerField(default=0)
    quote_count = models.IntegerField(default=0)
    scrapping_request = models.ForeignKey(
        ScrappingRequest, on_delete=models.SET_NULL, null=True, related_name="tweets"
    )

    objects = TweetManager()

    def __repr__(self) -> str:
        return f"<Tweet: id={self.id}, user={self.user}, content='{Truncator(self.content).chars(16)}', twitter_id={self.twitter_id}>"

    def __str__(self) -> str:
        return Truncator(self.content).chars(16)

    def get_twitter_url(self):
        return f"https://twitter.com/{self.user.username}/status/{self.twitter_id}"

    def export(self):
        return {
            "url": self.get_twitter_url(),
            "date": self.published_at,
            "content": self.content,
            "user": self.user.username,
            "reply_count": self.reply_count,
            "retweet_count": self.retweet_count,
            "like_count": self.like_count,
            "quote_count": self.quote_count,
            "in_reply_to_id": self.in_reply_to_id,
            "in_reply_to_user": self.get_in_reply_to_user(),
            "conversation_id": self.conversation_id,
            "conversation_user": self.get_conversation_user(),
        }

    def is_reply(self):
        return bool(self.in_reply_to_id)

    def get_in_reply_to_tweet(self):
        if self.in_reply_to_tweet:
            return self.in_reply_to_tweet
        try:
            tweet = Tweet.objects.get(twitter_id=self.in_reply_to_id)
            self.in_reply_to_tweet = tweet
            self.save()
            return tweet
        except Tweet.DoesNotExist:
            # Happens when it's replying to a deleted or protected tweet
            return None

    def get_in_reply_to_user(self):
        if self.in_reply_to_tweet:
            return self.in_reply_to_tweet.user.username
        if self.in_reply_to_id:
            tweet = self.get_in_reply_to_tweet()
            if tweet:
                return tweet.user.username
        return None

    def get_conversation_tweet(self):
        if self.conversation_tweet:
            return self.conversation_tweet
        try:
            tweet = Tweet.objects.get(twitter_id=self.conversation_id)
            self.conversation_tweet = tweet
            self.save()
            return tweet
        except Tweet.DoesNotExist:
            # Happens when the conversation started with a deleted or protected tweet
            return None

    def get_conversation_user(self):
        if self.conversation_tweet:
            return self.conversation_tweet.user.username
        if self.conversation_id:
            tweet = self.get_conversation_tweet()
            if tweet:
                return tweet.user.username
        return None
