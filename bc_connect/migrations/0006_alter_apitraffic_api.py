# Generated by Django 3.2.11 on 2022-04-13 22:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bc_connect', '0005_auto_20220413_2213'),
    ]

    operations = [
        migrations.AlterField(
            model_name='apitraffic',
            name='api',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]
