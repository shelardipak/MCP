import os
import json
import subprocess
from pylint.lint import Run
from pylint.reporters.json_reporter import JSONReporter
from io import StringIO

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
    temp_file = "temp_code.py"
    with open(temp_file, "w") as f:
      f.write(code)
    output = StringIO()
    reporter = JSONReporter(output=output)
    issues = []
    try:
      Run([temp_file], reporter=reporter, exit=False)
      output.seek(0)
      result = output.read()
      try:
        pylint_output = json.loads(result)
        for message in pylint_output:
          issues.append({
            "line": message["line"],
            "issue": message["message"],
            "suggestion": message["symbol"],
            "rule": message["message-id"]
          })
      except Exception as parse_e:
        issues.append({
          "line": 0,
          "issue": f"Failed to parse pylint output: {parse_e}",
          "suggestion": "Ensure pylint is installed and working correctly",
          "severity": "error",
          "rule": "pylint-output"
        })
    except Exception as e:
      issues.append({
        "line": 0,
        "issue": f"Pylint error: {e}",
        "suggestion": "Check pylint installation",
        "severity": "error",
        "rule": "pylint-error"
      })
    finally:
      os.remove(temp_file)
    return issues