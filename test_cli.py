#!/usr/bin/env python3
"""
Quick test to verify the CLI is working
"""

import subprocess
import sys


def run_command(cmd):
    """Run a command and return success status"""
    print(f"Testing: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"  ✓ Success")
        return True
    else:
        print(f"  ✗ Failed: {result.stderr}")
        return False


def main():
    """Test basic CLI functionality"""
    print("=== Claude Lab CLI Test ===\n")

    tests = [
        ("lab --help", "Help command"),
        ("lab check", "System check"),
        ("lab image-list", "List images"),
        ("lab list", "List labs"),
    ]

    results = []
    for cmd, description in tests:
        print(f"\nTest: {description}")
        success = run_command(cmd)
        results.append((description, success))
        print()

    # Summary
    print("\n=== Test Summary ===")
    passed = sum(1 for _, success in results if success)
    total = len(results)

    for description, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {description}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✅ All tests passed! CLI is working correctly.")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
