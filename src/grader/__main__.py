import typer
from grader._grader import app as grader_app
from grader.bulk_grader import app as bulk_grader_app

app = typer.Typer(help="ITI 1121 Grading CLI Tools")
app.add_typer(grader_app, name="grade", help="Grade a single submission")
app.add_typer(bulk_grader_app, name="bulk", help="Bulk grade multiple submissions")

if __name__ == "__main__":
    app()
