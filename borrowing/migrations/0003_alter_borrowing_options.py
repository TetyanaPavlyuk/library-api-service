# Generated by Django 5.1.1 on 2024-10-01 10:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("borrowing", "0002_alter_borrowing_actual_return_date"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="borrowing",
            options={"ordering": ["-actual_return_date", "-borrow_date"]},
        ),
    ]