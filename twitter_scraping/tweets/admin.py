from django.contrib import admin
from django.utils.html import format_html
from .models import Tweet, TwitterUser, ScrapingRequest
from .utils import export


class BaseInputFieldFilter(admin.SimpleListFilter):
    template = "tweets/admin_input_filter.html"

    def lookups(self, request, model_admin):
        return ((None, None),)


class TwitterIdFilter(BaseInputFieldFilter):
    title = "twitter id"
    parameter_name = "twitter_id"

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(twitter_id=value)


class UsernameFilter(BaseInputFieldFilter):
    title = "username"
    parameter_name = "username"

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(username__iexact=value)


class UserUsernameFilter(BaseInputFieldFilter):
    title = "user username"
    parameter_name = "username"

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(user__username__iexact=value)


class ReplyToUsernameFilter(BaseInputFieldFilter):
    title = "reply to username"
    parameter_name = "reply_to_username"

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(in_reply_to_tweet__user__username__iexact=value)


class ConversationUsernameFilter(BaseInputFieldFilter):
    title = "conversation username"
    parameter_name = "conversation_username"

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(conversation_tweet__user__username__iexact=value)


class ScrapingRequestFilter(BaseInputFieldFilter):
    title = "scraping request"
    parameter_name = "scraping_request"

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(scraping_request__id=value)


@admin.register(Tweet)
class TweetAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "show_tweet_url",
        "show_username_url",
        "published_at",
        "get_reply_to_user",
        "get_conversation_user",
        "content",
    )
    list_filter = (
        UserUsernameFilter,
        ReplyToUsernameFilter,
        ConversationUsernameFilter,
        TwitterIdFilter,
        ScrapingRequestFilter,
        "created",
        "modified",
        "published_at",
    )
    raw_id_fields = (
        "user",
        "in_reply_to_tweet",
        "conversation_tweet",
        "retweeted_tweet",
        "quoted_tweet",
        "scraping_request",
    )
    actions = ["export_tweets"]

    def show_tweet_url(self, obj):
        return format_html(f"<a href='{obj.get_twitter_url()}'>{obj.twitter_id}</a>")

    show_tweet_url.short_description = "Twitter ID"

    def show_username_url(self, obj):
        return format_html(
            f"<a href='{obj.user.get_twitter_url()}'>{obj.user.username}</a>"
        )

    show_username_url.short_description = "Username"

    def get_reply_to_user(self, obj):
        try:
            return obj.in_reply_to_tweet.user.username
        except Exception as e:
            return obj.in_reply_to_id

    get_reply_to_user.short_description = "Reply to User"

    def get_conversation_user(self, obj):
        try:
            return obj.conversation_tweet.user.username
        except Exception as e:
            return obj.conversation_id

    get_conversation_user.short_description = "Conversation User"

    def export_tweets(self, request, queryset):
        filters = request.GET.urlencode()
        filename = f"tweets {filters}"
        export(queryset, filename)

    export_tweets.short_description = "Export selected tweets"


@admin.register(TwitterUser)
class TwitterUserAdmin(admin.ModelAdmin):
    list_display = ("id", "twitter_id", "username", "display_name", "location")


@admin.register(ScrapingRequest)
class ScrapingRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "status",
        "include_replies",
        "show_username_url",
        "show_tweet_url",
        "since",
        "until",
        "started",
        "finished",
        "tweets_saved",
    )
    list_filter = (
        "status",
        "include_replies",
        UsernameFilter,
        TwitterIdFilter,
        "created",
    )
    actions = [
        "start_scraping",
        "export_scraping_results",
        "create_conversation_scraping_requests",
    ]

    def show_username_url(self, obj):
        return format_html(f"<a href='{obj.get_twitter_url()}'>{obj.username}</a>")

    show_username_url.short_description = "Username"

    def show_tweet_url(self, obj):
        try:
            tweet = Tweet.objects.get(twitter_id=obj.twitter_id)
            return format_html(
                f"<a href='{tweet.get_twitter_url()}'>{tweet.twitter_id}</a>"
            )
        except:
            return obj.twitter_id

    show_tweet_url.short_description = "Tweet Id"

    def tweets_saved(self, obj):
        try:
            # To Do: Include tweets from derived requests (might require a new fk field)
            return Tweet.objects.filter(scraping_request=obj).count()
        except Exception as e:
            return None

    tweets_saved.short_description = "Tweets saved"

    def start_scraping(self, request, queryset):
        for obj in queryset:
            obj.create_scraping_task()

    start_scraping.short_description = "Start scraping tasks"

    def create_conversation_scraping_requests(self, request, queryset):
        for obj in queryset:
            obj.create_conversation_scraping_requests()

    create_conversation_scraping_requests.short_description = (
        "Create conversation scraping requests"
    )

    def export_scraping_results(self, request, queryset):
        scraping_ids = list(queryset.values_list("id", flat=True))
        filename = f"scraping_requests id={scraping_ids}"
        tweets = Tweet.objects.filter(scraping_request__in=queryset)
        export(tweets, filename)

    export_scraping_results.short_description = "Export scraping results"
