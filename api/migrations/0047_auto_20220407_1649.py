# Generated by Django 3.2.8 on 2022-04-07 11:49

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0046_goal'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='goal',
            options={'ordering': ('-reps',)},
        ),
        migrations.RemoveField(
            model_name='entry',
            name='dates',
        ),
        migrations.RemoveField(
            model_name='entry',
            name='values',
        ),
        migrations.CreateModel(
            name='Value',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reps', models.IntegerField()),
                ('dumble_weight', models.FloatField()),
                ('one_rep_value', models.FloatField(blank=True, null=True)),
                ('date', models.DateField(default=datetime.date.today)),
                ('entry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.entry')),
            ],
        ),
    ]
