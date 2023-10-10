# Generated by Django 4.1.3 on 2023-03-24 12:51

from django.db import migrations, models
import django.db.models.deletion
import utils.model_date


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128)),
            ],
        ),
        migrations.CreateModel(
            name='Entity',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128)),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('password', models.CharField(max_length=32)),
                ('entity_super', models.IntegerField()),
                ('system_super', models.IntegerField()),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='User.department')),
                ('entity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='User.entity')),
            ],
        ),
        migrations.CreateModel(
            name='SessionPool',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sessionId', models.CharField(max_length=32)),
                ('expireAt', models.DateTimeField(default=utils.model_date.get_datetime)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='User.user')),
            ],
        ),
        migrations.AddField(
            model_name='department',
            name='entity',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='User.entity'),
        ),
        migrations.AddField(
            model_name='department',
            name='parent',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='User.department'),
        ),
    ]
