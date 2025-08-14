import asyncio
from app.database import connect_to_mongo, get_database

async def check_users():
    await connect_to_mongo()
    db = get_database()
    users = await db.users.find().to_list(None)
    print(f'Found {len(users)} users')
    for user in users:
        print(f'User: {user.get("email", "No email")} - Active: {user.get("is_active", False)}')

if __name__ == "__main__":
    asyncio.run(check_users())
