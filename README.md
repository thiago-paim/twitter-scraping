# twitter-scrapping

## Setup geral

### Iniciando o Django
```
python manage.py runserver
```

## Setup para rodar raspagem de tweets

### Iniciando Docker e Rabbit MQ
```
sudo service docker start
docker run -d -p 5672:5672 rabbitmq
```

### Iniciando um Celery Worker local
```
celery -A twitter_scrapping worker -l INFO -f celery.log
```

### Iniciando um Celery Flower
```
celery flower
```

### Iniciando uma task de scrapping
Abra o shell do Django
```
python manage.py shell
```

Importe a task, defina os parâmetros e envie ela para o worker
```
from tweets.tasks import scrape_tweets
username = 'ErikakHilton'
since = '2023-03-01'
until = '2023-03-15'
scrape_tweets.delay(username, since, until)
```