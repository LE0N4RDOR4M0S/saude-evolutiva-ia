import typer
from rich.console import Console
from rich.table import Table
from .collector import GitCollector
from .analyzer import AIAnalyzer
import os

app = typer.Typer()
console = Console()

@app.command()
def scan(
    path: str = typer.Argument(..., help="Caminho local do repositório"),
    commits: int = typer.Option(100, help="Quantos commits analisar para trás"),
    ai: bool = typer.Option(True, help="Executar análise de IA")
):
    if not os.path.exists(path):
        console.print(f"[bold red]Erro:[/bold red] Caminho '{path}' não encontrado.")
        raise typer.Exit()

    console.print(f"[bold green]Iniciando análise em: {path}[/bold green]")
    
    collector = GitCollector(path, limit_commits=commits)
    hotspots = collector.collect_metrics()
    
    table = Table(title=f"Top Hotspots (Últimos {commits} commits)")
    table.add_column("Arquivo", style="cyan")
    table.add_column("Churn", style="magenta")
    table.add_column("Complexidade (CC)", style="yellow")
    table.add_column("Risk Score", style="bold red")
    table.add_column("Main Author", style="green")

    for h in hotspots:
        main_author = list(h['top_authors'].keys())[0] if h['top_authors'] else "N/A"
        table.add_row(
            h['file'], 
            str(h['churn']), 
            str(h['complexity']), 
            str(h['risk_score']),
            main_author
        )
    
    console.print(table)

    if ai and hotspots:
        console.print("\n[bold purple]🤖 Consultando a IA para diagnóstico...[/bold purple]")
        analyzer = AIAnalyzer()
        report = analyzer.analyze_health(hotspots)
        
        console.print("\n[bold]Relatório de Saúde Evolutiva:[/bold]")
        console.print(report)
        
        with open("HEALTH_REPORT.md", "w") as f:
            f.write(report)
        console.print("\n[dim]Relatório salvo em HEALTH_REPORT.md[/dim]")

if __name__ == "__main__":
    app()