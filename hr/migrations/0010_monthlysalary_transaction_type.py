from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0009_monthlysalary_cfg_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='monthlysalary',
            name='transaction_type',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('bank_islami', 'Bank Islami'),
                    ('ubl', 'UBL'),
                    ('cash', 'Cash in Hand'),
                    ('personal', 'Personal Account'),
                ],
                default='bank_islami',
            ),
        ),
    ]
