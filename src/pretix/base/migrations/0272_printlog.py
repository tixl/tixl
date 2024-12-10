# Generated by Django 4.2.16 on 2024-09-19 10:41

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.OAUTH2_PROVIDER_APPLICATION_MODEL),
        ("pretixbase", "0271_itemcategory_cross_selling"),
    ]

    operations = [
        migrations.CreateModel(
            name="PrintLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False
                    ),
                ),
                ("datetime", models.DateTimeField(default=django.utils.timezone.now)),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("successful", models.BooleanField(default=True)),
                ("source", models.CharField(max_length=255)),
                ("type", models.CharField(max_length=255)),
                ("info", models.JSONField(default=dict)),
                (
                    "api_token",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="pretixbase.teamapitoken",
                    ),
                ),
                (
                    "device",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="print_logs",
                        to="pretixbase.device",
                    ),
                ),
                (
                    "oauth_application",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to=settings.OAUTH2_PROVIDER_APPLICATION_MODEL,
                    ),
                ),
                (
                    "position",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="print_logs",
                        to="pretixbase.orderposition",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="print_logs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("-datetime",),
            },
        ),
    ]
