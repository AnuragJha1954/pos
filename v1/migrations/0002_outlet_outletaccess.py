# Generated by Django 4.2.5 on 2024-10-15 14:04

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('v1', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Outlet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('logo', models.ImageField(upload_to='logos/')),
                ('gst_number', models.CharField(max_length=50)),
                ('name', models.CharField(max_length=255)),
                ('account_details', models.TextField()),
                ('outlet_name', models.CharField(max_length=255)),
                ('address', models.TextField()),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='outlets', to='v1.company')),
            ],
        ),
        migrations.CreateModel(
            name='OutletAccess',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('permissions', models.JSONField()),
                ('outlet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='v1.outlet')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
