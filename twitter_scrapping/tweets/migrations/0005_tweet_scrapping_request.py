# Generated by Django 4.1.7 on 2023-03-24 20:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("tweets", "0004_scrappingrequest"),
    ]

    operations = [
        migrations.AddField(
            model_name="tweet",
            name="scrapping_request",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="tweets",
                to="tweets.scrappingrequest",
            ),
        ),
    ]