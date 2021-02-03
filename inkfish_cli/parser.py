from dataclasses import dataclass
import re

from pathlib import Path

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
            for idx, line in enumerate(f.readlines()):
              match = re.search(COMMENT_PATTERN, str(line))
              if match:
                  points, text = match.groups()
                  comments.append(Comment(path=file_path, line=idx, text=text, points=points))
        except UnicodeDecodeError:
            print(f"WARNING: could not decode {file_path}")
        return comments

def find_all_comments(submission_path: Path):
    return [comment for file in submission_path.rglob("*") if file.is_file() for comment in find_comments(file)]

