# Generated by Django 3.0.8 on 2020-10-01 11:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminpanel', '0010_auto_20200930_1439'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='DiscountPercentage',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
    ]
