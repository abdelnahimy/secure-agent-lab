import json
import sys


def main():
    try:
        # The hook provides the tool call arguments as a JSON object via stdin
        input_data = sys.stdin.read()
        if not input_data.strip():
            sys.exit(0)

        data = json.loads(input_data)

        # Extract the command being executed. The parameter name might be
        # "CommandLine" or "command" depending on the tool schema.
        command = data.get("CommandLine", "") or data.get("command", "")

        if not command:
            sys.exit(0)

        # Define destructive patterns to block
        blocked_patterns = ["rm -rf /", "rm -rf *", "mkfs", "> /dev/sda"]

        for pattern in blocked_patterns:
            if pattern in command:
                # Print the reason to stderr and exit with non-zero status to block
                print(
                    f"Security Policy Violation: Command blocked due to destructive pattern '{pattern}'",
                    file=sys.stderr,
                )
                sys.exit(1)

        # Exit cleanly if no violations found
        sys.exit(0)

    except json.JSONDecodeError:
        print("Error: Could not parse stdin as JSON", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error validating tool call: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
