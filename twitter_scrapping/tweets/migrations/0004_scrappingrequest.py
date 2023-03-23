# Generated by Django 4.1.7 on 2023-03-22 00:07

from django.db import migrations, models
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ("tweets", "0003_tweet_conversation_tweet_tweet_in_reply_to_tweet"),
    ]

    operations = [
        migrations.CreateModel(
            name="ScrappingRequest",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created",
                    django_extensions.db.fields.CreationDateTimeField(
                        auto_now_add=True, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    django_extensions.db.fields.ModificationDateTimeField(
                        auto_now=True, verbose_name="modified"
                    ),
                ),
                ("username", models.CharField(blank=True, max_length=50, null=True)),
                ("since", models.DateTimeField(blank=True, null=True)),
                ("until", models.DateTimeField(blank=True, null=True)),
                ("started", models.DateTimeField(blank=True, null=True)),
                ("finished", models.DateTimeField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("created", "Created"),
                            ("started", "Started"),
                            ("finished", "Finished"),
                            ("interrupted", "Interrupted"),
                        ],
                        default="created",
                        max_length=12,
                    ),
                ),
            ],
            options={
                "get_latest_by": "modified",
                "abstract": False,
            },
        ),
    ]
