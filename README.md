# twitter-scrapping

# Setup geral

## Iniciando o Django
```
python manage.py runserver
```

# Setup manual

## Iniciando Docker e Rabbit MQ
```
sudo service docker start
docker run -d -p 5672:5672 rabbitmq
```

## Iniciando um Celery Worker local
```
celery -A twitter_scrapping worker -l INFO -f celery3.log
```

## Iniciando um Celery Flower
```
celery flower
```

# Setup com Docker

Primeiro você precisa ter o [Docker](https://docs.docker.com/engine/) instalado e rodando.

Depois é só rodar:

```
docker compose build
docker compose up
```

Acesse o admin em `http://localhost:8000/admin/`

## Abrir shell de um container
```
docker exec -it django /bin/bash
```

# Exemplos de uso

Os exemplos abaixo deve ser rodados no shell do Django
```
python manage.py shell
```

## Iniciando uma task de scrapping pelo admin

- Acesse `http://127.0.0.1:8000/admin/tweets/scrappingrequest/`
- Clique em "ADD SCRAPPING REQUEST"
- Preencha os campos "Username", "Since" e "Until"
    - Se quiser realizar um scrapping recursivo, marque a opção "Recurse"
- Clique em "SAVE"
- Na tela de listagem, selecione a request que acabou de criar
- Clique em "Action", selecione "Start scrapping tasks", e então clique em Go

## Iniciando uma task de scrapping manualmente

Precisamos criar um objeto `ScrappingRequest` com os parâmetros do scrapping, e então chamar o método para iniciar a task
```
from tweets.models import ScrappingRequest
username = 'andreawerner_'
since = '2022-09-01'
until = '2022-09-02'
req = ScrappingRequest.objects.create(
    username=username, since=since, until=until
)
req.create_scrapping_task()
```

Para raspar todas as respostas e conversas derivadas dos tweets, podemos usar `recurse=True`.
Porém este parâmetro pode aumentar significativamente o tempo de raspagem.
```
from tweets.models import ScrappingRequest
username = 'andreawerner_'
since = '2022-09-01'
until = '2022-09-02'
req = ScrappingRequest.objects.create(
    username=username, since=since, until=until, recurse=True
)
req.create_scrapping_task()
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