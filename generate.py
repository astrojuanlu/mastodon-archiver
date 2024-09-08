import typing as t
import json
from pathlib import Path
import shutil

from pydantic import BaseModel, AwareDatetime, TypeAdapter
from structlog import get_logger
from jinja2 import FileSystemLoader, Environment

logger = get_logger()

type MediaType = t.Literal["video/mp4", "image/jpeg", "image/png", "audio/mpeg"]
type Type = t.Literal["Announce", "Create"]


class Attachment(BaseModel):
    url: str
    mediaType: MediaType
    name: str | None  # alt text


class Object(BaseModel):
    url: str
    content: str
    attachment: list[Attachment]


class Toot(BaseModel):
    id: str
    type: Type
    actor: str
    published: AwareDatetime
    object: Object | str


def generate_archive(
    input_directory=Path("export"),
    template_dir=Path("templates"),
    static_dir=Path("static"),
    base="https://social.juanlu.space/@astrojuanlu/",
    output_dir=Path("output"),
):
    with (input_directory / "outbox.json").open() as fh:
        contents = json.load(fh)

    toots_adapter = TypeAdapter(list[Toot])
    toots = toots_adapter.validate_python(contents["orderedItems"])

    logger.info("Loaded toots from outbox.json", num_toots=len(toots))

    jinja_env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=True,
    )
    template = jinja_env.get_template("toot.html.j2")

    output_dir.mkdir(exist_ok=True)

    for static_subdir in ("css", "fonts", "img"):
        shutil.copytree(
            static_dir / static_subdir, output_dir / static_subdir, dirs_exist_ok=True
        )

    for toot in toots:
        if toot.type == "Announce":
            logger.debug("Skipping", toot=toot)
            continue

        output_path = output_directory / toot.object.url.removeprefix(base)
        with output_path.with_suffix(".html").open("w") as fh:
            fh.write(template.render(toot=toot))


if __name__ == "__main__":
    generate_archive()
