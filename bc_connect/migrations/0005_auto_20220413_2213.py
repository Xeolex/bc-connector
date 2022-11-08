# Generated by Django 3.2.11 on 2022-04-13 22:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bc_connect', '0004_apitraffic_view'),
    ]

    operations = [
        migrations.AlterField(
            model_name='apitraffic',
            name='body',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='apitraffic',
            name='created',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AlterField(
            model_name='apitraffic',
            name='method',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='apitraffic',
            name='param',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='apitraffic',
            name='path',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='apitraffic',
            name='response',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='apitraffic',
            name='updated',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AlterField(
            model_name='apitraffic',
            name='view',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]