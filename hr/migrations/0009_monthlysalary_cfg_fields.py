from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0008_employeesalary_custom_config'),
    ]

    operations = [
        migrations.AddField(
            model_name='monthlysalary',
            name='cfg_housing_pct',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name='monthlysalary',
            name='cfg_medical_pct',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name='monthlysalary',
            name='cfg_transport_pct',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name='monthlysalary',
            name='cfg_fuel_pct',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name='monthlysalary',
            name='cfg_tax_pct',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name='monthlysalary',
            name='cfg_pf_pct',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name='monthlysalary',
            name='cfg_security_pct',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name='monthlysalary',
            name='cfg_van_child_pct',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name='monthlysalary',
            name='cfg_bonus_per_day',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='monthlysalary',
            name='cfg_bonus_pct',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
    ]
