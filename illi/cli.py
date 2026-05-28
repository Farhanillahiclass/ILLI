"""
ILLI Command Line Interface
"""

import click
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.engine import get_engine
from rich.console import Console
from rich.panel import Panel

console = Console()


@click.group()
def cli():
    """ILLI - Intelligent Local Learning Interface"""
    pass


@cli.command()
@click.option('--config', '-c', help='Configuration file path')
def init(config):
    """Initialize ILLI system"""
    console.print(Panel.fit("ILLI System Initialization", style="bold blue"))
    
    async def _init():
        engine = get_engine()
        await engine.initialize()
        console.print("[green]✓[/green] ILLI initialized successfully!")
    
    asyncio.run(_init())


@cli.command()
@click.option('--config', '-c', help='Configuration file path')
@click.option('--api', is_flag=True, help='Start API server')
def start(config, api):
    """Start ILLI system"""
    console.print(Panel.fit("Starting ILLI System", style="bold green"))
    
    async def _start():
        engine = get_engine()
        await engine.start()
        
        # Start API server if requested
        if api:
            import uvicorn
            from core.api_server import app
            
            console.print("[cyan]Starting API server on http://localhost:8000[/cyan]")
            
            # Run API server in background
            api_task = asyncio.create_task(
                uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
            )
        
        console.print("[green]✓[/green] ILLI is running!")
        if api:
            console.print("[cyan]API server running on http://localhost:8000[/cyan]")
        console.print("\nPress Ctrl+C to stop\n")
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping ILLI...[/yellow]")
            await engine.stop()
            console.print("[green]✓[/green] ILLI stopped")
    
    asyncio.run(_start())


@cli.command()
def status():
    """Check ILLI system status"""
    engine = get_engine()
    status = engine.get_status()
    
    console.print(Panel.fit("ILLI System Status", style="bold cyan"))
    console.print(f"State: {status.state.value}")
    console.print(f"Model Loaded: {status.model_loaded}")
    console.print(f"Active Agents: {status.active_agents}")
    console.print(f"Memory Usage: {status.memory_usage_mb:.2f} MB")
    console.print(f"CPU Usage: {status.cpu_usage_percent:.1f}%")
    console.print(f"GPU Usage: {status.gpu_usage_percent:.1f}%")
    console.print(f"Uptime: {status.uptime_seconds:.1f}s")
    console.print(f"Tasks Completed: {status.tasks_completed}")
    console.print(f"Tasks Failed: {status.tasks_failed}")


@cli.command()
@click.argument('query')
def query(query):
    """Submit a query to ILLI"""
    async def _query():
        engine = get_engine()
        await engine.start()
        
        console.print(f"\n[bold]Query:[/bold] {query}\n")
        response = await engine.query(query)
        
        console.print(f"[bold]Response:[/bold]\n{response}\n")
        
        await engine.stop()
    
    asyncio.run(_query())


def main():
    """Main entry point"""
    cli()


if __name__ == '__main__':
    main()
