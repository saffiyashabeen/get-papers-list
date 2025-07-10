import typer
from get_papers_list import pubmed

app = typer.Typer()

@app.command()
def main(
    query: str = typer.Argument(..., help="Search query for PubMed."),
    file: str = typer.Option("pubmed_papers.csv", "-f", "--file", help="Output CSV filename."),
    debug: bool = typer.Option(False, "-d", "--debug", help="Enable debug mode.")
):
    """Fetch PubMed papers with pharma/biotech affiliations and export to CSV."""
    paper_ids = pubmed.fetch_papers(query, debug)
    if not paper_ids:
        typer.echo("No papers found for query.")
        raise typer.Exit()

    paper_details = pubmed.fetch_paper_details(paper_ids, debug)
    processed_papers = [pubmed.detect_non_academic_authors(paper) for paper in paper_details]

    pubmed.export_to_csv(processed_papers, file)
    typer.echo(f"Results exported to {file}")

if __name__ == "__main__":
    app()
