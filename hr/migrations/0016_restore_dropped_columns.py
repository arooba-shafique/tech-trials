from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0015_rename_custom_fuel_pct_employeesalary_custom_kid_fee_pct_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='employeesalary',
            name='kid_fee',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='employeesalary',
            name='custom_kid_fee_pct',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name='employeesalary',
            name='custom_van_child_pct',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name='monthlysalary',
            name='cfg_kid_fee_pct',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name='monthlysalary',
            name='cfg_van_child_pct',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name='monthlysalary',
            name='kid_fee',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='monthlysalary',
            name='van_child_deduction',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='salaryconfig',
            name='kid_fee_pct',
            field=models.DecimalField(decimal_places=2, default=0, help_text="Kid's fee allowance % of basic", max_digits=5),
        ),
        migrations.AddField(
            model_name='salaryconfig',
            name='van_child_pct',
            field=models.DecimalField(decimal_places=2, default=0, help_text="Van/Child deduction % of basic", max_digits=5),
        ),
    ]
