#!/usr/bin/env python3
"""
Testing script for Phase 1 + Phase 2
Simulates a complete conversation flow
"""

import asyncio
import json
from datetime import datetime
from orchestrator import orchestrator
from config import PlatformState

# Test conversation flow
TEST_CONVERSATION = [
    # Phase 1: Concierge
    "Hola, me llamo Juan Pérez y trabajo en Falabella como CDO",

    # Phase 1: Discovery
    "Diría que nuestro AI está en un 4/10",
    "Nuestros procesos críticos son: logística, recomendaciones de productos y detección de fraude",
    "Los mayores dolores son: demoras en entregas, recomendaciones poco precisas y pérdidas por fraude que llegan a $2M anuales",
    "La prioridad principal es reducir fraude, después mejorar la cadena de suministro",
    "Tenemos datos de transacciones, pero la calidad es mixta. Tenemos equipo de 5 personas en datos",

    # Phase 2: Request for proposal
    "Genera mi propuesta",
]


async def run_test():
    """Run complete test conversation"""
    print("=" * 80)
    print("🤖 AGENTIC PLATFORM - TESTING PHASE 1 + PHASE 2")
    print("=" * 80)
    print()

    session_id = "test_phase1_2_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    current_state = None

    for i, user_input in enumerate(TEST_CONVERSATION, 1):
        print(f"\n[Turn {i}] User: {user_input}")
        print("-" * 80)

        # Run through orchestrator
        result = await orchestrator.run_conversation(session_id, user_input, current_state)

        # Update state
        current_state = result

        # Print last assistant message
        last_msg = result["messages"][-1] if result["messages"] else None
        if last_msg and last_msg["role"] == "assistant":
            print(f"[Assistant] {last_msg['content'][:500]}...")

        # Print progress
        print(f"\nStage: {result.get('stage')}")
        print(f"Current Agent: {result.get('current_agent')}")
        print(f"Overall Maturity: {result.get('overall_maturity')}/10")

        if result.get("name"):
            print(f"Profile: {result.get('name')} @ {result.get('company')} ({result.get('role')})")

        await asyncio.sleep(1)  # Brief pause between turns

    # Final summary
    print("\n" + "=" * 80)
    print("✅ CONVERSATION COMPLETE")
    print("=" * 80)

    print(f"\n📊 FINAL STATE:")
    print(json.dumps({
        "session_id": current_state.get("session_id"),
        "name": current_state.get("name"),
        "company": current_state.get("company"),
        "email": current_state.get("email"),
        "role": current_state.get("role"),
        "overall_maturity": current_state.get("overall_maturity"),
        "stage": current_state.get("stage"),
        "scorecard": current_state.get("scorecard_scores"),
        "total_turns": len(current_state.get("messages", [])),
    }, indent=2))

    # Extract and show proposal if generated
    if "proposal" in current_state:
        print("\n📄 PROPOSAL GENERATED:")
        proposal = current_state["proposal"]
        # Show first 500 chars
        print(proposal[:1000] + "...\n[Propuesta truncada por longitud]")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_test())
