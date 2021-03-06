# Generated by Django 3.2.8 on 2022-03-28 19:12

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0045_auto_20220328_1931'),
    ]

    operations = [
        migrations.CreateModel(
            name='Goal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reps', models.IntegerField()),
                ('is_acheived', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('exercise', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.exercise')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.systemuser')),
            ],
        ),
    ]
