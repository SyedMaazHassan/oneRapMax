# Generated by Django 3.0.8 on 2022-01-28 09:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_systemuser_stripe_cust_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='systemuser',
            name='stripe_cust_id',
        ),
    ]
