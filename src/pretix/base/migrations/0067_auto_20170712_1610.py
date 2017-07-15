# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-12 16:10
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pretixbase', '0066_auto_20170708_2102'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='subevent',
            options={'ordering': ('date_from', 'name'), 'verbose_name': 'Date in event series', 'verbose_name_plural': 'Dates in event series'},
        ),
        migrations.AddField(
            model_name='itemaddon',
            name='price_included',
            field=models.BooleanField(default=False, help_text='If selected, adding add-ons to this ticket is free, even if the add-ons would normally cost money individually.', verbose_name='Add-Ons are included in the price'),
        ),
        migrations.AlterField(
            model_name='cartposition',
            name='subevent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='pretixbase.SubEvent', verbose_name='Date'),
        ),
        migrations.AlterField(
            model_name='event',
            name='has_subevents',
            field=models.BooleanField(default=False, verbose_name='Event series'),
        ),
        migrations.AlterField(
            model_name='orderposition',
            name='subevent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='pretixbase.SubEvent', verbose_name='Date'),
        ),
        migrations.AlterField(
            model_name='quota',
            name='subevent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='quotas', to='pretixbase.SubEvent', verbose_name='Date'),
        ),
        migrations.AlterField(
            model_name='subevent',
            name='active',
            field=models.BooleanField(default=False, help_text='Only with this checkbox enabled, this date is visible in the frontend to users.', verbose_name='Active'),
        ),
        migrations.AlterField(
            model_name='subevent',
            name='presale_end',
            field=models.DateTimeField(blank=True, help_text='Optional. No products will be sold after this date.', null=True, verbose_name='End of presale'),
        ),
        migrations.AlterField(
            model_name='subevent',
            name='presale_start',
            field=models.DateTimeField(blank=True, help_text='Optional. No products will be sold before this date.', null=True, verbose_name='Start of presale'),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='subevent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='pretixbase.SubEvent', verbose_name='Date'),
        ),
        migrations.AlterField(
            model_name='waitinglistentry',
            name='subevent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='pretixbase.SubEvent', verbose_name='Date'),
        ),
    ]
