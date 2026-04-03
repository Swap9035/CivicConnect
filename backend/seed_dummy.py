import asyncio
from dotenv import load_dotenv

load_dotenv()

from services.superuser_services.db.connection import connect_to_mongo as connect_superuser_mongo
from services.superuser_services.utils.seed_data import create_initial_superadmin, seed_sample_data
from services.user_service.src.services.user_service import UserService
from services.user_service.src.models.user import UserCreate
from services.user_service.src.db.user_repository import UserRepository

async def run_seed():
    print("Connecting to Mongo db for superuser...")
    await connect_superuser_mongo()
    
    print("Seeding super admin and sample officers...")
    await create_initial_superadmin()
    await seed_sample_data()
    
    print("Seeding dummy citizen...")
    user_service = UserService()
    # Check if user already exists
    repo = UserRepository()
    existing = await repo.get_user_by_mobile("9876543210")
    if existing:
        print("Dummy citizen already exists.")
    else:
        dummy_citizen = UserCreate(
            full_name="Citizen Test",
            mobile_number="9876543210",
            password="Password@123",  # Note: The codebase hashes it in create_user_with_password
            residential_address="123 Main St, Nagpur",
            email="citizen.test@example.com",
            language_preference="English"
        )
        try:
            # We call signup to hash password correctly
            await user_service.signup(dummy_citizen)
            print("Dummy citizen created successfully.")
        except Exception as e:
            print(f"Citizen creation error: {e}")
            
    print("Dummy credentials seeded!")

if __name__ == "__main__":
    asyncio.run(run_seed())
