from copy import deepcopy
from django.utils import timezone
from snscrape.modules.twitter import User as SNUser, Tweet as SNTweet

tz = timezone.get_default_timezone()

user1 = SNUser(
    username="GergelyOrosz",
    id=30192824,
    displayname="Gergely Orosz",
    rawDescription="Writing @Pragmatic_Eng & @EngGuidebook.",
    created=timezone.datetime(2009, 4, 10, 10, 1, 11, tzinfo=tz),
    followersCount=202171,
    friendsCount=1368,
    statusesCount=24961,
    listedCount=2268,
    location="Amsterdam, The Netherlands",
)

user1_updated_dict = {
    "followersCount": 202173,
    "friendsCount": 1368,
    "statusesCount": 24965,
    "listedCount": 2268,
}
user1_updated = deepcopy(user1)
for attr, value in user1_updated_dict.items():
    setattr(user1_updated, attr, value)


user1_incomplete = deepcopy(user1)
user1_incomplete_remove_fields = ["username", "followersCount"]
for attr in user1_incomplete_remove_fields:
    delattr(user1_incomplete, attr)


tweet1 = SNTweet(
    url="https://twitter.com/GergelyOrosz/status/1636295637187584000",
    date=timezone.datetime(2023, 3, 16, 9, 17, 35, tzinfo=tz),
    rawContent="Test tweet content",
    renderedContent="Test tweet content",
    id=1636295637187584000,
    user=user1,
    replyCount=22,
    retweetCount=13,
    likeCount=235,
    quoteCount=2,
    viewCount=161280,
    conversationId=1636295637187584000,
    retweetedTweet=None,
    inReplyToTweetId=None,
    inReplyToUser=None,
    lang="en",
)

tweet1_updated_tweet_dict = {
    "replyCount": 32,
    "retweetCount": 13,
    "likeCount": 335,
    "quoteCount": 2,
    "viewCount": 181280,
}
tweet1_updated_tweet = deepcopy(tweet1)
for attr, value in tweet1_updated_tweet_dict.items():
    setattr(tweet1_updated_tweet, attr, value)


tweet1_updated_user_dict = {
    "user": user1_updated,
}
tweet1_updated_user = deepcopy(tweet1)
for attr, value in tweet1_updated_user_dict.items():
    setattr(tweet1_updated_user, attr, value)


tweet1_updated_both_dict = {
    "user": user1_updated,
    "replyCount": 32,
    "retweetCount": 13,
    "likeCount": 335,
    "quoteCount": 2,
    "viewCount": 181280,
}
tweet1_updated_both = deepcopy(tweet1)
for attr, value in tweet1_updated_both_dict.items():
    setattr(tweet1_updated_both, attr, value)


tweet1_incomplete = deepcopy(tweet1)
tweet1_incomplete_remove_fields = ["id", "rawContent", "replyCount", "conversationId"]
for attr in tweet1_incomplete_remove_fields:
    delattr(tweet1_incomplete, attr)
