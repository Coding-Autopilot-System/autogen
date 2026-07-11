import pytest
from fastapi.testclient import TestClient
import os
import sys

# Add scripts to path so we can import proxy
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))
try:
    proxy = __import__('9router_proxy')
    app = proxy.app
    pick_chain = proxy.pick_chain
except ImportError:
    pass # Will handle manually

def test_pick_chain_planner():
    chain, role = pick_chain("You are an autonomous orchestrator.", "Frontier mode: plan next phase")
    assert role == "Planner/Orchestrator"
    # Ensure llama3.2 fallback is present at the end of the chain
    assert chain[-1][0] == "llama3.2-16k"
    assert chain[-1][2] == "ollama"

def test_pick_chain_coder():
    chain, role = pick_chain("You are a helpful assistant.", "Please write a python script")
    assert role == "Coder"
    assert chain[-1][0] == "llama3.2"
