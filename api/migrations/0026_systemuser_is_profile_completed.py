# Generated by Django 3.0.8 on 2022-03-10 19:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0025_remove_systemuser_is_profile_completed'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemuser',
            name='is_profile_completed',
            field=models.BooleanField(default=True),
        ),
    ]
