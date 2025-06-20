#!/usr/bin/env python3
"""Allow running the module directly with python -m summarize_mcp."""

import asyncio
import sys
from .server import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer interrupted by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Fatal server error: {e}", file=sys.stderr)
        sys.exit(1)