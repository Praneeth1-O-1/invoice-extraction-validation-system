"""
Command-line interface for Invoice QC Service.
Provides extract, validate, and full-run commands.
"""

import json
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .extractor import InvoiceExtractor
from .validator import InvoiceValidator
from .schemas import Invoice, ValidationReport

app = typer.Typer(help="Invoice Quality Control CLI")
console = Console()


@app.command()
def extract(
    pdf_dir: Path = typer.Option(..., "--pdf-dir", help="Directory containing PDF invoices"),
    output: Path = typer.Option("extracted_invoices.json", "--output", help="Output JSON file"),
):
    """
    Extract structured data from invoice PDFs.

    Example:
        python -m invoice_qc extract --pdf-dir pdfs --output invoices.json
    """
    console.print(f"\n[bold blue]📄 Extracting invoices from:[/bold blue] {pdf_dir}")

    if not pdf_dir.exists():
        console.print(f"[bold red]❌ Error:[/bold red] Directory {pdf_dir} does not exist")
        raise typer.Exit(code=1)

    extractor = InvoiceExtractor()
    invoices = extractor.extract_from_directory(pdf_dir)

    if not invoices:
        console.print("[yellow]⚠️  No invoices extracted[/yellow]")
        raise typer.Exit(code=0)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(
        [invoice.model_dump(mode="json") for invoice in invoices],
        indent=2,
        default=str
    ))

    console.print(f"\n[bold green]✓ Extracted {len(invoices)} invoices[/bold green]")
    console.print(f"[dim]Output saved to:[/dim] {output}")

    _print_extraction_summary(invoices)


@app.command()
def validate(
    input_file: Path = typer.Option(..., "--input", help="Input JSON file with extracted invoices"),
    report: Path = typer.Option("validation_report.json", "--report", help="Output validation report file"),
    tolerance: float = typer.Option(0.02, "--tolerance", help="Amount matching tolerance (default: 2%)"),
):
    """
    Validate extracted invoice data.

    Example:
        python -m invoice_qc validate --input invoices.json --report report.json
    """
    console.print(f"\n[bold blue]🔍 Validating invoices from:[/bold blue] {input_file}")

    if not input_file.exists():
        console.print(f"[bold red]❌ Error:[/bold red] File {input_file} does not exist")
        raise typer.Exit(code=1)

    invoices_data = json.loads(input_file.read_text())
    invoices = [Invoice(**data) for data in invoices_data]

    validator = InvoiceValidator(tolerance=tolerance)
    validation_report = validator.validate_batch(invoices)

    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(validation_report.model_dump_json(indent=2))

    _print_validation_results(validation_report)
    console.print(f"\n[dim]Report saved to:[/dim] {report}")

    if validation_report.summary.invalid_invoices > 0:
        raise typer.Exit(code=1)


@app.command("full-run")
def full_run(
    pdf_dir: Path = typer.Option(..., "--pdf-dir", help="Directory containing PDF invoices"),
    report: Path = typer.Option("validation_report.json", "--report", help="Output validation report file"),
    save_extracted: Optional[Path] = typer.Option(None, "--save-extracted", help="Also save extracted JSON"),
    tolerance: float = typer.Option(0.02, "--tolerance", help="Amount matching tolerance"),
):
    """
    Extract and validate invoices in one command (end-to-end).

    Example:
        python -m invoice_qc full-run --pdf-dir pdfs --report report.json
    """
    console.print(f"\n[bold blue]🚀 Running full invoice QC pipeline[/bold blue]")
    console.print(f"[dim]PDF directory:[/dim] {pdf_dir}")

    if not pdf_dir.exists():
        console.print(f"[bold red]❌ Error:[/bold red] Directory {pdf_dir} does not exist")
        raise typer.Exit(code=1)

    # Step 1: Extract
    console.print("\n[bold]Step 1: Extraction[/bold]")
    extractor = InvoiceExtractor()
    invoices = extractor.extract_from_directory(pdf_dir)

    if not invoices:
        console.print("[yellow]⚠️  No invoices extracted[/yellow]")
        raise typer.Exit(code=0)

    console.print(f"[green]✓ Extracted {len(invoices)} invoices[/green]")

    # Optionally save extracted data
    if save_extracted:
        save_extracted.parent.mkdir(parents=True, exist_ok=True)
        save_extracted.write_text(json.dumps(
            [invoice.model_dump(mode="json") for invoice in invoices],
            indent=2,
            default=str
        ))
        console.print(f"[dim]Extracted data saved to:[/dim] {save_extracted}")

    # Step 2: Validate
    console.print("\n[bold]Step 2: Validation[/bold]")
    validator = InvoiceValidator(tolerance=tolerance)
    validation_report = validator.validate_batch(invoices)

    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(validation_report.model_dump_json(indent=2))

    _print_validation_results(validation_report)
    console.print(f"\n[dim]Report saved to:[/dim] {report}")

    if validation_report.summary.invalid_invoices > 0:
        raise typer.Exit(code=1)


def _print_extraction_summary(invoices):
    """Pretty-print a summary table of extracted invoices"""
    table = Table(title="Extracted Invoices", show_header=True, header_style="bold cyan")

    table.add_column("Invoice #", style="cyan")
    table.add_column("Date")
    table.add_column("Seller")
    table.add_column("Buyer")
    table.add_column("Amount", justify="right")
    table.add_column("Currency")

    for invoice in invoices[:10]:
        table.add_row(
            invoice.invoice_number or "N/A",
            str(invoice.invoice_date) if invoice.invoice_date else "N/A",
            (invoice.seller_name[:30] + "...") if invoice.seller_name and len(invoice.seller_name) > 30 else (invoice.seller_name or "N/A"),
            (invoice.buyer_name[:30] + "...") if invoice.buyer_name and len(invoice.buyer_name) > 30 else (invoice.buyer_name or "N/A"),
            str(invoice.gross_total) if invoice.gross_total else "N/A",
            invoice.currency or "N/A"
        )

    if len(invoices) > 10:
        table.add_row("...", "...", "...", "...", "...", "...", style="dim")

    console.print("\n")
    console.print(table)


def _print_validation_results(report: ValidationReport):
    """Pretty-print validation report results"""
    summary = report.summary

    if summary.invalid_invoices == 0:
        status_text = "[bold green]✓ ALL INVOICES VALID[/bold green]"
        status_color = "green"
    else:
        status_text = f"[bold red]✗ {summary.invalid_invoices} INVALID INVOICES[/bold red]"
        status_color = "red"

    summary_text = f"""
{status_text}

Total Invoices:     {summary.total_invoices}
Valid Invoices:     [green]{summary.valid_invoices}[/green]
Invalid Invoices:   [red]{summary.invalid_invoices}[/red]
With Warnings:      [yellow]{summary.invoices_with_warnings}[/yellow]
"""

    console.print("\n")
    console.print(Panel(summary_text, title="Validation Summary", border_style=status_color))

    # Error breakdown
    if summary.error_counts:
        error_table = Table(show_header=True, header_style="bold red")
        error_table.add_column("Error Type", style="red")
        error_table.add_column("Count", justify="right")

        for err, count in sorted(summary.error_counts.items(), key=lambda x: -x[1]):
            error_table.add_row(err, str(count))

        console.print("\n[bold red]Top Errors:[/bold red]")
        console.print(error_table)

    # Warning breakdown
    if summary.warning_counts:
        warning_table = Table(show_header=True, header_style="bold yellow")
        warning_table.add_column("Warning Type", style="yellow")
        warning_table.add_column("Count", justify="right")

        for warn, count in sorted(summary.warning_counts.items(), key=lambda x: -x[1]):
            warning_table.add_row(warn, str(count))

        console.print("\n[bold yellow]Top Warnings:[/bold yellow]")
        console.print(warning_table)


if __name__ == "__main__":
    app()
