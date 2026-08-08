from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0014_separationrecord'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='separationrecord',
            name='separation_date',
        ),
    ]
