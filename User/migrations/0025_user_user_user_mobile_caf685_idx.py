# Generated by Django 4.1.3 on 2023-05-24 14:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("User", "0024_app_image"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="user",
            index=models.Index(fields=["mobile"], name="User_user_mobile_caf685_idx"),
        ),
    ]
