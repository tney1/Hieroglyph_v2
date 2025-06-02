#! /usr/bin/env python3.11
from base64 import b64encode
from argparse import ArgumentParser
from pathlib import Path
from json import dump
from io import BytesIO
import pdf2image


def dump_file(content, name, output):
    with open(output, 'w+') as outputfile:
        dump({
            "name": name,
            "src_lang": "chinese",
            "dst_lang": "english",
            "b64data": content,
            "metadata": {"source_document": name}
        }, outputfile, indent=2)


parser = ArgumentParser(__file__)
parser.add_argument("-i", "--input", type=Path, required=True, help="Input file(s) to b64ify")
parser.add_argument("-o", "--output", type=Path, required=False, help="Output directory for b64 json")
args = parser.parse_args()
if args.input.suffix == '.pdf':
    input_files = []
    for page_index, page_pillow in enumerate(pdf2image.convert_from_path(args.input, dpi=300), start=1):
        buffer = BytesIO()
        page_pillow.save(buffer, format='JPEG', quality=95, subsampling=0)
        input_files.append((f"{args.input.with_suffix('')}.{page_index}.jpeg",
                            b64encode(buffer.getvalue()).decode('utf-8')))

elif '*' in str(args.input) and '*' not in str(args.parent):
    print(f"Wildcard detected in {args.input}")
    input_files = [(str(filepath), b64encode(open(filepath, 'rb').read()).decode('utf-8')) for filepath in args.input.parent.glob(args.input.name)]
else:
    input_files = [(str(args.input), b64encode(open(args.input, 'rb').read()).decode('utf-8'))]

print(f"Start processing {len(input_files)} -> {args.output}")
for filename, input_content in input_files:
    output = args.output / Path(filename).with_suffix('.json').name if args.output else Path(filename).with_suffix('.json')
    dump_file(input_content, str(output.name), output)
    print(f"\tFinished converting {filename} to {output}")
print(f"Finished processing {args.input}")
