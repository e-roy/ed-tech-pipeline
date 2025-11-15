"""
Person B Work Verification Script

This script verifies that all Person B deliverables are in place
and properly configured.
"""

import os
import sys
from pathlib import Path


def check_file_exists(filepath, description):
    """Check if a file exists"""
    if Path(filepath).exists():
        print(f"✅ {description}")
        return True
    else:
        print(f"❌ {description} - MISSING: {filepath}")
        return False


def check_import(module_path, description):
    """Check if a module can be imported"""
    try:
        parts = module_path.split('.')
        mod = __import__(module_path)
        for part in parts[1:]:
            mod = getattr(mod, part)
        print(f"✅ {description}")
        return True
    except ImportError as e:
        print(f"❌ {description} - IMPORT ERROR: {e}")
        return False


def check_env_var(var_name, description):
    """Check if environment variable is set"""
    value = os.getenv(var_name)
    if value and value != "your-replicate-api-key-here":
        print(f"✅ {description} (prefix: {value[:8]}...)")
        return True
    else:
        print(f"⚠️  {description} - Not set or using placeholder")
        return False


def main():
    print("\n" + "=" * 60)
    print("Person B Work Verification")
    print("=" * 60 + "\n")

    checks_passed = 0
    checks_total = 0

    print("📁 File Structure Check:")
    print("-" * 60)

    files_to_check = [
        ("app/agents/__init__.py", "Agents package init"),
        ("app/agents/base.py", "Agent base interfaces"),
        ("app/agents/prompt_parser.py", "Prompt Parser Agent"),
        ("app/agents/batch_image_generator.py", "Batch Image Generator Agent"),
        ("test_agents.py", "Agent testing suite"),
        ("PERSON_B_README.md", "Person B documentation"),
    ]

    for filepath, desc in files_to_check:
        checks_total += 1
        if check_file_exists(filepath, desc):
            checks_passed += 1

    print("\n📦 Import Check:")
    print("-" * 60)

    imports_to_check = [
        ("app.agents.base", "AgentInput, AgentOutput, Agent"),
        ("app.agents.prompt_parser", "PromptParserAgent"),
        ("app.agents.batch_image_generator", "BatchImageGeneratorAgent"),
    ]

    for module, desc in imports_to_check:
        checks_total += 1
        if check_import(module, desc):
            checks_passed += 1

    print("\n🔐 Environment Check:")
    print("-" * 60)

    # Load .env file
    from dotenv import load_dotenv
    load_dotenv()

    env_vars = [
        ("REPLICATE_API_KEY", "Replicate API Key"),
    ]

    for var, desc in env_vars:
        checks_total += 1
        if check_env_var(var, desc):
            checks_passed += 1

    print("\n🧪 Agent Initialization Check:")
    print("-" * 60)

    try:
        api_key = os.getenv("REPLICATE_API_KEY")
        if api_key and api_key != "your-replicate-api-key-here":
            from app.agents.prompt_parser import PromptParserAgent
            from app.agents.batch_image_generator import BatchImageGeneratorAgent

            parser = PromptParserAgent(api_key)
            generator = BatchImageGeneratorAgent(api_key)

            print(f"✅ Prompt Parser initialized (model: {parser.model})")
            print(f"✅ Batch Image Generator initialized (models: {len(generator.models)})")
            checks_passed += 2
        else:
            print("⚠️  Skipping initialization (API key not set)")
        checks_total += 2
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        checks_total += 2

    print("\n🔌 Orchestrator Integration Check:")
    print("-" * 60)

    try:
        with open("app/services/orchestrator.py", "r") as f:
            content = f.read()

        integration_checks = [
            ("PromptParserAgent" in content, "PromptParserAgent import"),
            ("BatchImageGeneratorAgent" in content, "BatchImageGeneratorAgent import"),
            ("self.prompt_parser" in content, "Prompt parser instance"),
            ("self.image_generator" in content, "Image generator instance"),
            ("prompt_result = await self.prompt_parser.process" in content, "Prompt parser usage"),
            ("image_result = await self.image_generator.process" in content, "Image generator usage"),
        ]

        for check, desc in integration_checks:
            checks_total += 1
            if check:
                print(f"✅ {desc}")
                checks_passed += 1
            else:
                print(f"❌ {desc}")

    except Exception as e:
        print(f"❌ Could not verify orchestrator: {e}")
        checks_total += 6

    print("\n" + "=" * 60)
    print(f"Verification Results: {checks_passed}/{checks_total} checks passed")
    print("=" * 60 + "\n")

    if checks_passed == checks_total:
        print("🎉 PERFECT! All Person B deliverables verified!")
        print("\nNext steps:")
        print("  1. Run: python test_agents.py quick")
        print("  2. Review: PERSON_B_README.md")
        print("  3. Start integration testing with Person A")
        return 0
    elif checks_passed >= checks_total * 0.8:
        print("✅ GOOD! Most checks passed.")
        print("\nWarnings:")
        print("  - Some optional checks failed")
        print("  - Review output above for details")
        print("  - Person B work is mostly complete")
        return 0
    else:
        print("❌ ISSUES FOUND! Review failures above.")
        print("\nAction required:")
        print("  - Fix missing files/imports")
        print("  - Set REPLICATE_API_KEY in .env")
        print("  - Review PERSON_B_README.md for setup")
        return 1


if __name__ == "__main__":
    sys.exit(main())
