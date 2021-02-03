Inkfish CLI
==========

To use this tool, you'll need to put your Khoury credentials into
environment variables `INKFISH_USER` and `INKFISH_PASSWORD`.

Downloading assignments
=======================
`inkfish download [assignment_id]` will download all ungraded
assignments for the given assignment to the directory `~/inkfish`. The
assignment ID can be found in the URL of the assignment.

Grading assignments
===================

To place a grading comment, leave a comment below the line you're
grading in the following format:

```
// [int]pts: [comment]
```

Once you've completed grading, you can use the command `inkfish grade
[path_to_assignment]`. Firstly, you must click the 'Create' button
before running the command. The comments will be added, but not saved,
so you can look over them before submitting. The flag `--dry-run`
allows you to preview the comments before submitting.
