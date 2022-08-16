import os
import argparse
import shutil
from pathlib import Path
from typing import List
from rocrate.rocrate import ROCrate
from rocrate.model.person import Person
from notebook_embedder import embed_notebook_metadata
from metadata import extract_default_authors, extract_notebook_metadata, AuthorInfo

NOTEBOOK_EXTENSION = ".ipynb"
DESCRIPTION = """
Embeds rocrate data within every jupyter notebook in the directory, and then
creates a parent rocrate in the same directory.
"""
DEFAULT_CRATE_NAME = "ro-crate-metadata.json"
METADATA_KEY = "ro-crate"
TEMP_DIR = "/tmp/crate_hole"


def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("dir", type=Path, help="The directory to act on")
    parser.add_argument(
        "metadata",
        type=Path,
        help="An metadata.json file containing some defaults for author information",
    )
    args = parser.parse_args()

    notebooks = get_notebooks(args.dir)
    for notebook in notebooks:
        update_notebook_metadata(notebook, args.metadata)

    create_root_crate(args.dir, notebooks, args.metadata)


def get_notebooks(dir: Path) -> List[Path]:
    """Returns a list of paths to jupyter notebooks in the given directory

    Parameters:
        dir: The path to the directory in which to search.

    Returns:
        Paths of the notebooks found in the directory
    """
    files = [Path(file) for file in os.listdir(dir)]
    is_notebook = lambda file: file.suffix == NOTEBOOK_EXTENSION
    return list(filter(is_notebook, files))


def update_notebook_metadata(notebook: Path, metadata: Path) -> None:
    """Creates and embeds an rocrate in the metadata of a jupyter notebooks

    Parameters:
        notebook: The path of a jupyter notebook
        metadata: A metadata file containing author information

    """
    crate = generate_notebook_crate(notebook, metadata)
    crate_file = create_temporary_crate_file(crate)
    with open(crate_file) as in_file:
        data = in_file.read()
    embed_notebook_metadata(notebook, METADATA_KEY, data)
    clean_up()


def generate_notebook_crate(notebook: Path, metadata: Path) -> ROCrate:
    """Creates and returns an rocrate for a given notebook.

    Parameters:
        notebook: The notebook to add to the rocrate
        metadata: A path to a file containing some default information to be
            used in adding the rocrate.

    Returns:
        An rocrate object containing information about the notebook.
    """
    crate = ROCrate()
    add_notebook(crate, notebook, metadata)
    return crate


def add_notebook(crate: ROCrate, notebook: Path, metadata: Path) -> None:
    """Adds notebook information to an ROCRate.

    Parameters:
        crate: The rocrate to update.
        notebook: The notebook to add to the rocrate
        metadata: A path to a file containing some default information to be
            used in adding the rocrate.
    """
    default_authors = extract_default_authors(metadata)
    notebook_metadata = extract_notebook_metadata(
        notebook,
        {"title": notebook.name, "creators": default_authors, "description": ""},
    )

    # Add the notebook to the crate
    properties = {
        "name": notebook_metadata["title"],
        "description": notebook_metadata["description"],
        "encodingFormat": "application/x-ipynb+json",
    }
    file = crate.add_file(notebook, properties=properties)

    # Generate and add the authors to the crate
    authors = create_people(crate, notebook_metadata["creators"])
    crate.add(*authors)
    file["author"] = authors


def create_people(crate: ROCrate, authors: List[AuthorInfo]) -> List[Person]:
    """Converts a list of authors to a list of Persons to be embedded within an ROCrate

    Parameters:
        crate: The rocrate in which the authors will be created.
        authors: A list of author information.

    Returns:
        A list of Persons.
    """
    return [
        Person(crate, author["orcid"], {"name": author["name"]}) for author in authors
    ]


def create_root_crate(output_dir: Path, notebooks: List[Path], metadata: Path) -> None:
    """Creates a parent crate in the supplied directory, linking together the
    info from its children crates.

    Parameters:
        notebooks: The notebooks to include in the crate
        output_dir: The path to the directory in which to create the
                ro-crate-metadata.json file.
        metadata: A path to a metadata.json file
    """
    result = ROCrate()
    for notebook in notebooks:
        add_notebook(result, notebook, metadata)

    # Create and copy across ro-crate-metadata.json file
    crate_file = create_temporary_crate_file(result)
    shutil.copyfile(crate_file, output_dir.joinpath(crate_file.name))
    clean_up()


def create_temporary_crate_file(crate: ROCrate) -> Path:
    """Writes an rocrate to a temporary directory, and returns the Path to the
    generated file.

    Parameters:
        crate: The rocrate to write.

    Returns:
        The path of the crate within the temporary directory.
    """
    temp_dir = Path(TEMP_DIR)
    temp_dir.mkdir(parents=True, exist_ok=True)

    crate.write(temp_dir)
    return temp_dir.joinpath(DEFAULT_CRATE_NAME)


def clean_up() -> None:
    """Deletes the temporary directory"""
    shutil.rmtree(TEMP_DIR)


if __name__ == "__main__":
    main()
