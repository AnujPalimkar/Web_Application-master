# Generated by Django 3.0.8 on 2020-12-10 15:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminpanel', '0041_installmentdue_isinstalmentpaid'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='Stripe_Payment_Id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
