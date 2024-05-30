# Generated by Django 5.0.6 on 2024-05-30 21:43

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_remove_dateslot_end_time_remove_dateslot_start_time_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Appointment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('duration', models.DurationField()),
                ('center', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.center')),
                ('time_slot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.dateslot')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
