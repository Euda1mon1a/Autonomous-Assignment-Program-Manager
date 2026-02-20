import sys
import os

# Add current directory to sys.path
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.services.game_theory import get_game_theory_service


def seed_game_theory():
    db = SessionLocal()
    try:
        service = get_game_theory_service(db)
        print("Creating default strategies...")
        service.create_default_strategies()

        strategies = service.list_strategies(active_only=False)
        print(f"Total strategies available: {len(strategies)}")
        for s in strategies:
            print(f" - {s.name} ({s.strategy_type})")

        # Also create a sample tournament if strategies exist
        if len(strategies) >= 2:
            print("\nCreating sample tournament...")
            tournament = service.create_tournament(
                name="Initial Baseline Tournament",
                description="Automated baseline tournament comparing default strategies.",
                strategy_ids=[s.id for s in strategies],
                created_by="system",
            )
            print(f"Created tournament: {tournament.name} (ID: {tournament.id})")

            print("\nRunning tournament...")
            results = service.run_tournament(tournament.id)
            print(f"Tournament complete! Winner: {results['winner']}")

    finally:
        db.close()


if __name__ == "__main__":
    seed_game_theory()
