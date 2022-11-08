# Generated by Django 3.2.11 on 2022-08-23 17:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bc_connect', '0011_auto_20220611_0756'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenant',
            name='auth_type',
            field=models.CharField(choices=[('Oauth', 'Oauth'), ('Key', 'Key')], default='', max_length=250),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='tenant',
            name='scope',
            field=models.CharField(default='', max_length=250),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='tenant',
            name='token',
            field=models.CharField(default=' ', max_length=500),
            preserve_default=False,
        ),
    ]