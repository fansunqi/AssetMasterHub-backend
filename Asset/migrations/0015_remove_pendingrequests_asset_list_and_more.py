# Generated by Django 4.1.3 on 2023-04-21 03:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Asset', '0014_alter_asset_property'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pendingrequests',
            name='asset_list',
        ),
        migrations.AddField(
            model_name='pendingrequests',
            name='asset',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='Asset.asset'),
            preserve_default=False,
        ),
    ]
