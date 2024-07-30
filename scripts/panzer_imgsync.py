"""
Implements a telegram bot.

Uses the following environment variables:
    PANZER_IMGSYNC_API_ID
    PANZER_IMGSYNC_API_HASH
    PANZER_IMGSYNC_CHANNEL

    PANZER_IMGSYNC_BOT_NAME
    PANZER_IMGSYNC_BOT_TOKEN

The bot downloads recent images from the channel
and write them to the "upload" directory.

The filenames should use the date (in isoformat) as a prefix
and the sha256 hash of the file contents as a suffix.
"""

import os
import sys
import pathlib as pl
import datetime as dt
import telethon
from PIL import Image

# Load environment variables
APP_TITLE = 'panzerimgsync'
API_ID = os.environ.get('PANZER_IMGSYNC_API_ID')
API_HASH = os.environ.get('PANZER_IMGSYNC_API_HASH')
assert API_ID, "missing envvar: PANZER_IMGSYNC_API_ID"
assert API_HASH, "missing envvar: PANZER_IMGSYNC_API_HASH"

# BOT_NAME = os.environ.get('PANZER_IMGSYNC_BOT_NAME', "panzer_imgsync_bot")
# BOT_TOKEN = os.environ.get('PANZER_IMGSYNC_BOT_TOKEN')
# assert BOT_TOKEN, "missing environment variable PANZER_IMGSYNC_BOT_TOKEN"

CHANNEL_NAME = os.environ.get('PANZER_IMGSYNC_CHANNEL', "@RosaroterPanzerBackup")

ROOT_DIR = pl.Path(__file__).parent.parent
UPLOAD_DIR = ROOT_DIR / "upload"

# Create the "upload" directory if it doesn't exist
UPLOAD_DIR.mkdir(exist_ok=True)

client = telethon.TelegramClient(APP_TITLE, API_ID, API_HASH)


async def async_main():
    # Getting information about yourself
    me = await client.get_me()

    print("client id/username:", me.id, me.username, me.phone)

    offset_id = 0
    limit = 200
    async for msg in client.iter_messages(CHANNEL_NAME, offset_id=offset_id, limit=limit):
        if msg.photo is None:
            # Skip if the message has no photo attached
            continue

        if msg.media.__class__.__name__ != 'MessageMediaPhoto':
            continue

        fname_prefix = msg.date.isoformat().replace(":", "")[:17]
        if not (fname_prefix.startswith("2024-07-19") or fname_prefix.startswith("2024-07-20")):
            continue

        if msg.file.mime_type == 'image/jpeg':
            file_ext = "jpg"
        elif msg.file.mime_type == 'image/jpeg':
            file_ext = "png"
        else:
            print("invalid mime type", msg.file.mime_type)
            continue

        fname = fname_prefix + "_" + str(msg.photo.id) + "." + file_ext
        out_fpath = UPLOAD_DIR / fname

        print(">>>", msg.id, msg.file.mime_type, "old" if out_fpath.exists() else "new", out_fpath)
        # print("...", msg.forwards, {res.reaction.emoticon: res.count for res in msg.reactions.results})

        if out_fpath.exists():
            continue

        # download photo to upload directory
        blob = await client.download_media(msg, bytes)
        with out_fpath.open(mode='wb') as fobj:
            fobj.write(blob)

    return


def main(args: list[str]) -> int:
    with client:
        client.loop.run_until_complete(async_main())

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))


