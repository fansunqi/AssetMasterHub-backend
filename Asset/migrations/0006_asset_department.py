# Generated by Django 4.1.3 on 2023-04-18 00:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('User', '0012_alter_user_entity'),
        ('Asset', '0005_asset_property'),
    ]

    operations = [
        migrations.AddField(
            model_name='asset',
            name='department',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='User.department'),
        ),
    ]
