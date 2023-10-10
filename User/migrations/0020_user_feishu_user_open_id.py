# Generated by Django 4.1.3 on 2023-05-14 05:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("User", "0019_user_mobile"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="feishu",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="user",
            name="open_id",
            field=models.CharField(max_length=128, null=True),
        ),
    ]
