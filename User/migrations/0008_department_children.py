# Generated by Django 4.1.3 on 2023-04-06 08:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("User", "0007_user_function_string"),
    ]

    operations = [
        migrations.AddField(
            model_name="department",
            name="children",
            field=models.CharField(max_length=256, null=True),
        ),
    ]
