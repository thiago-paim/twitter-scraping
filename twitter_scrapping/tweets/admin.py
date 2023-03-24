from django.contrib import admin
from .models import Tweet, TwitterUser 


class BaseUsernameFilter(admin.SimpleListFilter):
    template = 'tweets/admin_input_filter.html'

    def lookups(self, request, model_admin):
        return ((None, None),)
    
class UserUsernameFilter(BaseUsernameFilter):
    title = 'username'
    parameter_name = 'username'
    
    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(user__username=value)

class ReplyToUsernameFilter(BaseUsernameFilter):
    title = 'Reply to username'
    parameter_name = 'reply_to_username'
    
    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(in_reply_to_tweet__user__username=value)
        
class ConversationUsernameFilter(BaseUsernameFilter):
    title = 'conversation username'
    parameter_name = 'conversation_username'
    
    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(conversation_tweet__user__username=value)
        

@admin.register(Tweet)
class TweetAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'twitter_id', 'user', 'published_at', 'get_reply_to_user', 
        'get_conversation_user', 'content',
    )
    list_filter = (
        'created', 'modified', 'published_at', UserUsernameFilter, 
        ReplyToUsernameFilter, ConversationUsernameFilter,
    )
    raw_id_fields = ('user', 'in_reply_to_tweet', 'conversation_tweet')
    
    def get_reply_to_user(self, obj):
        try:
            return obj.in_reply_to_tweet.user.username
        except Exception as e:
            return None
    get_reply_to_user.short_description = 'Reply to User'
    
    def get_conversation_user(self, obj):
        try:
            return obj.conversation_tweet.user.username
        except Exception as e:
            return None
    get_conversation_user.short_description = 'Conversation User'
    
    
@admin.register(TwitterUser)
class TwitterUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'twitter_id', 'username', 'display_name', 'location')   