from django.core.management.base import BaseCommand, CommandError
from colleges.models import College
from rest_framework_api_key.models import APIKey

class Command(BaseCommand):
    help = "Interactively register a new college and generate an API key for it"

    def handle(self, *args, **options):
        # Get input interactively
        self.stdout.write(self.style.MIGRATE_HEADING("📘 Register New College"))
        name = input("Enter college name: ").strip()
        code = input("Enter college code (unique, e.g., ABC123): ").strip().upper()

        if not name or not code:
            raise CommandError("❌ Both name and code are required.")

        if College.objects.filter(code=code).exists():
            raise CommandError(f"❌ College with code '{code}' already exists.")

        # Create college and API key
        college = College.objects.create(name=name, code=code)
        api_key, key = APIKey.objects.create_key(name=f"{college.code}-key")
        college.api_key = api_key
        college.save()

        # Output details
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"✅ College '{college.name}' registered successfully!"))
        self.stdout.write(self.style.SUCCESS(f"   College Code: {college.code}"))
        self.stdout.write(self.style.SUCCESS(f"   API Key: {key}"))
        self.stdout.write(self.style.WARNING("⚠️  Make sure to store this API key securely — it will not be shown again."))
