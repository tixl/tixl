# Generated by Django 3.2.19 on 2023-08-09 11:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sendmail', '0004_rule_restrict_to_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='rule',
            name='checked_in_status',
            field=models.CharField(default='all', max_length=10, null=True),
        ),
    ]
