from django.conf import settings
from django.utils import timezone
import pandas as pd


def export_csv(queryset, filename=None):
    if not filename:
        filename = f'{queryset.model.__name__.lower()}s'
    time_signature = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
    filepath = f'{settings.DEFAULT_EXPORT_PATH}{time_signature} {filename}.csv'
    
    df = pd.DataFrame(tweet.export() for tweet in queryset)
    df.to_csv(filepath)

