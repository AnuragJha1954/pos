# Generated by Django 4.2.5 on 2024-09-24 03:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('qr', '0002_order_address'),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('phone_number', models.CharField(max_length=15)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='customers', to='qr.order')),
            ],
        ),
    ]
