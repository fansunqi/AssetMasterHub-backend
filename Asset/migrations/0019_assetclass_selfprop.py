# Generated by Django 4.1.3 on 2023-04-22 13:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Asset', '0018_asset_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='assetclass',
            name='selfprop',
            field=models.TextField(null=True),
        ),
    ]
