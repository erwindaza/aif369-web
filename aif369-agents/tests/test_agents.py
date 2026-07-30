"""Test agents locally"""
import asyncio
import httpx

BASE_URL = "http://localhost:8000"


async def test_ventas():
    """Test VENTAS agent"""
    print("\n" + "=" * 60)
    print("TEST 1: VENTAS Agent")
    print("=" * 60)

    queries = [
        "¿Cuánto cuesta el curso de agentes?",
        "Quiero aprender agentes de IA",
        "¿Qué incluye el taller?",
    ]

    async with httpx.AsyncClient() as client:
        for query in queries:
            print(f"\nCliente: {query}")

            response = await client.post(
                f"{BASE_URL}/submit_and_wait",
                json={
                    "agent_type": "ventas",
                    "payload": {
                        "message": query,
                        "customer_phone": "+56912345678",
                    },
                    "priority": 1,
                    "timeout_seconds": 30,
                },
            )

            if response.status_code == 200:
                result = response.json()
                print(f"Status: {result.get('status')}")
                print(f"Agent: {result.get('output', {}).get('agent')}")
                print(f"Response: {result.get('output', {}).get('response', '')[:150]}...")
            else:
                print(f"Error: {response.status_code}")


async def test_caio():
    """Test CAIO agent"""
    print("\n" + "=" * 60)
    print("TEST 2: CAIO Agent (Consulting)")
    print("=" * 60)

    queries = [
        "Necesito implementar agentes en mi empresa",
        "¿Cuánto cuesta una consultoría de IA?",
        "Tenemos un proyecto de arquitectura AI",
    ]

    async with httpx.AsyncClient() as client:
        for query in queries:
            print(f"\nCliente: {query}")

            response = await client.post(
                f"{BASE_URL}/submit_and_wait",
                json={
                    "agent_type": "caio",
                    "payload": {
                        "message": query,
                        "customer_phone": "+56987654321",
                    },
                    "priority": 1,
                    "timeout_seconds": 30,
                },
            )

            if response.status_code == 200:
                result = response.json()
                print(f"Status: {result.get('status')}")
                print(f"Agent: {result.get('output', {}).get('agent')}")
                print(f"Response: {result.get('output', {}).get('response', '')[:150]}...")
            else:
                print(f"Error: {response.status_code}")


async def test_orchestrator_routing():
    """Test intent classification and routing"""
    print("\n" + "=" * 60)
    print("TEST 3: Orchestrator Intent Routing")
    print("=" * 60)

    test_cases = [
        ("¿Cuánto cuesta el curso?", "ventas"),
        ("Necesito implementar IA en mi empresa", "caio"),
        ("¿Cómo compro un curso?", "ventas"),
        ("Consultoría para arquitectura AI", "caio"),
    ]

    async with httpx.AsyncClient() as client:
        for query, expected_agent in test_cases:
            print(f"\nQuery: {query}")
            print(f"Expected: {expected_agent}")

            response = await client.post(
                f"{BASE_URL}/classify",
                json={"query": query},
            )

            if response.status_code == 200:
                result = response.json()
                detected_agent = result.get("intent")
                confidence = result.get("confidence", 0)
                print(f"Detected: {detected_agent} (confidence={confidence:.2f})")
                status = "✓" if detected_agent == expected_agent else "✗"
                print(f"Result: {status}")
            else:
                print(f"Error: {response.status_code}")


async def test_escalation():
    """Test escalation from VENTAS to CAIO"""
    print("\n" + "=" * 60)
    print("TEST 4: Escalation (VENTAS → CAIO)")
    print("=" * 60)

    # Customer starts with sales question
    query = "¿Qué cursos tienen? Estoy interesado pero necesito implementarlo en mi empresa"

    print(f"Customer: {query}")
    print("\nExpected flow:")
    print("1. VENTAS detects that needs consulting")
    print("2. Escalates to CAIO")
    print("3. CAIO responds with consulting options")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/submit_and_wait",
            json={
                "agent_type": "auto",  # Auto-detect
                "payload": {
                    "message": query,
                    "customer_phone": "+56912345678",
                },
            },
        )

        if response.status_code == 200:
            result = response.json()
            print(f"\nResult:")
            print(f"Initial agent: {result.get('output', {}).get('agent')}")
            if result.get("output", {}).get("escalate_to_caio"):
                print("✓ Escalated to CAIO")
                print(f"CAIO Response: {result.get('output', {}).get('response', '')[:150]}...")
        else:
            print(f"Error: {response.status_code}")


async def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║  AIF369 Multi-Agent System - Test Suite               ║")
    print("║  Testing VENTAS + CAIO agents                          ║")
    print("╚" + "=" * 58 + "╝")

    try:
        # Wait for server to be ready
        async with httpx.AsyncClient() as client:
            for i in range(30):
                try:
                    await client.get(f"{BASE_URL}/health", timeout=2)
                    break
                except:
                    if i < 29:
                        await asyncio.sleep(1)
                    else:
                        raise

        # Run tests
        await test_ventas()
        await test_caio()
        await test_orchestrator_routing()
        await test_escalation()

        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure Docker containers are running:")
        print("  docker-compose -f docker-compose.test.yml up")


if __name__ == "__main__":
    asyncio.run(main())
