# Generated by Django 4.1.3 on 2023-05-13 09:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("User", "0018_alter_entity_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="mobile",
            field=models.CharField(max_length=32, null=True, unique=True),
        ),
    ]
