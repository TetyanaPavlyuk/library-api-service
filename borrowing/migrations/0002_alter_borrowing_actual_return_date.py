# Generated by Django 5.1.1 on 2024-09-30 16:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("borrowing", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="borrowing",
            name="actual_return_date",
            field=models.DateField(blank=True, null=True),
        ),
    ]
