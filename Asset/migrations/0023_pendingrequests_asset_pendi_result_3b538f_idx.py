# Generated by Django 4.1.3 on 2023-05-11 08:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Asset", "0022_asset_label_visible"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="pendingrequests",
            index=models.Index(fields=["result"], name="Asset_pendi_result_3b538f_idx"),
        ),
    ]
