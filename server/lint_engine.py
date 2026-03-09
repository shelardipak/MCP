import os
import json
import subprocess

async def run_lint_analysis(code: str, custom_rules: dict = None):
    """
    Analyze Python code using pylint as an external tool.
    This replaces the custom linting logic with pylint.

    Args:
        code: The Python code to analyze
        custom_rules: Optional custom rules (not used with pylint)

    Returns:
        List of issues found in the code
    """
    # Save the code to a temporary file
    temp_file = "temp_code.py"
    with open(temp_file, "w") as f:
        f.write(code)

    print("Running pylint on the code...temp file created:", temp_file)
    # Run pylint as a subprocess
    result = subprocess.run(
        ["python", "-m", "pylint", "--output-format=json", temp_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    print("Pylint completed with return code:", result.returncode)

    # Parse pylint JSON output
    issues = []
    if result.stdout:
        try:
            pylint_output = json.loads(result.stdout)
            for message in pylint_output:
                issues.append({
                    "line": message["line"],
                    "issue": message["message"],
                    "suggestion": message["symbol"],
                    "severity": message["type"],
                    "rule": message["message-id"]
                })
        except json.JSONDecodeError:
            issues.append({
                "line": 0,
                "issue": "Failed to parse pylint output",
                "suggestion": "Ensure pylint is installed and working correctly",
                "severity": "error",
                "rule": "pylint-output"
            })

    # Clean up temporary file
    os.remove(temp_file)

    return issues