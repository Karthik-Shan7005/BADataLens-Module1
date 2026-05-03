import os
from dotenv import load_dotenv

load_dotenv()

# Test 1: Anthropic API key
print("Testing Anthropic API key...")
try:
    import anthropic
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=50,
        messages=[{"role": "user", "content": "Say OK"}]
    )
    print(f"  Anthropic OK — response: {msg.content[0].text.strip()}")
except Exception as e:
    print(f"  Anthropic FAILED: {e}")

# Test 2: SQL Server connection
print("Testing SQL Server connection...")
try:
    from sqlalchemy import create_engine, text
    engine = create_engine(os.getenv("DATABASE_URL"))
    with engine.connect() as conn:
        result = conn.execute(text("SELECT DB_NAME() AS db"))
        db_name = result.fetchone()[0]
    print(f"  SQL Server OK — connected to database: {db_name}")
except Exception as e:
    print(f"  SQL Server FAILED: {e}")
