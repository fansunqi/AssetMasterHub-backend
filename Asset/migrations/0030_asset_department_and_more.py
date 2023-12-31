# Generated by Django 4.1.3 on 2023-05-19 03:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('User', '0023_log_is_succ'),
        ('Asset', '0029_pendingrequests_asset_pendi_message_6f3bd7_idx'),
    ]

    operations = [
        migrations.AddField(
            model_name='asset',
            name='department',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='User.department'),
        ),
        migrations.AddIndex(
            model_name='asset',
            index=models.Index(fields=['department'], name='Asset_asset_departm_52e787_idx'),
        ),
    ]
