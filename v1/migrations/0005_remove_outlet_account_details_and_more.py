# Generated by Django 4.2.5 on 2024-11-11 06:54

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('v1', '0004_employee'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='outlet',
            name='account_details',
        ),
        migrations.RemoveField(
            model_name='outlet',
            name='outlet_name',
        ),
        migrations.RemoveField(
            model_name='outletaccess',
            name='user',
        ),
        migrations.AddField(
            model_name='outlet',
            name='bank_account_number',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='outlet',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='outlet',
            name='ifsc_code',
            field=models.CharField(blank=True, max_length=11, null=True),
        ),
        migrations.AddField(
            model_name='outlet',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='outlet',
            name='opening_hours',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='outlet',
            name='phone_number',
            field=models.CharField(blank=True, max_length=15, null=True),
        ),
        migrations.AddField(
            model_name='outlet',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='outletaccess',
            name='employee',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='v1.employee'),
            preserve_default=False,
        ),
    ]
