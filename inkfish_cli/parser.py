from dataclasses import dataclass
import json
import re
from pathlib import Path

from inkfish_cli.constants import METAFILE

COMMENT_PATTERN = r"\/\/ ([-]?\d+)pts: (.*)"

@dataclass
class Comment:
    path: Path
    line: int
    text: str
    points: str

def find_comments(file_path: Path):
    with open(file_path) as f:
        comments = []
        try:
            no_prev_comments = 0
            for line_no, line in enumerate(f.readlines()):
              match = re.search(COMMENT_PATTERN, str(line))
              if match:
                  points, text = match.groups()
                  line_no -= no_prev_comments
                  # Account for grading comments in the line number

                  comments.append(Comment(path=file_path, line=line_no, text=text, points=points))
                  no_prev_comments += 1
        except UnicodeDecodeError:
            print(f"WARNING: could not decode {file_path}")
        return comments

def find_all_comments(submission_path: Path):
    # Nothing prevents posting comments on files that aren't part of the OG submission on the inkfish backend,
    # so we're checking it here
    with open(submission_path / METAFILE) as f:
        project_files = [submission_path / Path(file) for file in json.load(f)["files"]]
    return [comment for file in project_files if file.is_file() for comment in find_comments(file)]

