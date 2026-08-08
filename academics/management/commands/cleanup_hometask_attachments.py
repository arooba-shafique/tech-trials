"""
Management command to delete homework attachments that are past their due date.

Usage:
    python manage.py cleanup_hometask_attachments

Run this daily via cron or Vercel cron job to keep storage clean.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from academics.models import HomeTask


class Command(BaseCommand):
    help = 'Delete homework attachments that are past their due date'

    def handle(self, *args, **options):
        today = timezone.now().date()
        overdue_tasks = HomeTask.objects.filter(
            due_date__lt=today,
            attachment__isnull=False
        )

        count = 0
        for task in overdue_tasks:
            if task.attachment:
                task.attachment.delete(save=False)
                task.attachment = None
                task.save(update_fields=['attachment'])
                count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Successfully cleaned up {count} homework attachment(s).')
        )
