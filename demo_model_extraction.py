#!/usr/bin/env python3
"""Demo script to show LLM model extraction from Kiro settings."""

from pathlib import Path
from kiro_analyzer.analyzers import ModelUsageCalculator

def main():
    """Extract and display LLM model configuration from Kiro settings."""
    print("=" * 60)
    print("Kiro LLM Model Configuration Extraction")
    print("=" * 60)
    print()
    
    # Create calculator with default settings path
    calculator = ModelUsageCalculator()
    
    # Extract model info (no log entries needed for settings extraction)
    result = calculator.calculate([])
    
    print("📊 Model Configuration from Settings:")
    print("-" * 60)
    print(f"  Primary Model:     {result['configured_model']}")
    print(f"  Agent Model:       {result['agent_model']}")
    print(f"  Agent Autonomy:    {result['model_settings'].get('agentAutonomy', 'N/A')}")
    print()
    
    print("📁 Settings File Location:")
    print(f"  {calculator.settings_path}")
    print()
    
    if result['configured_model']:
        print("✅ Successfully extracted model configuration!")
    else:
        print("⚠️  No model configuration found in settings")
    
    print()
    print("=" * 60)

if __name__ == "__main__":
    main()
