from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0001_initial'),
        ('hr', '0011_monthlysalary_has_custom_config'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmployeeDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('document_type', models.CharField(choices=[('degree', 'Degree'), ('certificate', 'Certificate'), ('experience', 'Experience Letter'), ('cnic', 'CNIC'), ('other', 'Other')], max_length=20)),
                ('title', models.CharField(blank=True, default='', max_length=200)),
                ('file', models.FileField(upload_to='employee_docs/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='academics.teacherprofile')),
            ],
            options={
                'ordering': ['-uploaded_at'],
            },
        ),
    ]
