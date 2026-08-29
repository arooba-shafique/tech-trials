# Migration 0018: Safety net — ensure config_mode/cfg_mode columns exist on Vercel DB.
# Uses PostgreSQL IF NOT EXISTS so it's idempotent.
# This handles the case where 0017 was marked as applied but its RunPython failed silently.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0017_monthlysalary_cfg_kid_fee_pct_monthlysalary_cfg_mode_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                "ALTER TABLE hr_salaryconfig ADD COLUMN IF NOT EXISTS config_mode varchar(10) DEFAULT 'percentage' NOT NULL",
                "ALTER TABLE hr_monthlysalary ADD COLUMN IF NOT EXISTS cfg_mode varchar(10) DEFAULT 'percentage' NOT NULL",
                "ALTER TABLE hr_monthlysalary ADD COLUMN IF NOT EXISTS cfg_kid_fee_pct numeric(5,2) DEFAULT 0 NOT NULL",
                "ALTER TABLE hr_monthlysalary ADD COLUMN IF NOT EXISTS kid_fee numeric(12,2) DEFAULT 0 NOT NULL",
            ],
            reverse_sql=[
                "ALTER TABLE hr_salaryconfig DROP COLUMN IF EXISTS config_mode",
                "ALTER TABLE hr_monthlysalary DROP COLUMN IF EXISTS cfg_mode",
                "ALTER TABLE hr_monthlysalary DROP COLUMN IF EXISTS cfg_kid_fee_pct",
                "ALTER TABLE hr_monthlysalary DROP COLUMN IF EXISTS kid_fee",
            ],
        ),
    ]
