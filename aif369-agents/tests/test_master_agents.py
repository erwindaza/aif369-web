"""Test Master program agents

Simplified tests that verify the agents module structure
"""
import pytest


def test_agents_module_exists():
    """Verify agents module exists and is importable"""
    import agents
    assert hasattr(agents, '__file__'), "agents is not a proper module"
    print("✓ agents module structure OK")


def test_models_module_exists():
    """Verify models module exists and is importable"""
    import models
    assert hasattr(models, '__file__'), "models is not a proper module"
    print("✓ models module structure OK")


def test_orchestrator_exists():
    """Verify orchestrator module exists"""
    import orchestrator
    assert hasattr(orchestrator, '__file__'), "orchestrator is not a proper module"
    print("✓ orchestrator module structure OK")


def test_main_app_startup():
    """Verify main FastAPI app can be imported"""
    from main import app
    assert app is not None, "FastAPI app is None"
    assert hasattr(app, 'openapi'), "App doesn't have expected FastAPI attributes"
    print("✓ FastAPI main app OK")


def test_requirements_installed():
    """Verify all required packages are installed"""
    required = [
        'fastapi',
        'uvicorn',
        'langchain',
        'langgraph',
        'pydantic',
        'aiofiles',
        'apscheduler',
    ]

    for pkg in required:
        __import__(pkg)

    print(f"✓ All {len(required)} required packages installed")


@pytest.mark.asyncio
async def test_health_endpoint_definition():
    """Verify health endpoint exists in main app"""
    from main import app
    routes = [route.path for route in app.routes]
    assert any('health' in route for route in routes), "No health endpoint found"
    print("✓ Health endpoint defined in FastAPI app")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
