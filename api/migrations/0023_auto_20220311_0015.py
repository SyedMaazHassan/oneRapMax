# Generated by Django 3.0.8 on 2022-03-10 19:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0022_auto_20220225_2027'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='systemuser',
            name='about',
        ),
        migrations.RemoveField(
            model_name='systemuser',
            name='display_name',
        ),
        migrations.RemoveField(
            model_name='systemuser',
            name='is_fee_paid',
        ),
        migrations.RemoveField(
            model_name='systemuser',
            name='is_trial_end',
        ),
        migrations.RemoveField(
            model_name='systemuser',
            name='is_trial_synced',
        ),
        migrations.RemoveField(
            model_name='systemuser',
            name='is_trial_taken',
        ),
        migrations.RemoveField(
            model_name='systemuser',
            name='stripe_cust_id',
        ),
        migrations.AddField(
            model_name='systemuser',
            name='gender',
            field=models.CharField(blank=True, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], max_length=15, null=True),
        ),
        migrations.AddField(
            model_name='systemuser',
            name='height',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='systemuser',
            name='is_profile_completed',
            field=models.BooleanField(default=False),
        ),
    ]
