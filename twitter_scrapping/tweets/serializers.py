from rest_framework import serializers
from rest_framework.fields import empty
from .models import Tweet, TwitterUser



class SnscrapeTwitterUserSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='twitter_id')
    username = serializers.CharField()
    displayname = serializers.CharField(source='display_name')
    rawDescription = serializers.CharField(source='description', allow_null=True, allow_blank=True)
    created = serializers.DateTimeField(source='account_created_at')
    location = serializers.CharField(allow_null=True, allow_blank=True)
    followersCount = serializers.IntegerField(source='followers_count')
    
    class Meta:
        model = TwitterUser
        fields = [
            'id', 'username', 'displayname', 'rawDescription', 'created',
            'location', 'followersCount'
        ]
        
    def get_instance(self):
        try:
            instance = TwitterUser.objects.get(
                twitter_id=self.validated_data['twitter_id']
            )
        except TwitterUser.DoesNotExist:
            instance = None
        return instance

        
class SnscrapeTweetSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='twitter_id')
    rawContent = serializers.CharField(source='content')
    date = serializers.DateTimeField(source='published_at')
    inReplyToTweetId = serializers.CharField(source='in_reply_to_id', allow_null=True, allow_blank=True)
    conversationId = serializers.CharField(source='conversation_id', allow_null=True, allow_blank=True)
    replyCount = serializers.IntegerField(source='reply_count')
    retweetCount = serializers.IntegerField(source='retweet_count')
    likeCount = serializers.IntegerField(source='like_count')
    quoteCount = serializers.IntegerField(source='quote_count')

    class Meta:
        model = Tweet
        fields = [
            'id', 'rawContent', 'date', 'inReplyToTweetId', 'conversationId',
            'replyCount', 'retweetCount', 'likeCount', 'quoteCount'
        ]
    
    def __init__(self, instance=None, data=empty, **kwargs):
        if data and data.get('user'):
            user = data.pop('user')
            self.user_twitter_id = user.id
        super().__init__(instance, data, **kwargs)
        
    def create(self, validated_data):
        validated_data['user'] = TwitterUser.objects.get(
            twitter_id=self.user_twitter_id
        )
        return super().create(validated_data)
    
    def get_instance(self):
        try:
            instance = Tweet.objects.get(
                twitter_id=self.validated_data['twitter_id']
            )
        except Tweet.DoesNotExist:
            instance = None
        return instance
