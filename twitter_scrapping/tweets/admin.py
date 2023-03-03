from django.contrib import admin
from .models import Tweet, TwitterUser


@admin.register(TwitterUser)
class TwitterUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'twitter_id', 'username', 'display_name', 'location')    
    
@admin.register(Tweet)
class TweetAdmin(admin.ModelAdmin):
    list_display = ('id', 'twitter_id', 'user', 'published_at', 'content')
    
    
