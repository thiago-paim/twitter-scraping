import pandas as pd

from .models import Tweet


def export_tweets(queryset):
    pass


def convert_tweet_to_kwargs(tweet):
    tweet_key_mapping = {
        'id': 'twitter_id',
        'rawContent': 'content',
        'date': 'published_at',
        'inReplyToTweetId': 'in_reply_to_id',
        'conversationId': 'conversation_id',
        'replyCount': 'reply_count',
        'retweetCount': 'retweet_count',
        'likeCount': 'like_count',
        'quoteCount': 'quote_count',
    }
    tweet_kwargs = {model_key: getattr(tweet, tweet_key) for tweet_key, model_key in tweet_key_mapping.items()}
    return tweet_kwargs


def convert_twitter_user_to_kwargs(user):
    user_key_mapping = {
        'id': 'twitter_id',
        'username': 'username',
        'displayname': 'display_name',
        'rawDescription': 'description',
        'created': 'account_created_at',
        'location': 'location',
        'followersCount': 'followers_count',
    }
    user_kwargs = {
        model_key: getattr(user, user_key) for user_key, model_key in user_key_mapping.items()
    }
    return user_kwargs