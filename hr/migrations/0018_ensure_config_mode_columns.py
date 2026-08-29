# Migration 0018: Safety net — ensure config_mode/cfg_mode columns exist.
# Uses RunPython to handle both PostgreSQL and SQLite.

from django.db import migrations


def forwards(apps, schema_editor):
    conn = schema_editor.connection
    vendor = conn.vendor  # 'postgresql', 'sqlite', etc.

    with conn.cursor() as cursor:
        if vendor == 'postgresql':
            cursor.execute("ALTER TABLE hr_salaryconfig ADD COLUMN IF NOT EXISTS config_mode varchar(10) DEFAULT 'percentage' NOT NULL")
            cursor.execute("ALTER TABLE hr_monthlysalary ADD COLUMN IF NOT EXISTS cfg_mode varchar(10) DEFAULT 'percentage' NOT NULL")
            cursor.execute("ALTER TABLE hr_monthlysalary ADD COLUMN IF NOT EXISTS cfg_kid_fee_pct numeric(5,2) DEFAULT 0 NOT NULL")
            cursor.execute("ALTER TABLE hr_monthlysalary ADD COLUMN IF NOT EXISTS kid_fee numeric(12,2) DEFAULT 0 NOT NULL")
        else:
            # SQLite or other — check if columns exist before adding
            cursor.execute("PRAGMA table_info(hr_salaryconfig)")
            cols = {row[1] for row in cursor.fetchall()}
            if 'config_mode' not in cols:
                cursor.execute("ALTER TABLE hr_salaryconfig ADD COLUMN config_mode varchar(10) DEFAULT 'percentage' NOT NULL")

            cursor.execute("PRAGMA table_info(hr_monthlysalary)")
            cols = {row[1] for row in cursor.fetchall()}
            if 'cfg_mode' not in cols:
                cursor.execute("ALTER TABLE hr_monthlysalary ADD COLUMN cfg_mode varchar(10) DEFAULT 'percentage' NOT NULL")
            if 'cfg_kid_fee_pct' not in cols:
                cursor.execute("ALTER TABLE hr_monthlysalary ADD COLUMN cfg_kid_fee_pct decimal(5,2) DEFAULT 0 NOT NULL")
            if 'kid_fee' not in cols:
                cursor.execute("ALTER TABLE hr_monthlysalary ADD COLUMN kid_fee decimal(12,2) DEFAULT 0 NOT NULL")


def backwards(apps, schema_editor):
    conn = schema_editor.connection
    vendor = conn.vendor
    with conn.cursor() as cursor:
        if vendor == 'postgresql':
            cursor.execute("ALTER TABLE hr_salaryconfig DROP COLUMN IF EXISTS config_mode")
            cursor.execute("ALTER TABLE hr_monthlysalary DROP COLUMN IF EXISTS cfg_mode")
            cursor.execute("ALTER TABLE hr_monthlysalary DROP COLUMN IF EXISTS cfg_kid_fee_pct")
            cursor.execute("ALTER TABLE hr_monthlysalary DROP COLUMN IF EXISTS kid_fee")
        else:
            # SQLite doesn't support DROP COLUMN IF EXISTS — skip
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0017_monthlysalary_cfg_kid_fee_pct_monthlysalary_cfg_mode_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
