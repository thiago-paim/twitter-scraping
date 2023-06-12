from celery import shared_task
from celery.utils.log import get_task_logger
from copy import deepcopy
from datetime import datetime
from django.utils import timezone
from django.conf import settings
from rest_framework.serializers import ValidationError
from snscrape.modules.twitter import (
    TwitterTweetScraperMode,
    TwitterTweetScraper,
    TwitterSearchScraper,
    TwitterProfileScraper,
    User as SNUser,
    Tweet as SNTweet,
    Tombstone,
)
import traceback

from .serializers import SnscrapeTweetSerializer
from .utils import CustomTwitterProfileScraper, tweet_to_json, CustomTwitterTweetScraper

logger = get_task_logger(__name__)


@shared_task
def scrape_tweet(tweet_id, mode=TwitterTweetScraperMode.SINGLE):
    mode = mode
    tweet_scrapper = TwitterTweetScraper(tweet_id, mode=mode).get_items()
    tweet = next(tweet_scrapper)
    return tweet


def record_tweet(raw_tweet, req_id=None):
    # Consider moving this to SnscrapeTweetSerializer
    tweet = deepcopy(raw_tweet)
    tweet.raw_tweet_object = tweet_to_json(tweet)

    if tweet.quotedTweet:
        if type(tweet.quotedTweet) == SNTweet:
            qt_tweet, created = record_tweet(tweet.quotedTweet)
            tweet.quoted_id = qt_tweet.twitter_id
            tweet.quoted_tweet = qt_tweet.id

        if type(tweet.quotedTweet) == Tombstone:
            tweet.quoted_id = tweet.quotedTweet.id

    if tweet.retweetedTweet:
        if type(tweet.retweetedTweet) == SNTweet:
            rt_tweet, created = record_tweet(tweet.retweetedTweet)
            tweet.retweeted_id = rt_tweet.twitter_id
            tweet.retweeted_tweet = rt_tweet.id

        if type(tweet.retweetedTweet) == Tombstone:
            tweet.retweeted_id = tweet.retweetedTweet.id

    tweet.scraping_request = req_id
    tweet_serializer = SnscrapeTweetSerializer(data=tweet)
    if tweet_serializer.is_valid():
        tweet, created = tweet_serializer.save()
        # To Do: Retornar também outros tweets que tenham sido criados (rt ou qt)
        return tweet, created
    else:
        raise ValidationError(tweet_serializer.errors)


@shared_task
def scrape_user_tweets(req_id):
    try:
        from .models import ScrapingRequest

        started_at = timezone.now()
        req = ScrapingRequest.objects.get(id=req_id)
        req.start()

        username = req.username
        logger.info(
            f"req_id={req_id}: Iniciando scrape_user_tweets com username={username}, since={req.since}, until={req.until})"
        )

        tweets = []
        created_tweets = []
        updated_tweets = []
        MIN_TWEETS = (
            5  # É comum que usuários tenham 1 ou 2 tweets fixados no topo do perfil
        )
        tweet_scrapper = CustomTwitterProfileScraper(username).get_items()

        # Loop manual necessário para que erros em tweets pontuais não travem o generator
        while True:
            try:
                tweet = next(tweet_scrapper)
                if type(tweet) != SNTweet:
                    continue
                tweets.append(tweet)
                if tweet.date < req.since and len(tweets) > MIN_TWEETS:
                    logger.info(
                        f"req_id={req_id}: Limite de raspagem atingido em {tweet.date}"
                    )
                    break

                try:
                    t, created = record_tweet(tweet, req_id)
                    if created:
                        created_tweets.append(t)
                    else:
                        updated_tweets.append(t)
                except ValidationError as e:
                    logger.error(
                        f"req_id={req_id}: Erro de validação ao salvar tweet {tweet}: {e}"
                    )
                except Exception as e:
                    tb = traceback.format_exc()
                    logger.error(
                        f"req_id={req_id}: Exceção ao salvar tweet {tweet}: {e}:\n{tb}"
                    )

            except StopIteration:
                break
            except Exception as e:
                tb = traceback.format_exc()
                logger.error(
                    f"req_id={req_id}: Exceção no tweet {tweet.id}: {e}:\n{tb}"
                )
                raise

        logger.info(f"req_id={req_id}: Encontrados {len(tweets)} tweets")

        req.log(f"tweets={[t.id for t in tweets]}")
        req.log(f"created_tweets={[t.twitter_id for t in created_tweets]}")
        req.log(f"updated_tweets={[t.twitter_id for t in updated_tweets]}")
        req.finish()
        req.create_conversation_scraping_requests()

        finished_at = timezone.now()
        logger.info(
            f"req_id={req_id}: Finalizando scrape_user_tweets(username={username}, since={req.since}, until={req.until}):"
            + f"{len(created_tweets)} tweets criados, {len(updated_tweets)} tweets atualizados"
        )
        logger.info(f"req_id={req_id}: Tempo total={finished_at - started_at}")

    except Exception as e:
        tb = traceback.format_exc()
        logger.error(
            f"req_id={req_id}: Exceção geral ao executar scrape_user_tweets: {e}:\n{tb}"
        )
        req.interrupt()

    start_next_scraping_request.delay()
    return {
        "created_tweets": len(created_tweets),
        "updated_tweets": len(updated_tweets),
    }


@shared_task
def scrape_tweet_replies(tweet_id, req_id):
    try:
        from .models import ScrapingRequest

        started_at = timezone.now()
        req = ScrapingRequest.objects.get(id=req_id)
        req.start()

        username = req.username
        logger.info(
            f"req_id={req_id}: Iniciando scrape_tweet_replies com tweet_id={tweet_id}, username={username})"
        )
        tweets = []
        created_tweets = []
        updated_tweets = []

        tweet_scraper = CustomTwitterTweetScraper(
            tweet_id, mode=TwitterTweetScraperMode.SCROLL
        ).get_items()

        # Loop manual necessário para que erros em tweets pontuais não travem o generator
        while True:
            try:
                tweet = next(tweet_scraper)
                if type(tweet) != SNTweet:
                    continue
                tweets.append(tweet)
                try:
                    t, created = record_tweet(tweet, req_id)
                    if created:
                        created_tweets.append(t)
                    else:
                        updated_tweets.append(t)
                except ValidationError as e:
                    logger.error(
                        f"req_id={req_id}: Erro de validação ao salvar tweet {tweet}: {e}"
                    )
                except Exception as e:
                    tb = traceback.format_exc()
                    logger.error(
                        f"req_id={req_id}: Exceção ao salvar tweet {tweet}: {e}:\n{tb}"
                    )
            except StopIteration:
                break
            except Exception as e:
                tb = traceback.format_exc()
                logger.error(
                    f"req_id={req_id}: Exceção no tweet {tweet.id}: {e}:\n{tb}"
                )
                raise
        logger.info(f"req_id={req_id}: Encontrados {len(tweets)} tweets")

        req.log(f"tweets={[t.id for t in tweets]}")
        req.log(f"created_tweets={[t.twitter_id for t in created_tweets]}")
        req.log(f"updated_tweets={[t.twitter_id for t in updated_tweets]}")
        req.finish()

        finished_at = timezone.now()
        logger.info(
            f"req_id={req_id}: Finalizando scrape_tweet_replies(tweet_id={tweet_id}, username={username}):"
            + f"{len(created_tweets)} tweets criados, {len(updated_tweets)} tweets atualizados"
        )
        logger.info(f"req_id={req_id}: Tempo total={finished_at - started_at}")

    except Exception as e:
        tb = traceback.format_exc()
        logger.error(
            f"req_id={req_id}: Exceção geral ao executar scrape_tweet_replies: {e}:\n{tb}"
        )
        req.interrupt()

    start_next_scraping_request.delay()
    return {
        "created_tweets": len(created_tweets),
        "updated_tweets": len(updated_tweets),
    }


@shared_task
def scrape_last_tweet_from_user(username):
    tweet = next(CustomTwitterProfileScraper(username).get_items())
    return tweet


@shared_task
def scrape_tweets_and_replies(req_id):
    """DEPRECATED: TwitterSearchScraper doesn't work anymore"""
    try:
        from .models import ScrapingRequest

        started_at = timezone.now()
        req = ScrapingRequest.objects.get(id=req_id)
        req.start()

        username = req.username
        since = req.since.strftime("%Y-%m-%dT%H:%M:%SZ")
        until = req.until.strftime("%Y-%m-%dT%H:%M:%SZ")
        logger.info(
            f"Iniciando scrape_tweets_and_replies(username={username}, since={since}, until={until}, recurse={req.recurse})"
        )

        started_scraping_at = timezone.now()
        query = f"from:{username} since:{since} until:{until}"
        user_scraping_results = TwitterSearchScraper(query).get_items()
        tweet_ids = []
        logger.info(f'Contando tweets do usuário "{username}"')
        for tweet in user_scraping_results:
            tweet_ids.append(tweet.id)
        logger.info(f"Encontrados {len(tweet_ids)} tweets")

        logger.info(f'Raspando tweets do usuário "{username}" e suas respostas')
        tweets_and_replies = []
        if req.recurse:
            mode = TwitterTweetScraperMode.RECURSE
        else:
            mode = TwitterTweetScraperMode.SCROLL
        for tweet_id in tweet_ids:
            tweet_scrapper = TwitterTweetScraper(tweet_id, mode=mode).get_items()
            try:
                # Loop manual necessário para que erros em tweets pontuais não travem o generator
                while True:
                    tweet = next(tweet_scrapper)
                    tweets_and_replies.append(tweet)
            except StopIteration:
                continue
            except Exception as e:
                tb = traceback.format_exc()
                logger.error(f"Exceção ao raspar tweet {tweet_id}: {e}:\n{tb}")
        logger.info(f"Encontrados {len(tweets_and_replies)} tweets")

        started_saving_at = timezone.now()
        logger.info(f"Iniciando gravacao de {len(tweets_and_replies)} tweets")
        created_tweets = []
        updated_tweets = []
        for tweet_data in tweets_and_replies:
            try:
                t, created = save_scrapped_tweet(tweet_data, req_id)
                if created:
                    created_tweets.append(t)
                else:
                    updated_tweets.append(t)

            except ValidationError as e:
                logger.error(f"Erro de validação ao salvar tweet {tweet_data}: {e}")

            except Exception as e:
                tb = traceback.format_exc()
                logger.error(f"Exceção ao salvar tweet {tweet_data}: {e}:\n{tb}")

        req.finish()
        finished_at = timezone.now()
        logger.info(
            f"Finalizando scrape_tweets_and_replies(username={username}, since={since}, until={until}, recurse={req.recurse}):"
            + f"{len(created_tweets)} tweets criados, {len(updated_tweets)} tweets atualizados"
        )
        logger.info(
            f"Tempo total={finished_at - started_at}; Tempo de scraping={started_saving_at - started_scraping_at}; Tempo de gravação={finished_at - started_saving_at}"
        )
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(
            f"Exceção ao executar scrape_tweets_and_replies(req_id={req_id}): {e}:\n{tb}"
        )
        req.interrupt()


def save_scrapped_tweet(tweet_data, req_id):
    """DEPRECATED: Deprecated along with scrape_tweets_and_replies"""
    tweet_data.scraping_request = req_id
    tweet_serializer = SnscrapeTweetSerializer(data=tweet_data)
    if tweet_serializer.is_valid():
        tweet, created = tweet_serializer.save()
        return tweet, created
    else:
        raise ValidationError(tweet_serializer.errors)


@shared_task
def create_scraping_requests(usernames, periods, include_replies=False):
    from .models import ScrapingRequest

    created_requests = []
    for period in periods:
        since = timezone.make_aware(datetime.strptime(period["since"], "%Y-%m-%d"))
        until = timezone.make_aware(datetime.strptime(period["until"], "%Y-%m-%d"))

        for username in usernames:
            if not ScrapingRequest.objects.filter(
                username=username,
                since=since,
                until=until,
                include_replies=include_replies,
            ).exists():
                req = ScrapingRequest.objects.create(
                    username=username, since=since, until=until
                )
                req.save()
                created_requests.append(req)
                logger.info(
                    f"Criando ScrapingRequest(username={username}, since={period['since']}, until={period['until']}, include_replies={include_replies})"
                )

    logger.info(f"Criados {len(created_requests)} ScrapingRequest's")
    return created_requests


@shared_task
def start_next_scraping_request():
    from .models import ScrapingRequest

    running_requests_count = ScrapingRequest.objects.filter(status="started").count()
    if running_requests_count >= settings.MAX_SCRAPINGS:
        return

    requests = list(ScrapingRequest.objects.filter(status="created"))
    started_reqs = []
    while requests and running_requests_count < settings.MAX_SCRAPINGS:
        req = requests.pop(0)
        req.create_scraping_task()
        logger.info(
            f"Iniciando ScrapingRequest(username={req.username}, since={req.since}, until={req.until})"
        )
        running_requests_count += 1
        started_reqs.append(req.id)
    return started_reqs
