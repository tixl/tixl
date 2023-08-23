# Generated by Django 4.2.4 on 2023-08-23 15:26

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("pretixbase", "0244_mediumkeyset"),
    ]

    operations = [
        migrations.AddField(
            model_name="discount",
            name="benefit_limit_products",
            field=models.ManyToManyField(
                related_name="benefit_discounts", to="pretixbase.item"
            ),
        ),
        migrations.AddField(
            model_name="discount",
            name="benefit_same_products",
            field=models.BooleanField(default=True),
        ),
    ]
