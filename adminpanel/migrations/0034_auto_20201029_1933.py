# Generated by Django 3.0.8 on 2020-10-29 19:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminpanel', '0033_auto_20201029_1918'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderdiscount',
            name='DiscountType',
        ),
        migrations.AddField(
            model_name='orderdiscount',
            name='DiscountType_Id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
