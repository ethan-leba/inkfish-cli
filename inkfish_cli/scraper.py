from typing import List
from typing import NamedTuple
from dataclasses import asdict

from inkfish_cli.parser import Comment
import requests
import tarfile
import os
import re
from bs4 import BeautifulSoup
from pathlib import Path
from tempfile import NamedTemporaryFile

INKFISH_URL = "https://inkfish.ntuck-neu.site/"
INKFISH_PATH = Path("~/inkfish").expanduser()

SUB_ID_FILE = ".inkfish_sub_id"

# def main():
session: requests.Session = requests.Session()

def get_soup(link):
    return BeautifulSoup(session.get(link).text, "html.parser")


csrf_token = (
    get_soup(INKFISH_URL).find("input", attrs={"name": "_csrf_token"}).attrs["value"]
)

resp = session.post(
    "https://inkfish.ntuck-neu.site/session",
    headers={
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "content-type": "application/x-www-form-urlencoded",
        "pragma": "no-cache",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
    },
    data={
        "_csrf_token": csrf_token,
        "login": os.environ["INKFISH_USER"],
        "password": os.environ["INKFISH_PASSWORD"],
    },
)

# XXX: Won't fetch already graded names
def get_grading_names(num):
    html = get_soup(
        f"https://inkfish.ntuck-neu.site/staff/assignments/{num}/grading_tasks"
    )

    tb = html.find("table").tbody

    return [row.find("td").text for row in tb.find_all("tr")]


class AssignmentID(NamedTuple):
    sub_id: str
    grade_id: str


def get_grade_id(sub_id):
    html = get_soup(f"https://inkfish.ntuck-neu.site/staff/subs/{sub_id}")
    edit_grade = html.find("a", text="Edit Grade")

    return edit_grade and edit_grade.attrs["href"].split("/")[-2]


def get_grading_list(num):
    names = get_grading_names(num)
    html = get_soup(f"https://inkfish.ntuck-neu.site/staff/assignments/{num}")
    table_body = html.find("th", text="Student").parent.parent.tbody

    grade_d = {}
    for row in table_body.find_all("tr"):
        name, grade_link, *_, sub_link = row.find_all("td")

        if name.text not in names:
            continue

        sub_id = sub_link.find("a").attrs["href"].split("/")[-1]
        grade_d[name.text] = sub_id

    return grade_d


def download_all(num):
    gl = get_grading_list(num)

    for name, sub in gl.items():
        try:
            download_sub(name, sub)
        except:
            print(f"WARNING: {name} download failed")


def download_sub(name, id: str):
    r3 = get_soup(f"https://inkfish.ntuck-neu.site/staff/subs/{id}")

    dl_link = next(
        link.attrs["href"]
        for link in r3.find_all("a")
        if link.attrs["href"].startswith("/uploads")
    )

    gimme = session.get(f"{INKFISH_URL}/{dl_link}")

    INKFISH_PATH.mkdir(exist_ok=True)
    sub_path = INKFISH_PATH / name.replace(" ", "-").lower()
    tar_path = sub_path.with_suffix(".tar.gz")
    sub_path.mkdir()

    with open(tar_path, mode="wb") as tf:
        for chunk in gimme.iter_content(chunk_size=128):
            tf.write(chunk)

    with tarfile.open(tar_path) as tar:
        tar.extractall(path=sub_path)

    with open(sub_path / SUB_ID_FILE, mode="w") as f:
        f.write(id)

    tar_path.unlink()


def save_to_file(filename, resp):
    with open(filename, "wb") as fd:
        for chunk in resp.iter_content(chunk_size=128):
            fd.write(chunk)


def post_comments(project_root: Path, comments: List[Comment]):
    with open(project_root / SUB_ID_FILE) as f:
        sub_id = f.read()

    grade_id = get_grade_id(sub_id)
    if not grade_id:
        session.post(f"{INKFISH_URL}staff/subs/{sub_id}/grades").raise_for_status()

    grade_id = int(get_grade_id(sub_id))

    edit_html = get_soup(f"https://inkfish.ntuck-neu.site/staff/grades/{grade_id}/edit")

    csrf = re.search(
        r"window\.csrf_token = \"(.*?)\"", edit_html.find("script").string
    ).group(1)

    for comment in comments:
        json_body = asdict(comment)
        json_body["grade_id"] = grade_id
        json_body["path"] = str(comment.path.relative_to(project_root))

        headers = {
            "Connection": "keep-alive",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "accept": "application/json",
            "x-csrf-token": csrf,
            "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Mobile Safari/537.36",
            "content-type": "application/json; charset=UTF-8",
            "Origin": "https://inkfish.ntuck-neu.site",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://inkfish.ntuck-neu.site/staff/grades/5792/edit",
            "Accept-Language": "en-US,en;q=0.9",
        }

        response = requests.post(
            "https://inkfish.ntuck-neu.site/ajax/staff/grades/5792/line_comments",
            headers=headers,
            cookies=session.cookies,
            json={"line_comment": json_body},
        )
        if response.status_code != 201:
            print("warning: ", resp.text)
    print(f"save applied comments at: https://inkfish.ntuck-neu.site/ajax/staff/grades/{grade_id}/edit")


# post a line comment
# https://inkfish.ntuck-neu.site/ajax/staff/grades/5771/line_comments
# {line_comment: {grade_id: 5771, path: "hw02-starter/Makefile", line: 1, text: "", points: "0"}}
