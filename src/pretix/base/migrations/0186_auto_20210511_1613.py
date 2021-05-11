# Generated by Django 3.2.2 on 2021-05-11 16:13

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pretixbase', '0185_memberships'),
    ]

    operations = [
        migrations.AddField(
            model_name='checkin',
            name='created',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='checkin',
            name='error_explanation',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='checkin',
            name='error_reason',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='checkin',
            name='raw_barcode',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='checkin',
            name='raw_item',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='all_checkins', to='pretixbase.item'),
        ),
        migrations.AddField(
            model_name='checkin',
            name='raw_subevent',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='all_checkins', to='pretixbase.subevent'),
        ),
        migrations.AddField(
            model_name='checkin',
            name='raw_variation',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='all_checkins', to='pretixbase.itemvariation'),
        ),
        migrations.AddField(
            model_name='checkin',
            name='successful',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='checkin',
            name='position',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='all_checkins', to='pretixbase.orderposition'),
        ),
    ]
