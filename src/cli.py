import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
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
    
    with console.status("[bold green]Minerando histórico (Churn + Complexidade)...[/bold green]"):
        hotspots = collector.collect_metrics()
    
    with console.status("[bold blue]Calculando acoplamento lógico...[/bold blue]"):
        raw_couplings = collector.get_coupling_analysis(min_shared_commits=3)

    coupling_map = {}
    for c in raw_couplings:
        if c['file_a'] not in coupling_map:
            coupling_map[c['file_a']] = f"{c['file_b']} ({c['strength']})"
        
        if c['file_b'] not in coupling_map:
            coupling_map[c['file_b']] = f"{c['file_a']} ({c['strength']})"

    table = Table(title=f"Top Hotspots (Últimos {commits} commits)")
    table.add_column("Arquivo", style="cyan")
    table.add_column("Churn", style="magenta", justify="right")
    table.add_column("Complexidade", style="yellow", justify="right")
    table.add_column("Risk Score", style="bold red", justify="right")
    table.add_column("Main Author", style="green")
    table.add_column("Acoplamento Principal", style="blue")

    for h in hotspots:
        main_author = list(h['top_authors'].keys())[0] if h['top_authors'] else "N/A"
        
        coupling_info = coupling_map.get(h['file'], "-")

        table.add_row(
            h['file'], 
            str(h['churn']), 
            str(h['complexity']), 
            str(h['risk_score']),
            main_author,
            coupling_info
        )
    
    console.print(table)

    if raw_couplings:
        console.print("\n")
        coup_table = Table(title="🔗 Top Acoplamento Lógico (Dependências Ocultas)")
        coup_table.add_column("Arquivo A", style="cyan")
        coup_table.add_column("Arquivo B", style="cyan")
        coup_table.add_column("Co-alterações", justify="center")
        coup_table.add_column("Força", justify="right", style="green")

        for c in raw_couplings[:5]:
            coup_table.add_row(
                c['file_a'],
                c['file_b'],
                str(c['shared_commits']),
                c['strength']
            )
        console.print(coup_table)

    if ai and hotspots:
        console.print("\n[bold purple]Consultando a IA para diagnóstico...[/bold purple]")
        
        analyzer = AIAnalyzer()
        
        context_data = {
            "hotspots": hotspots,
            "logical_coupling": raw_couplings[:5]
        }
        
        report_input = str(context_data) 
        
        report = analyzer.analyze_health(report_input)
        
        console.print(Panel(report, title="Relatório de Saúde Evolutiva", border_style="green"))
        
        with open("HEALTH_REPORT.md", "w", encoding="utf-8", newline="\n") as f:
            f.write(report)
        console.print("\n[dim]Relatório salvo em HEALTH_REPORT.md[/dim]")

if __name__ == "__main__":
    app()