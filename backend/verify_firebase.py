import asyncio
import os
from dotenv import load_dotenv
from shared.firebase_client import get_firestore_client

load_dotenv()

async def verify_firebase():
    print("🔥 Starting Firebase/Firestore Verification...")
    try:
        db = get_firestore_client()
        print("✅ Firestore client initialized successfully")
        
        # Test collection
        test_col = db.collection("_migration_test")
        test_id = "test_doc_1"
        test_data = {
            "name": "Firebase Migration Test",
            "timestamp": "now",
            "status": "success"
        }
        
        print(f"📝 Testing Write to collection '_migration_test' (ID: {test_id})...")
        await test_col.document(test_id).set(test_data)
        print("✅ Write successful")
        
        print(f"📖 Testing Read from ID: {test_id}...")
        doc = await test_col.document(test_id).get()
        if doc.exists:
            print(f"✅ Read successful: {doc.to_dict()}")
        else:
            print("❌ Read failed: Document does not exist")
            
        print("🧹 Cleaning up test document...")
        await test_col.document(test_id).delete()
        print("✅ Cleanup successful")
        
        print("\n🏆 Firebase Migration Verification COMPLETE: STATUS SUCCESS")
        
    except Exception as e:
        print(f"❌ Verification FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(verify_firebase())
