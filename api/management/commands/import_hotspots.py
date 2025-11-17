"""
Management command to import existing hotspot folders into the Hotspot model
Usage: python manage.py import_hotspots
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from api.models import Hotspot
import os
import re


class Command(BaseCommand):
    help = 'Import existing hotspot folders into the Hotspot model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without actually importing',
        )
        parser.add_argument(
            '--test-connection',
            action='store_true',
            help='Test connection for each hotspot after import',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        test_connection = options['test_connection']

        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('Hotspot Import Utility'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        base_dir = settings.BASE_DIR

        # Find all hotspot_* folders
        hotspot_folders = []
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if os.path.isdir(item_path) and item.startswith('hotspot'):
                hotspot_folders.append(item)

        self.stdout.write(f'\nFound {len(hotspot_folders)} hotspot folder(s):')
        for folder in sorted(hotspot_folders):
            self.stdout.write(f'  - {folder}')

        # Import each hotspot
        imported = 0
        skipped = 0
        updated = 0

        for hotspot_name in sorted(hotspot_folders):
            # Generate display name
            if hotspot_name == 'hotspot':
                display_name = 'Default Hotspot'
            else:
                # Convert hotspot_lab -> Laboratory, hotspot_wifi -> WiFi, etc.
                suffix = hotspot_name.replace('hotspot_', '').replace('hotspot', '')
                if suffix:
                    display_name = suffix.replace('_', ' ').title()
                else:
                    display_name = 'Default Hotspot'

            # Check if already exists
            existing = Hotspot.objects.filter(hotspot_name=hotspot_name).first()

            if existing:
                self.stdout.write(f'\n[SKIP] {hotspot_name}')
                self.stdout.write(f'       Already exists as: {existing.display_name}')
                skipped += 1
            else:
                self.stdout.write(f'\n[NEW] {hotspot_name}')
                self.stdout.write(f'      Display Name: {display_name}')

                if not dry_run:
                    hotspot = Hotspot.objects.create(
                        hotspot_name=hotspot_name,
                        display_name=display_name,
                        description=f'Auto-imported from {hotspot_name} folder',
                        is_active=True
                    )

                    if test_connection:
                        self.test_hotspot_connection(hotspot)

                    imported += 1
                else:
                    imported += 1

        # Summary
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('Import Summary:'))
        self.stdout.write(f'  New hotspots: {imported}')
        self.stdout.write(f'  Skipped (already exist): {skipped}')
        self.stdout.write(f'  Total folders scanned: {len(hotspot_folders)}')

        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN completed - no changes were made'))
            self.stdout.write(self.style.WARNING('Run without --dry-run to actually import'))
        else:
            self.stdout.write(self.style.SUCCESS('\nImport completed successfully!'))

        self.stdout.write('=' * 70)

    def test_hotspot_connection(self, hotspot):
        """Test connection for a hotspot"""
        from django.utils import timezone

        base_dir = settings.BASE_DIR
        folder_path = os.path.join(base_dir, hotspot.hotspot_name)
        login_file_path = os.path.join(folder_path, 'login.html')

        # Check folder
        folder_exists = os.path.isdir(folder_path)

        # Check login.html
        login_file_exists = os.path.isfile(login_file_path)

        # Check config
        config_matched = False
        if login_file_exists:
            try:
                with open(login_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    pattern = r"window\.HOTSPOT_NAME\s*=\s*['\"]([^'\"]+)['\"]"
                    match = re.search(pattern, content)
                    if match:
                        found_name = match.group(1)
                        config_matched = (found_name == hotspot.hotspot_name)
            except Exception:
                pass

        # Update status
        hotspot.folder_exists = folder_exists
        hotspot.login_file_exists = login_file_exists
        hotspot.config_matched = config_matched
        hotspot.last_checked = timezone.now()
        hotspot.save()

        # Display status
        status_icon = hotspot.status_icon
        self.stdout.write(f'      Status: {status_icon} {hotspot.status.upper()}')
        if not folder_exists:
            self.stdout.write(self.style.ERROR(f'        ✗ Folder not found'))
        if not login_file_exists:
            self.stdout.write(self.style.ERROR(f'        ✗ login.html not found'))
        if folder_exists and login_file_exists and not config_matched:
            self.stdout.write(self.style.WARNING(f'        ⚠ Config mismatch in login.html'))
        if hotspot.status == 'ready':
            self.stdout.write(self.style.SUCCESS(f'        ✓ Ready to use'))
