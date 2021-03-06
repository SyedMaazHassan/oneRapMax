# Generated by Django 3.2.8 on 2022-03-17 18:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0037_alter_group_icon'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='group',
            options={'ordering': ('-created_at',), 'verbose_name': 'Group', 'verbose_name_plural': 'Groups'},
        ),
        migrations.AlterField(
            model_name='systemuser',
            name='is_profile_completed',
            field=models.BooleanField(default=False),
        ),
    ]
