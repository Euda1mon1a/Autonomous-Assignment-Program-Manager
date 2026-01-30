"""CLI commands for privacy and data anonymization operations."""

import json
from pathlib import Path

import typer

app = typer.Typer(help="Privacy and data anonymization commands")


@app.command()
def detect_pii(
    text: str = typer.Argument(..., help="Text to scan for PII"),
    enable_names: bool = typer.Option(
        False, "--names", "-n", help="Enable name detection"
    ),
) -> None:
    """
    Detect PII in provided text.

    Scans text for personally identifiable information including:
    - Email addresses
    - Phone numbers
    - SSN
    - IP addresses
    - Credit cards
    """
    from app.privacy.detectors import PIIDetector

    detector = PIIDetector(enable_name_detection=enable_names)
    matches = detector.detect_all(text)

    if not matches:
        typer.echo(typer.style("No PII detected!", fg=typer.colors.GREEN))
        return

    typer.echo(f"\nFound {len(matches)} PII match(es):\n")

    for match in matches:
        color = {
            "ssn": typer.colors.RED,
            "credit_card": typer.colors.RED,
            "email": typer.colors.YELLOW,
            "phone": typer.colors.YELLOW,
        }.get(match.type.value, typer.colors.CYAN)

        typer.echo(
            f"  [{typer.style(match.type.value.upper(), fg=color)}] "
            f"{match.value} (pos: {match.start}-{match.end})"
        )


@app.command()
def scan_file(
    file_path: str = typer.Argument(..., help="Path to file to scan"),
    output: str = typer.Option(
        "table", "--output", "-o", help="Output format: table, json"
    ),
) -> None:
    """
    Scan a file for PII.

    Supports text files and JSON files.
    """
    from app.privacy.detectors import PIIDetector

    path = Path(file_path)

    if not path.exists():
        typer.echo(f"Error: File not found: {file_path}", err=True)
        raise typer.Exit(1)

    detector = PIIDetector()

    # Read file
    with open(path) as f:
        content = f.read()

        # Try to parse as JSON
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            pii_detected = detector.detect_in_dict(data)

            if not pii_detected:
                typer.echo(
                    typer.style("No PII detected in file!", fg=typer.colors.GREEN)
                )
                return

            typer.echo(f"\nPII detected in {len(pii_detected)} field(s):\n")

            for field, matches in pii_detected.items():
                typer.echo(f"  Field: {field}")
                for match in matches:
                    typer.echo(f"    - {match.type.value}: {match.value}")

            return

    except json.JSONDecodeError:
        # Not JSON, treat as plain text
        pass

        # Scan as plain text
    matches = detector.detect_all(content)

    if not matches:
        typer.echo(typer.style("No PII detected in file!", fg=typer.colors.GREEN))
        return

    typer.echo(f"\nFound {len(matches)} PII match(es) in file:\n")

    for match in matches:
        typer.echo(f"  {match.type.value}: {match.value}")


@app.command()
def mask_text(
    text: str = typer.Argument(..., help="Text to mask"),
    pii_type: str = typer.Option(
        "email", "--type", "-t", help="PII type: email, phone, ssn, name"
    ),
    strategy: str = typer.Option(
        "partial", "--strategy", "-s", help="Masking strategy"
    ),
) -> None:
    """
    Mask PII in text.

    Examples:
        privacy mask-text "john@example.com" --type email --strategy partial
        privacy mask-text "555-123-4567" --type phone
    """
    from app.privacy.maskers import MaskerFactory

    factory = MaskerFactory()
    masker = factory.get_masker(pii_type)

    masked = masker.mask(text)

    typer.echo(f"\nOriginal: {text}")
    typer.echo(f"Masked:   {typer.style(masked, fg=typer.colors.CYAN)}\n")


@app.command()
def anonymize_json(
    input_file: str = typer.Argument(..., help="Input JSON file"),
    output_file: str = typer.Argument(..., help="Output JSON file"),
    fields: str = typer.Option(
        None, "--fields", "-f", help="Comma-separated fields to anonymize"
    ),
    method: str = typer.Option(
        "mask", "--method", "-m", help="Method: mask, pseudonymize, generalize"
    ),
    k_value: int = typer.Option(5, "--k", help="K value for k-anonymity"),
    detect_auto: bool = typer.Option(
        True, "--auto-detect/--no-auto-detect", help="Auto-detect PII"
    ),
) -> None:
    """
    Anonymize data in JSON file.

    Reads JSON file, applies anonymization, and writes to output file.
    """
    from app.privacy import AnonymizationConfig, AnonymizationMethod, DataAnonymizer

    # Read input file
    input_path = Path(input_file)
    if not input_path.exists():
        typer.echo(f"Error: Input file not found: {input_file}", err=True)
        raise typer.Exit(1)

    with open(input_path) as f:
        data = json.load(f)

        # Prepare config
    field_list = fields.split(",") if fields else None

    try:
        method_enum = AnonymizationMethod(method)
    except ValueError:
        typer.echo(f"Error: Invalid method '{method}'", err=True)
        raise typer.Exit(1)

    config = AnonymizationConfig(
        method=method_enum,
        fields=field_list,
        detect_pii=detect_auto,
        k_value=k_value,
    )

    # Anonymize
    anonymizer = DataAnonymizer()

    if isinstance(data, list):
        result = anonymizer.anonymize_batch(data, config)
    else:
        result = anonymizer.anonymize_record(data, config)

    if not result.success:
        typer.echo(f"Error during anonymization: {result.errors}", err=True)
        raise typer.Exit(1)

        # Write output
    output_path = Path(output_file)
    with open(output_path, "w") as f:
        json.dump(result.anonymized_data, f, indent=2, default=str)

    typer.echo(
        f"\n{typer.style('Success!', fg=typer.colors.GREEN)} "
        f"Anonymized {result.anonymized_count} record(s)"
    )

    if result.pii_detected:
        typer.echo(f"\nPII detected in fields: {', '.join(result.pii_detected.keys())}")

    typer.echo(f"Output written to: {output_file}\n")


@app.command()
def test_k_anonymity(
    k_value: int = typer.Option(5, "--k", help="K value"),
    sample_size: int = typer.Option(
        100, "--size", "-s", help="Number of sample records"
    ),
) -> None:
    """
    Test k-anonymity with sample data.

    Generates sample records and applies k-anonymity transformation.
    """
    # Generate sample data
    import random

    from app.privacy import AnonymizationConfig, AnonymizationMethod, DataAnonymizer

    ages = [random.randint(20, 70) for _ in range(sample_size)]
    zipcodes = [f"{random.randint(10000, 99999)}" for _ in range(sample_size)]

    records = [
        {
            "id": i,
            "age": ages[i],
            "zipcode": zipcodes[i],
            "diagnosis": random.choice(["A", "B", "C", "D"]),
        }
        for i in range(sample_size)
    ]

    typer.echo(f"Generated {sample_size} sample records\n")

    # Apply k-anonymity
    config = AnonymizationConfig(
        method=AnonymizationMethod.K_ANONYMITY,
        k_value=k_value,
        quasi_identifiers=["age", "zipcode"],
        sensitive_attributes=["diagnosis"],
    )

    anonymizer = DataAnonymizer()
    result = anonymizer.anonymize_batch(records, config)

    if not result.success:
        typer.echo(f"Error: {result.errors}", err=True)
        raise typer.Exit(1)

    typer.echo(
        f"{typer.style('K-anonymity applied!', fg=typer.colors.GREEN)} (k={k_value})\n"
    )
    typer.echo(f"Original records: {result.original_count}")
    typer.echo(f"Anonymized records: {result.anonymized_count}")
    typer.echo(f"Suppressed: {result.original_count - result.anonymized_count}\n")

    # Show sample
    typer.echo("Sample anonymized records:")
    for record in result.anonymized_data[:5]:
        typer.echo(f"  {record}")


@app.command()
def audit_history(
    limit: int = typer.Option(20, "--limit", "-l", help="Number of entries to show"),
    method: str = typer.Option(None, "--method", "-m", help="Filter by method"),
) -> None:
    """
    Show anonymization audit history.

    Displays recent anonymization operations from audit trail.
    """
    from app.db.session import SessionLocal
    from app.privacy import DataAnonymizer

    db = SessionLocal()
    try:
        anonymizer = DataAnonymizer(db=db)
        history = anonymizer.get_audit_history(limit=limit, method=method)

        if not history:
            typer.echo("No audit history found.")
            return

        typer.echo(f"\nAnonymization Audit History ({len(history)} entries):\n")

        for entry in history:
            timestamp_str = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            reversible = "Yes" if entry.reversible == "true" else "No"

            typer.echo(f"  [{timestamp_str}] {entry.method}")
            typer.echo(f"    Records: {entry.record_count}")
            typer.echo(f"    Reversible: {reversible}")
            typer.echo(f"    ID: {entry.id}\n")

    finally:
        db.close()


@app.command()
def benchmark(
    record_count: int = typer.Option(
        1000, "--count", "-c", help="Number of records to benchmark"
    ),
    method: str = typer.Option("mask", "--method", "-m", help="Anonymization method"),
) -> None:
    """
    Benchmark anonymization performance.

    Tests anonymization speed with specified number of records.
    """
    import time

    from app.privacy import AnonymizationConfig, AnonymizationMethod, DataAnonymizer

    # Generate test data
    records = [
        {
            "id": i,
            "name": f"Person {i}",
            "email": f"person{i}@example.com",
            "phone": f"555-{i:04d}",
            "age": 20 + (i % 50),
        }
        for i in range(record_count)
    ]

    typer.echo(f"\nBenchmarking {method} with {record_count} records...\n")

    # Benchmark
    try:
        method_enum = AnonymizationMethod(method)
    except ValueError:
        typer.echo(f"Error: Invalid method '{method}'", err=True)
        raise typer.Exit(1)

    config = AnonymizationConfig(
        method=method_enum,
        fields=["email", "phone"],
        audit_trail=False,  # Disable for benchmarking
    )

    anonymizer = DataAnonymizer()

    start_time = time.time()
    result = anonymizer.anonymize_batch(records, config)
    elapsed_time = time.time() - start_time

    if not result.success:
        typer.echo(f"Error: {result.errors}", err=True)
        raise typer.Exit(1)

        # Display results
    records_per_sec = record_count / elapsed_time

    typer.echo(f"{typer.style('Benchmark Complete', fg=typer.colors.GREEN)}\n")
    typer.echo(f"Records processed: {result.anonymized_count}")
    typer.echo(f"Time elapsed: {elapsed_time:.3f} seconds")
    typer.echo(f"Throughput: {records_per_sec:.0f} records/second\n")


@app.command()
def generate_key() -> None:
    """
    Generate encryption key for pseudonymization.

    Generates a Fernet encryption key suitable for reversible pseudonymization.
    """
    from cryptography.fernet import Fernet

    key = Fernet.generate_key()

    typer.echo("\nGenerated encryption key:\n")
    typer.echo(f"  {typer.style(key.decode(), fg=typer.colors.CYAN)}\n")
    typer.echo("Store this key securely! It's needed to reverse pseudonymization.\n")
    typer.echo("Usage in config:")
    typer.echo("  config = AnonymizationConfig(")
    typer.echo("      method='pseudonymize',")
    typer.echo(f"      encryption_key='{key.decode()}'")
    typer.echo("  )\n")


if __name__ == "__main__":
    app()
