# Generated by Django 5.1.3 on 2024-11-12 07:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_alter_profile_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='cover',
            field=models.ImageField(blank=True, null=True, upload_to='accounts/profiles'),
        ),
    ]
