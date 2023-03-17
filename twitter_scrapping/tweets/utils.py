from django.conf import settings
from django.utils import timezone
import pandas as pd


def export_csv(queryset):
    df = pd.DataFrame(tweet.as_csv_row() for tweet in queryset)
    filepath = f'{settings.DEFAULT_EXPORT_PATH}{queryset.model.__name__.lower()}-{timezone.now()}.csv'
    df.to_csv(filepath)

