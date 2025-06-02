import aiohttp
import asyncio
import time
import glob
import json
import pathlib
import base64
from asyncio import sleep
import argparse
from datetime import timedelta
# https://www.twilio.com/blog/asynchronous-http-requests-in-python-with-aiohttp


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="./assets/documents/**.pdf", type=str)
    parser.add_argument("--output", default=pathlib.Path("./output"), type=pathlib.Path)
    parser.add_argument("--errors", default=pathlib.Path("./errors"), type=pathlib.Path)
    parser.add_argument("--api", default="http://localhost:8088/pipeline", type=str)
    return parser.parse_args()


async def get_data(session: aiohttp.ClientSession, url: str, data: dict) -> dict:
    print(f"Submitting Data: {url} {data['name']}")
    max_retries = 100
    attempt = 0

    while True:
        try:
            async with session.post(url, json=data) as resp:
                print(f"Retrieving session data: {url} {data['name']}")
                return await resp.json()
        
        except (
            aiohttp.ClientOSError,
            aiohttp.ServerDisconnectedError,
        ):
            if attempt < max_retries:
                print(f"Retrying {attempt} for data {data['name']}")
                await sleep(5)
                attempt += 1
            else:
                raise

async def main(args):
    args.output.mkdir(exist_ok=True)
    async with aiohttp.ClientSession() as session:

        tasks = []
        all_files = glob.glob(args.input, recursive=True)
        for file in all_files:
            file_data = base64.b64encode(open(file, 'rb').read()).decode('utf-8')
            print(f"Check file: {file}, type: {type(file_data)}")
            data = {
                "name": str(file),
                "src_lang": "chinese",
                "dst_lang": "english",
                "image_type": "diagram",
                "overlay": "False",
                "b64data": file_data,
                "metadata": {} # Key value pairs of other metadata about the image
            }
            tasks.append(asyncio.ensure_future(get_data(session, args.api, data)))
        if tasks:
            print("About to start waiting for all the data")
        else:
            print(f"error: no files/tasks: {all_files}/{len(tasks)}")
            exit(1)
        for future_data in asyncio.as_completed(tasks):
            try:
                file_data = await future_data
                print(f"File data retrieved: {file_data['name']}")
                base_filename = pathlib.Path(file_data['name']).with_suffix('.json').name
                with open(args.output / base_filename, "w+") as fd:
                    json.dump(file_data, fd)
                print(f"Finished with data for: {file_data['name']}")
            except Exception as e:
                args.errors.mkdir(exist_ok=True)
                base_filename = pathlib.Path(file_data['name']).with_suffix('.json').name
                with open(args.errors / base_filename, "w+") as fd:
                    json.dump(file_data, fd)

if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main(get_arguments()))
    print(f"--- Execution time: {timedelta(seconds=time.time() - start_time)} ---")
