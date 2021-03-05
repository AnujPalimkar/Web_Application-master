# Generated by Django 3.0.8 on 2020-09-07 09:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('adminpanel', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='Phone_No',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='payment',
            name='Amount',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='payment',
            name='Is_Invoice_Sent',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='Price',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('InvoiceId', models.AutoField(primary_key=True, serialize=False)),
                ('InvoiceNumber', models.CharField(blank=True, max_length=50, null=True)),
                ('Filename', models.CharField(blank=True, max_length=2000, null=True)),
                ('CreatedBy', models.CharField(blank=True, max_length=200, null=True)),
                ('Content', models.FileField(blank=True, null=True, upload_to='')),
                ('Date', models.DateTimeField(auto_now_add=True, null=True)),
                ('Order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='adminpanel.Order')),
            ],
        ),
    ]