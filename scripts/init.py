"""
ILLI Initialization Script
Sets up the system for first use.
"""

import asyncio
import sys
from pathlib import Path
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.engine import get_engine
from memory.memory_engine import MemoryEngine
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


async def initialize_system():
    """Initialize the ILLI system"""
    
    console.print("[bold blue]ILLI System Initialization[/bold blue]\n")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        # Create directories
        task = progress.add_task("Creating directory structure...", total=None)
        directories = [
            "data/memory",
            "data/chroma",
            "logs",
            "snapshots",
            "models",
            "backups"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
        
        progress.remove_task(task)
        
        # Initialize memory
        task = progress.add_task("Initializing memory engine...", total=None)
        memory = MemoryEngine()
        await memory.initialize()
        progress.remove_task(task)
        
        # Initialize engine
        task = progress.add_task("Initializing AI engine...", total=None)
        engine = get_engine()
        await engine.initialize()
        progress.remove_task(task)
        
        # Create initial snapshot
        task = progress.add_task("Creating initial snapshot...", total=None)
        snapshot_dir = Path("snapshots/init")
        snapshot_dir.mkdir(exist_ok=True)
        progress.remove_task(task)
    
    console.print("\n[green]✓[/green] System initialized successfully!")
    console.print("\nNext steps:")
    console.print("1. Run: npm install (to install dashboard dependencies)")
    console.print("2. Run: python -m illi.cli start (to start ILLI)")
    console.print("3. Run: npm run dev (to start the dashboard)")


def main():
    """Main entry point"""
    try:
        asyncio.run(initialize_system())
    except KeyboardInterrupt:
        console.print("\n[yellow]Initialization cancelled[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error during initialization: {e}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    main()
