"""Test all API keys and service connections."""

import os
import sys
import json
import asyncio

# Load .env file from parent directory
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Also try local .env
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

import httpx

PASS = "\033[92m✓ PASS\033[0m"
FAIL = "\033[91m✗ FAIL\033[0m"
WARN = "\033[93m⚠ WARN\033[0m"


def check_env_var(name: str) -> str | None:
    val = os.getenv(name)
    if not val or val.startswith("your-") or val == "sk-ant-xxx":
        print(f"  {FAIL}  {name} — not set or still placeholder")
        return None
    masked = val[:8] + "..." + val[-4:] if len(val) > 16 else val[:4] + "..."
    print(f"  {PASS}  {name} — {masked}")
    return val


async def test_supabase(url: str, anon_key: str, service_key: str):
    print("\n── Supabase ──")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{url}/rest/v1/",
                headers={
                    "apikey": anon_key,
                    "Authorization": f"Bearer {anon_key}",
                },
                timeout=10,
            )
            if resp.status_code == 200:
                print(f"  {PASS}  Connection OK (anon key works)")
            else:
                print(f"  {FAIL}  HTTP {resp.status_code}: {resp.text[:100]}")
        except Exception as e:
            print(f"  {FAIL}  Connection failed: {e}")

        # Test service role key
        try:
            resp = await client.get(
                f"{url}/rest/v1/profiles?select=count&limit=0",
                headers={
                    "apikey": service_key,
                    "Authorization": f"Bearer {service_key}",
                },
                timeout=10,
            )
            if resp.status_code == 200:
                print(f"  {PASS}  Service role key works (profiles table accessible)")
            else:
                print(f"  {WARN}  Service role returned HTTP {resp.status_code} — table may not exist yet")
        except Exception as e:
            print(f"  {FAIL}  Service role test failed: {e}")


async def test_anthropic(api_key: str):
    print("\n── Anthropic (Claude) ──")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": "Say 'ok'"}],
                },
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                text = data["content"][0]["text"]
                print(f"  {PASS}  Claude responded: \"{text}\"")
            elif resp.status_code == 401:
                print(f"  {FAIL}  Invalid API key")
            elif resp.status_code == 429:
                print(f"  {WARN}  Rate limited — but key is valid")
            else:
                print(f"  {FAIL}  HTTP {resp.status_code}: {resp.text[:100]}")
        except Exception as e:
            print(f"  {FAIL}  Connection failed: {e}")


async def test_runway(api_key: str):
    print("\n── Runway ──")
    async with httpx.AsyncClient() as client:
        try:
            # Just check auth with a lightweight call
            resp = await client.get(
                "https://api.dev.runwayml.com/v1/tasks",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "X-Runway-Version": "2024-11-06",
                },
                params={"limit": 1},
                timeout=10,
            )
            if resp.status_code == 200:
                print(f"  {PASS}  API key valid, connection OK")
            elif resp.status_code == 401:
                print(f"  {FAIL}  Invalid API key")
            elif resp.status_code == 404:
                print(f"  {WARN}  Endpoint may have changed — key format looks OK")
            else:
                print(f"  {WARN}  HTTP {resp.status_code}: {resp.text[:100]}")
        except Exception as e:
            print(f"  {FAIL}  Connection failed: {e}")


async def test_elevenlabs(api_key: str):
    print("\n── ElevenLabs ──")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                "https://api.elevenlabs.io/v1/user",
                headers={"xi-api-key": api_key},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                tier = data.get("subscription", {}).get("tier", "unknown")
                chars_left = data.get("subscription", {}).get("character_count", 0)
                char_limit = data.get("subscription", {}).get("character_limit", 0)
                print(f"  {PASS}  Tier: {tier}, Characters: {chars_left}/{char_limit}")
            elif resp.status_code == 401:
                print(f"  {FAIL}  Invalid API key")
            else:
                print(f"  {FAIL}  HTTP {resp.status_code}: {resp.text[:100]}")
        except Exception as e:
            print(f"  {FAIL}  Connection failed: {e}")


async def test_deepgram(api_key: str):
    print("\n── Deepgram ──")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                "https://api.deepgram.com/v1/projects",
                headers={"Authorization": f"Token {api_key}"},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                projects = data.get("projects", [])
                print(f"  {PASS}  API key valid, {len(projects)} project(s) found")
            elif resp.status_code == 401:
                print(f"  {FAIL}  Invalid API key")
            else:
                print(f"  {FAIL}  HTTP {resp.status_code}: {resp.text[:100]}")
        except Exception as e:
            print(f"  {FAIL}  Connection failed: {e}")


async def test_redis(redis_url: str):
    print("\n── Redis ──")
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(redis_url)
        await r.ping()
        print(f"  {PASS}  Connected and responding")
        await r.aclose()
    except ImportError:
        try:
            import redis as sync_redis
            r = sync_redis.from_url(redis_url)
            r.ping()
            print(f"  {PASS}  Connected and responding (sync)")
            r.close()
        except ImportError:
            print(f"  {WARN}  redis package not installed — skipping")
        except Exception as e:
            print(f"  {FAIL}  Connection failed: {e}")
    except Exception as e:
        print(f"  {FAIL}  Connection failed: {e}")


async def main():
    print("=" * 50)
    print("  ClipPilot Lite — API Key Validation")
    print("=" * 50)

    # Check all env vars exist
    print("\n── Environment Variables ──")
    supabase_url = check_env_var("SUPABASE_URL")
    supabase_anon = check_env_var("SUPABASE_ANON_KEY")
    supabase_service = check_env_var("SUPABASE_SERVICE_ROLE_KEY")
    anthropic_key = check_env_var("ANTHROPIC_API_KEY")
    runway_key = check_env_var("RUNWAY_API_KEY")
    elevenlabs_key = check_env_var("ELEVENLABS_API_KEY")
    deepgram_key = check_env_var("DEEPGRAM_API_KEY")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    print(f"  {PASS}  REDIS_URL — {redis_url}")

    # Test each service
    if supabase_url and supabase_anon and supabase_service:
        await test_supabase(supabase_url, supabase_anon, supabase_service)

    if anthropic_key:
        await test_anthropic(anthropic_key)

    if runway_key:
        await test_runway(runway_key)

    if elevenlabs_key:
        await test_elevenlabs(elevenlabs_key)

    if deepgram_key:
        await test_deepgram(deepgram_key)

    await test_redis(redis_url)

    print("\n" + "=" * 50)
    print("  Done! Fix any FAIL items above, then start the server.")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
