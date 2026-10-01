from django.core.management.base import BaseCommand
from users.models import Store
from agents.planner import PlannerAgent

class Command(BaseCommand):
    help = 'Runs the Executor and Gemini Planner agents for all stores.'

    def handle(self, *args, **kwargs):
        stores = Store.objects.all()
        for store in stores:
            self.stdout.write(f"Initiating AI Agent pipeline for {store.name}...")
            planner = PlannerAgent(store)
            
            try:
                created = planner.generate_recommendations()
                self.stdout.write(self.style.SUCCESS(f"Successfully generated {created} new AI recommendations for {store.name}."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Agent pipeline failed for {store.name}. Error: {e}. Check your GEMINI_API_KEY in .env"))
