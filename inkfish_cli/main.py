from typing import Optional

from inkfish_cli import scraper
from inkfish_cli import parser

from pathlib import Path

import typer

app = typer.Typer()


@app.command()
def download(assignment_id: int):
    """Download all assigned submissions for the given assignment ID"""
    typer.echo(f"Downloading assigned submissions for assignment no. {assignment_id}")
    scraper.download_all(assignment_id)

@app.command()
def grade(submission_path: Path, dry_run: bool = False):
    """Submit grading comments for the given submission"""
    comments = parser.find_all_comments(submission_path)

    if dry_run:
        print(comments)
    else:
        scraper.post_comments(submission_path, comments)
