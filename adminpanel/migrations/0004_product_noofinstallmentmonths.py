# Generated by Django 3.0.8 on 2020-09-08 14:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminpanel', '0003_auto_20200908_0956'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='NoOfInstallmentMonths',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
