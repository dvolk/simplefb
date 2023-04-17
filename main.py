import datetime
import os
import pathlib
import shlex
import time

import flask
import humanize
import werkzeug

app = flask.Flask(__name__)
app.secret_key = b"secret"


def icon(text):
    """
    Return html for fontawesome icon - solid variant.
    """
    return f'<i class="fas fa-fw fa-{ text }"></i>'


def icon_regular(text):
    """
    Return html for fontawesome icon - regular variant.
    """
    return f'<i class="far fa-fw fa-{ text }"></i>'


@app.route("/")
def browse():
    """Browse files page."""

    # get query params
    browse_dir = flask.request.args.get("browse_dir", ".")
    sort_by = flask.request.args.get("sort_by", "r_mtime")

    # get some data
    browse_dir = pathlib.Path(browse_dir)
    files = browse_dir.iterdir()
    files = [
        f for f in files if (f.is_file() or f.is_dir()) and not f.name.startswith(".")
    ]
    epoch_time_now = int(time.time())

    # sort files
    if sort_by == "name":
        files = sorted(files, key=lambda x: x.name)
    if sort_by == "r_name":
        files = sorted(files, key=lambda x: x.name, reverse=True)
    if sort_by == "mtime":
        files = sorted(files, key=lambda x: x.stat().st_mtime)
    if sort_by == "r_mtime":
        files = sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)
    if sort_by == "size":
        files = sorted(files, key=lambda x: x.stat().st_size)
    if sort_by == "r_size":
        files = sorted(files, key=lambda x: x.stat().st_size, reverse=True)

    # directories first
    files = sorted(files, key=lambda x: x.is_dir(), reverse=True)

    return flask.render_template(
        "browse.jinja2",
        browse_dir=browse_dir,
        files=files,
        sort_by=sort_by,
        humanize=humanize,
        epoch_time_now=epoch_time_now,
        icon=icon,
        icon_regular=icon_regular,
    )


@app.route("/zip", methods=["POST"])
def zip():
    files = flask.request.form.getlist("selfile")
    browse_dir = flask.request.form.get("browse_dir", ".")

    if not files:
        flask.flash("No files selected for archiving.")
        return flask.redirect(flask.url_for("browse", browse_dir=browse_dir))

    datetime_now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    files_fmt = " ".join([shlex.quote(pathlib.Path(f).name) for f in files])
    archive_file = f"archive-{datetime_now}.tar.gz"

    cmd = f"cd {shlex.quote(browse_dir)}; tar czf {archive_file} {files_fmt} &"
    print(cmd)
    os.system(cmd)

    flask.flash("Archiving selected files.")
    return flask.redirect(flask.url_for("browse", browse_dir=browse_dir))


@app.route("/download")
def download():
    file = flask.request.args.get("file")

    return flask.send_file(file)


@app.route("/upload", methods=["POST"])
def upload():
    print(flask.request)
    print(flask.request.form)
    print(flask.request.files)
    fs = flask.request.files.getlist("files")
    browse_dir = flask.request.form.get("browse_dir", ".")

    for f in fs:
        f.save(pathlib.Path(browse_dir) / werkzeug.utils.secure_filename(f.filename))

    flask.flash("File uploaded successfully")
    return flask.redirect(flask.url_for("browse", browse_dir=browse_dir))


@app.route("/delete", methods=["POST"])
def delete():
    files = flask.request.form.getlist("selfile")
    browse_dir = flask.request.form.get("browse_dir")

    if not files:
        flask.flash("No files selected for deletion.")
        return flask.redirect(flask.url_for("browse", browse_dir=browse_dir))

    files_fmt = " ".join([shlex.quote(pathlib.Path(f).name) for f in files])
    cmd = f"cd {shlex.quote(browse_dir)}; rm -rf {files_fmt} &"
    print(cmd)
    os.system(cmd)

    flask.flash("Deleting selected files.")
    return flask.redirect(flask.url_for("browse", browse_dir=browse_dir))


app.run(debug=True)
