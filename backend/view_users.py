"""
View all registered users in MongoDB.
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def view_users():
    """View all users from database."""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb+srv://Keerthana:DPXK2AKcr88vY4qh@cluster0.izvwxc3.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    db = client.agentic_ai_db
    
    # Get all users
    users = await db.users.find().to_list(length=100)
    
    print(f"\n{'='*80}")
    print(f"REGISTERED USERS ({len(users)} total)")
    print(f"{'='*80}\n")
    
    for user in users:
        print(f"User ID:      {user['user_id']}")
        print(f"Email:        {user['email']}")
        print(f"Name:         {user['full_name']}")
        print(f"Role:         {user['role']}")
        print(f"Institution:  {user.get('institution', 'N/A')}")
        print(f"Active:       {user.get('is_active', True)}")
        print(f"Created:      {user['created_at']}")
        print(f"{'-'*80}\n")
    
    # Close connection
    client.close()

if __name__ == "__main__":
    asyncio.run(view_users())