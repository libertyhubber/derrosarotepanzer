#!/usr/bin/env python3

import os
import io
import re
import sys
import json
import hashlib
import pathlib as pl
import itertools as it
import collections
import datetime as dt
from PIL import Image


THUMBNAIL_SIZE = 150


def update_thumbnails():
    for entry_index_path in sorted(pl.Path("images").glob("*/*/entry_index.json")):
        dirpath = entry_index_path.parent
        thumbnails_path = dirpath / "thumbnails.jpg"
        is_thumbnails_fresh = (
            thumbnails_path.exists()
            and thumbnails_path.stat().st_mtime >= entry_index_path.stat().st_mtime
        )
        if is_thumbnails_fresh:
            continue

        with entry_index_path.open('rb') as fobj:
            entry_index = json.loads(fobj.read().decode("utf-8"))

        print("updating thumbnails", thumbnails_path)
        num_cols = 10
        num_rows = len(entry_index) // 10

        padding_x = num_cols * 2
        padding_y = num_rows * 2

        thumbnails_width = THUMBNAIL_SIZE * 10 + padding_x
        thumbnails_height = THUMBNAIL_SIZE * (num_rows + 1) + padding_y

        thumbnails_image = Image.new('RGB', (thumbnails_width, thumbnails_height))
        for i, entry in enumerate(entry_index):
            column = i % 10
            row = i // 10
            padding_x = column * 2
            padding_y = row * 2
            offset_x = padding_x + column * THUMBNAIL_SIZE
            offset_y = padding_y + row * THUMBNAIL_SIZE

            img_path = dirpath / entry['name']
            with Image.open(img_path) as img:
                img.thumbnail((THUMBNAIL_SIZE, THUMBNAIL_SIZE))
                img_width, img_height = img.size
                if img_width > img_height:
                    offset_y += (THUMBNAIL_SIZE - img_height) // 2
                else:
                    offset_x += (THUMBNAIL_SIZE - img_width) // 2

                thumbnails_image.paste(img.copy(), (offset_x, offset_y))

        thumbnails_image.save(str(thumbnails_path), "JPEG", quality=70, optimize=True)


def update_indexes():
    img_by_dir = collections.defaultdict(list)
    for fpath in sorted(pl.Path("images").glob("**/*.jpg")):
        if fpath.name == "thumbnails.jpg":
            continue

        dirpath = str(fpath.parent)[len("images/"):]
        img_by_dir[dirpath].append(fpath)

    dir_index_dicts = {
        dirpath: len(img_paths)
        for dirpath, img_paths in img_by_dir.items()
    }

    dir_index_data = json.dumps(dir_index_dicts, indent=2).encode("utf-8")
    dir_index_path = pl.Path("images") / "dir_index.json"

    is_dir_index_fresh = (
        dir_index_path.exists()
        and dir_index_path.open('rb').read() == dir_index_data
    )
    if not is_dir_index_fresh:
        with dir_index_path.open('wb') as fobj:
            fobj.write(dir_index_data)

    for dirname, img_paths in img_by_dir.items():
        dirpath = pl.Path("images").joinpath(*dirname.split("/"))
        entry_index_path = dirpath / "entry_index.json"

        if entry_index_path.exists():
            with entry_index_path.open('rb') as fobj:
                old_entry_index_data = fobj.read()
                old_entry_index = json.loads(old_entry_index_data.decode("utf-8"))
        else:
            old_entry_index_data = None
            old_entry_index = []

        new_entry_index = []
        old_entries = {entry['name']: entry for entry in old_entry_index}

        for img_path in img_paths:
            if img_path.name in old_entries:
                new_entry_index.append(old_entries[img_path.name])
            else:
                with Image.open(img_path) as img:
                    img_width, img_height = img.size

                new_entry_index.append({
                    'name'  : img_path.name,
                    'width' : img_width,
                    'height': img_height,
                })

        new_entry_index.sort(key=lambda e: e['name'])
        new_entry_index_data = (
            json.dumps(new_entry_index)
                .replace("}, {", "},\n{")
                .encode("utf-8")
        )
        if old_entry_index_data != new_entry_index_data:
            with entry_index_path.open('wb') as fobj:
                fobj.write(new_entry_index_data)


def ingest_uploads():
    uploads = it.chain(
        pl.Path("upload").glob("*.png"),
        pl.Path("upload").glob("*.jpg"),
        pl.Path("upload").glob("*.jpeg"),
        pl.Path("upload").glob("*.webp"),
        pl.Path("images").glob("*.png"),
        pl.Path("images").glob("*.jpg"),
        pl.Path("images").glob("*.jpeg"),
        pl.Path("images").glob("*.webp"),
        pl.Path(".").glob("*.png"),
        pl.Path(".").glob("*.jpg"),
        pl.Path(".").glob("*.jpeg"),
        pl.Path(".").glob("*.webp"),
    )

    for src_fpath in uploads:
        if src_fpath.name.startswith("favico"):
            continue
        basename, suffix = src_fpath.name.rsplit(".", 1)
        assert suffix in ("jpg", "jpeg", "png", "webp"), src_fpath

        if match := re.search(r"20[0-9]{2}-[0-1][0-9]-[0-3][0-9]", src_fpath.name):
            datestr = src_fpath.name[:10]
            tgt_fname = src_fpath.name
        else:
            datestr = dt.datetime.now().isoformat()[:19].replace(":", "")

            with src_fpath.open(mode="rb") as fobj:
                fdata = fobj.read()
                digest = hashlib.sha256(fdata).hexdigest()[:15]
            tgt_fname = datestr + "_" + digest + src_fpath.name

        dirpath = pl.Path("images") / datestr.split("-")[0] / datestr.split("-")[1]
        dirpath.mkdir(parents=True, exist_ok=True)

        tgt_fname = tgt_fname.rsplit(".", 1)[0] + ".jpg"
        tgt_fpath = dirpath / tgt_fname

        print(src_fpath, "->", tgt_fpath, src_fpath.stat().st_mtime)

        if suffix in ("png", "webp"):
            with Image.open(src_fpath) as png_img:
                jpg_img = Image.new('RGB', png_img.size)
                jpg_img.paste(png_img.copy())
                jpg_img.save(tgt_fpath, "JPEG", quality=95, optimize=True)
            src_fpath.unlink()
        else:
            src_fpath.rename(tgt_fpath)


def main(args: list[str]) -> int:
    ingest_uploads()
    update_indexes()
    update_thumbnails()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
