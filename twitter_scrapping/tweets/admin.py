from django.contrib import admin
from .models import Tweet, TwitterUser, ScrappingRequest
from .utils import export_csv


class BaseUsernameFilter(admin.SimpleListFilter):
    template = "tweets/admin_input_filter.html"

    def lookups(self, request, model_admin):
        return ((None, None),)


class UserUsernameFilter(BaseUsernameFilter):
    title = "username"
    parameter_name = "username"

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(user__username__iexact=value)


class ReplyToUsernameFilter(BaseUsernameFilter):
    title = "Reply to username"
    parameter_name = "reply_to_username"

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(in_reply_to_tweet__user__username__iexact=value)


class ConversationUsernameFilter(BaseUsernameFilter):
    title = "conversation username"
    parameter_name = "conversation_username"

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(conversation_tweet__user__username__iexact=value)


@admin.register(Tweet)
class TweetAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "twitter_id",
        "user",
        "published_at",
        "get_reply_to_user",
        "get_conversation_user",
        "content",
    )
    list_filter = (
        "created",
        "modified",
        "published_at",
        UserUsernameFilter,
        ReplyToUsernameFilter,
        ConversationUsernameFilter,
    )
    raw_id_fields = (
        "user",
        "in_reply_to_tweet",
        "conversation_tweet",
        "scrapping_request",
    )
    actions = ["export_tweets"]

    def get_reply_to_user(self, obj):
        try:
            return obj.in_reply_to_tweet.user.username
        except Exception as e:
            return None

    get_reply_to_user.short_description = "Reply to User"

    def get_conversation_user(self, obj):
        try:
            return obj.conversation_tweet.user.username
        except Exception as e:
            return None

    get_conversation_user.short_description = "Conversation User"

    def export_tweets(self, request, queryset):
        filters = request.GET.urlencode()
        filename = f"tweets {filters}"
        export_csv(queryset, filename)

    export_tweets.short_description = "Export selected tweets"


@admin.register(TwitterUser)
class TwitterUserAdmin(admin.ModelAdmin):
    list_display = ("id", "twitter_id", "username", "display_name", "location")


@admin.register(ScrappingRequest)
class ScrappingRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "status",
        "username",
        "since",
        "until",
        "started",
        "finished",
        "tweets_saved",
    )
    actions = ["start_scrapping", "export_scrapping_results"]

    def tweets_saved(self, obj):
        try:
            return Tweet.objects.filter(scrapping_request=obj).count()
        except Exception as e:
            return None

    tweets_saved.short_description = "Tweets saved"

    def start_scrapping(self, request, queryset):
        for obj in queryset:
            obj.create_scrapping_task()

    start_scrapping.short_description = "Start scrapping tasks"

    def export_scrapping_results(self, request, queryset):
        scrapping_ids = list(queryset.values_list("id", flat=True))
        filename = f"scrapping_requests id={scrapping_ids}"
        tweets = Tweet.objects.filter(scrapping_request__in=queryset)
        export_csv(tweets, filename)

    export_scrapping_results.short_description = "Export scrapping results"
