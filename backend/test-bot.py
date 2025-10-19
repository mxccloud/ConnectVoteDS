import time
from bot_api import VoterInfoBot

def test_bot_standalone():
    """Test the bot independently"""
    print("🧪 Starting standalone bot test...")
    
    # Test ID number (use a valid 13-digit SA ID for real test)
    test_id = "8312040719081"  # Replace with actual test ID
    
    print(f"🔢 Testing with ID: {test_id}")
    
    # Create bot instance
    bot = VoterInfoBot()
    
    try:
        # Start timer
        start_time = time.time()
        
        # Run the bot
        print("🚀 Running bot...")
        results = bot.run_bot(test_id)
        
        # Calculate execution time
        end_time = time.time()
        execution_time = end_time - start_time
        
        if results:
            print("\n" + "="*60)
            print("✅ BOT TEST SUCCESSFUL!")
            print("="*60)
            print(f"🕒 Execution Time: {execution_time:.2f} seconds")
            print(f"🆔 Identity Number: {results.get('identity_number', 'N/A')}")
            print(f"🏛️ Ward: {results.get('ward', 'N/A')}")
            print(f"📍 Voting District: {results.get('voting_district', 'N/A')}")
            print(f"🏘️ Municipality: {results.get('municipality', 'N/A')}")
            print(f"🌍 Province: {results.get('province', 'N/A')}")
            print("="*60)
        else:
            print("\n❌ BOT TEST FAILED: No results returned")
            
    except Exception as e:
        print(f"\n💥 BOT TEST ERROR: {e}")
        
    finally:
        # Always close the browser
        bot.close()
        print("🔒 Browser closed.")

if __name__ == "__main__":
    test_bot_standalone()
