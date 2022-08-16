import sys
import json
import argparse
from pathlib import Path


def embed_notebook_metadata(notebook: Path, key: str, value: str) -> None:
    """
    Attempts to write a key value pair to the metadata of a given notebook.

    Parameters:
        notebook: The path to the notebook to modify
        key: The metadata key with which to embed the JSON value
        value: A JSON string containing metadata info

    Raises:
        (json.JSONDecodeError) if the supplied value is not valid json.

    """
    with open(notebook.absolute(), "r") as input_file:
        lines = input_file.read()
        data = json.loads(lines)

    data["metadata"][key] = json.loads(value)
    with open(notebook, "w") as output_file:
        output_file.write(json.dumps(data, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="Embed some metadata in a jupyter notebook"
    )
    parser.add_argument("notebook", help="The notebook to act on")
    parser.add_argument("key", type=str, help="The key for the metadata")
    parser.add_argument(
        "value",
        nargs="?",
        help="An optional file containing JSON for a value to embed. Defaults to stdin.",
        type=argparse.FileType("r"),
        default=sys.stdin,
    )
    args = parser.parse_args()
    value = args.value.read()
    args.value.close()
    embed_notebook_metadata(Path(args.notebook), args.key, value)


if __name__ == "__main__":
    main()
