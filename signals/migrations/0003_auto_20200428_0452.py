# Generated by Django 3.0.5 on 2020-04-28 04:52

from django.db import migrations, models
import signals.models


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0002_auto_20200428_0451'),
    ]

    operations = [
        migrations.AlterField(
            model_name='signal',
            name='operation_type',
            field=models.CharField(choices=[(signals.models.OperationType['SELL'], 'SELL'), (signals.models.OperationType['BUY'], 'BUY')], max_length=50),
        ),
    ]
