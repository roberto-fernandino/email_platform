# Generated by Django 4.2.5 on 2023-09-21 16:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mail', '0003_remove_emailtracked_sent_at_emailtracked_sent_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailtracked',
            name='sent_try',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
