# Migration 0017: Add config_mode and cfg_mode fields safely

from django.db import migrations, models


def forwards(apps, schema_editor):
    """Safely add columns only if they don't already exist."""
    conn = schema_editor.connection
    with conn.cursor() as cursor:
        tables = conn.introspection.table_names(cursor)

        def add_col(table, col, field_def):
            if table not in tables:
                return
            columns = [c['name'] for c in conn.introspection.get_columns(cursor, table)]
            if col not in columns:
                sql = f'ALTER TABLE "{table}" ADD COLUMN "{col}" {field_def}'
                cursor.execute(sql)

        add_col('hr_salaryconfig', 'config_mode', "varchar(10) DEFAULT 'percentage' NOT NULL")
        add_col('hr_monthlysalary', 'cfg_mode', "varchar(10) DEFAULT 'percentage' NOT NULL")
        add_col('hr_monthlysalary', 'cfg_kid_fee_pct', 'numeric(5,2) DEFAULT 0 NOT NULL')
        add_col('hr_monthlysalary', 'kid_fee', 'numeric(12,2) DEFAULT 0 NOT NULL')


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0016_remove_employeesalary_custom_kid_fee_pct_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
