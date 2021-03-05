# Generated by Django 3.0.8 on 2020-10-12 16:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('adminpanel', '0017_auto_20201006_1547'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivityType',
            fields=[
                ('ActivityTypeId', models.AutoField(primary_key=True, serialize=False)),
                ('ActivityType', models.CharField(blank=True, max_length=50, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ActivityLog',
            fields=[
                ('ActivityLogId', models.AutoField(primary_key=True, serialize=False)),
                ('ActivityDescription', models.CharField(blank=True, max_length=2000, null=True)),
                ('CreatedBy', models.CharField(blank=True, max_length=50, null=True)),
                ('CreatedDate', models.DateField(auto_now_add=True, null=True)),
                ('ActivityType', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='adminpanel.ActivityType')),
            ],
        ),
    ]
