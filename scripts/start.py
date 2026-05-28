"""
ILLI Start Script
Starts the ILLI system.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.engine import get_engine
from rich.console import Console

console = Console()


async def start_system():
    """Start the ILLI system"""
    console.print("[bold green]Starting ILLI System[/bold green]\n")
    
    engine = get_engine()
    await engine.start()
    
    console.print("[green]✓[/green] ILLI is running!")
    console.print("\nPress Ctrl+C to stop\n")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping ILLI...[/yellow]")
        await engine.stop()
        console.print("[green]✓[/green] ILLI stopped")


def main():
    """Main entry point"""
    try:
        asyncio.run(start_system())
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    main()
