# Generated by Django 4.1.3 on 2023-05-16 13:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Asset', '0026_assetclass_loss_style'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assetclass',
            name='loss_style',
            field=models.IntegerField(default=1, null=True),
        ),
    ]