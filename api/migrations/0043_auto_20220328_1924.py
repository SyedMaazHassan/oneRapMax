# Generated by Django 3.2.8 on 2022-03-28 14:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0042_alter_goalcounter_user'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='badge',
            options={'ordering': ('requirement',)},
        ),
        migrations.AlterModelOptions(
            name='goalcounter',
            options={'ordering': ('-records_broke',)},
        ),
        migrations.AlterField(
            model_name='goalcounter',
            name='records_broke',
            field=models.IntegerField(default=0),
        ),
    ]