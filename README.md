# twitter-scrapping

# Setup geral

## Iniciando o Django
```
python manage.py runserver
```

# Setup para rodar raspagem de tweets

## Iniciando Docker e Rabbit MQ
```
sudo service docker start
docker run -d -p 5672:5672 rabbitmq
```

## Iniciando um Celery Worker local
```
celery -A twitter_scrapping worker -l INFO -f celery.log
```

## Iniciando um Celery Flower
```
celery flower
```

# Setup com Docker

## Abrir shell de um container
```
docker exec -it django /bin/bash
```

# Exemplos de uso

Os exemplos abaixo deve ser rodados no shell do Django
```
python manage.py shell
```

## Iniciando uma task de scrapping
```
from tweets.tasks import scrape_tweets
username = 'ErikakHilton'
since = '2023-03-15'
until = '2023-03-16'
scrape_tweets.delay(username, since, until)
```

## Raspar um único tweet e validar os dados
```
from tweets.serializers import SnscrapeTwitterUserSerializer, SnscrapeTweetSerializer
from tweets.tasks import scrape_single_tweet

tweet_id = '1636295637187584000'
tweet = scrape_single_tweet.delay(tweet_id)
user_serializer = SnscrapeTwitterUserSerializer(data=tweet.user.__dict__)
if not user_serializer.is_valid():
    print(user_serializer.errors)

tweet_kwargs = tweet.__dict__
tweet_kwargs['user_twitter_id'] = tweet.user.id
tweet_serializer = SnscrapeTweetSerializer(data=tweet_kwargs)
if not tweet_serializer.is_valid():
    print(tweet_serializer.errors)
```

## Exportar para CSV os tweets de um usuario
```
from tweets.models import Tweet, TwitterUser
from tweets.utils import export_csv

user = TwitterUser.objects.last()
tweets = Tweet.objects.filter(user=user)
export_csv(tweets)
```