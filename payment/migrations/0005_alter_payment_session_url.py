# Generated by Django 5.1.1 on 2024-10-17 06:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payment", "0004_alter_payment_session_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="payment",
            name="session_url",
            field=models.URLField(blank=True, max_length=511),
        ),
    ]
