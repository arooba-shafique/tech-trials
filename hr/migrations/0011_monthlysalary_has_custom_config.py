from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0010_monthlysalary_transaction_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='monthlysalary',
            name='has_custom_config',
            field=models.BooleanField(
                default=False,
                help_text='True if per-month overrides were saved via salary config',
            ),
        ),
    ]
