#!/usr/bin/env python3
"""
Simple test script for chart generation reliability.
Tests 10 different prompts covering various chart types and vague queries.
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5000/chat"

TEST_PROMPTS = [
    "show me revenue by region",
    "bar chart of sales",
    "pie chart of accounts by industry",
    "line chart of revenue over time",
    "scatter plot of revenue vs budget",
    "show me sales data",
    "what about opportunities?",
    "area chart of revenue by month",
    "histogram of revenue",
    "3d scatter of revenue, budget, and value"
]

def test_prompt(prompt: str, language: str = "en") -> dict:
    """Test a single prompt and return result."""
    payload = {
        "message": prompt,
        "language": language
    }
    
    try:
        response = requests.post(BASE_URL, json=payload, timeout=30)
        result = {
            "prompt": prompt,
            "status_code": response.status_code,
            "has_error": False,
            "has_chart": False,
            "chart_type": None,
            "error_type": None,
            "message": None
        }
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for error response
            if "error_type" in data:
                result["has_error"] = True
                result["error_type"] = data.get("error_type")
                result["message"] = data.get("message", "")
            # Check for successful chart
            elif "chart_json" in data:
                result["has_chart"] = True
                result["chart_type"] = data.get("chart_type")
                result["title"] = data.get("title", "")
            # Check for text response (no chart)
            elif "response" in data:
                result["message"] = str(data.get("response", ""))[:100]
        else:
            result["has_error"] = True
            result["message"] = f"HTTP {response.status_code}"
            
    except Exception as e:
        result = {
            "prompt": prompt,
            "status_code": None,
            "has_error": True,
            "has_chart": False,
            "error_type": "EXCEPTION",
            "message": str(e)
        }
    
    return result

def main():
    """Run all tests and report results."""
    print("=" * 60)
    print("Chart Generation Reliability Tests")
    print("=" * 60)
    print()
    
    results = []
    for prompt in TEST_PROMPTS:
        print(f"Testing: '{prompt}'...", end=" ")
        result = test_prompt(prompt)
        results.append(result)
        
        if result["has_chart"]:
            print(f"✓ SUCCESS (chart_type={result['chart_type']})")
        elif result["has_error"]:
            print(f"✗ ERROR ({result.get('error_type', 'UNKNOWN')}): {result.get('message', '')[:50]}")
        else:
            print(f"? NO CHART (message: {result.get('message', '')[:50]})")
    
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    
    success_count = sum(1 for r in results if r["has_chart"])
    error_count = sum(1 for r in results if r["has_error"])
    no_chart_count = len(results) - success_count - error_count
    
    print(f"Total tests: {len(results)}")
    print(f"Successful charts: {success_count}")
    print(f"Errors: {error_count}")
    print(f"No chart (text response): {no_chart_count}")
    print()
    
    # Check for 500 errors (should never happen)
    status_500 = [r for r in results if r.get("status_code") == 500]
    if status_500:
        print("⚠️  WARNING: Found 500 errors (should never happen):")
        for r in status_500:
            print(f"  - {r['prompt']}: {r.get('message', '')}")
        print()
    
    # Detailed results
    if error_count > 0:
        print("Error details:")
        for r in results:
            if r["has_error"]:
                print(f"  - {r['prompt']}: {r.get('error_type')} - {r.get('message', '')[:80]}")
        print()
    
    # Success rate
    success_rate = (success_count / len(results)) * 100
    print(f"Success rate: {success_rate:.1f}%")
    
    # Exit code
    if status_500:
        sys.exit(1)
    elif success_rate >= 80:
        print("✓ Tests passed (>=80% success rate)")
        sys.exit(0)
    else:
        print("⚠️  Tests passed but success rate < 80%")
        sys.exit(1)

if __name__ == "__main__":
    main()

