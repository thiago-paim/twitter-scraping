from rest_framework import serializers
from rest_framework.fields import empty
from snscrape.modules.twitter import User as SNUser, Tweet as SNTweet
from .models import Tweet, TwitterUser
from .utils import tweet_to_json


class SnscrapeTwitterUserSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="twitter_id")
    username = serializers.CharField()
    displayname = serializers.CharField(source="display_name")
    rawDescription = serializers.CharField(
        source="description", allow_null=True, allow_blank=True
    )
    created = serializers.DateTimeField(source="account_created_at")
    location = serializers.CharField(allow_null=True, allow_blank=True)
    followersCount = serializers.IntegerField(source="followers_count")
    friendsCount = serializers.IntegerField(source="following_count")
    statusesCount = serializers.IntegerField(source="tweet_count")
    listedCount = serializers.IntegerField(source="listed_count")

    class Meta:
        model = TwitterUser
        fields = [
            "id",
            "username",
            "displayname",
            "rawDescription",
            "created",
            "location",
            "followersCount",
            "friendsCount",
            "statusesCount",
            "listedCount",
        ]

    def __init__(self, instance=None, data=empty, **kwargs):
        if isinstance(data, SNUser):
            data = data.__dict__
        super().__init__(instance, data, **kwargs)


class SnscrapeTweetSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="twitter_id")
    user = SnscrapeTwitterUserSerializer()
    rawContent = serializers.CharField(source="content")
    date = serializers.DateTimeField(source="published_at")
    inReplyToTweetId = serializers.CharField(
        source="in_reply_to_id", allow_null=True, allow_blank=True
    )
    conversationId = serializers.CharField(
        source="conversation_id", allow_null=True, allow_blank=True
    )
    replyCount = serializers.IntegerField(source="reply_count")
    retweetCount = serializers.IntegerField(source="retweet_count")
    likeCount = serializers.IntegerField(source="like_count")
    quoteCount = serializers.IntegerField(source="quote_count")
    viewCount = serializers.IntegerField(source="view_count", allow_null=True)

    class Meta:
        model = Tweet
        fields = [
            "id",
            "user",
            "rawContent",
            "date",
            "inReplyToTweetId",
            "conversationId",
            "retweeted_id",
            "retweeted_tweet",
            "quoted_id",
            "quoted_tweet",
            "replyCount",
            "retweetCount",
            "likeCount",
            "quoteCount",
            "viewCount",
            "scrapping_request",
            "raw_tweet_object",
        ]

    def __init__(self, instance=None, data=empty, **kwargs):
        if isinstance(data, SNTweet):
            data.user = data.user.__dict__
            data = data.__dict__
        super().__init__(instance, data, **kwargs)

    def save(self, **kwargs):
        try:
            tweet = Tweet.objects.get(twitter_id=self.validated_data["twitter_id"])
            self.instance = tweet
        except Tweet.DoesNotExist:
            pass
        return super().save(**kwargs)

    def get_or_create_user(self, validated_data):
        user_data = validated_data.pop("user")
        user, created = TwitterUser.objects.update_or_create(
            twitter_id=user_data.get("twitter_id"), defaults=user_data
        )
        return user, created

    def create(self, validated_data):
        user, _ = self.get_or_create_user(validated_data)
        tweet = Tweet.objects.create(user=user, **validated_data)
        tweet.fetch_related_tweets()
        return tweet, True

    def update(self, instance, validated_data):
        user, _ = self.get_or_create_user(validated_data)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        instance.fetch_related_tweets()
        return instance, False
