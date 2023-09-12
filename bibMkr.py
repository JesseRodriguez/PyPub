import os
import yaml
from typing import Tuple, Any
from lib.Pub import Pub


def load_directory_paths() -> Tuple[str, str]:
    """
    Loads the directory paths from the YAML file.

    Returns:
        Tuple[str, str]: The directory paths for the database and sorting publications.
    """
    if not os.path.exists("config.yaml"):
        create_yaml_file()

    with open("config.yaml", "r") as file:
        data = yaml.safe_load(file)

    return data["LibDir"], data["PubSortDir"]


def fancy_welcome_message():
    """
    Prints a fancy welcome message to welcome the user to the Publication Manager.
    Gruvbox color scheme is approximated.
    """
    # Gruvbox Dark Palette (approximation)
    # Dark0  : \033[38;5;235m  (closest to ANSI 0;30m but darker)
    # Dark1  : \033[38;5;237m  (closest to ANSI 0;30m)
    # Light0 : \033[38;5;223m
    # Red    : \033[38;5;167m
    # Green  : \033[38;5;142m
    # Blue   : \033[38;5;109m
    # Reset  : \033[0m

    print("\033[38;5;235m" + "=================================================" + "\033[0m")
    print("\033[38;5;142m" + "Welcome to Jesse Rodriguez's Publication Manager!" + "\033[0m")
    print("\033[38;5;235m" + "=================================================" + "\033[0m")
    print("\033[38;5;109m" + "  Manage your academic publications with ease."    + "\033[0m")
    print("\033[38;5;235m" + "=================================================" + "\033[0m")
    print("\033[38;5;223m" + "  This script helps you quickly create bibtex"    + "\033[0m")
    print("\033[38;5;223m" + "                      records."    + "\033[0m")
    print("\033[38;5;235m" + "=================================================" + "\033[0m")


def main() -> None:
    """The main function to run the script."""
    lib_dir, pub_dir = load_directory_paths()
    pub = Pub(lib_dir)
    fancy_welcome_message()

    print("\033[38;5;223m"+"Looking for .pdfs with no corresponding .bib file..."+"\033[0m")
    for filename in os.listdir(pub_dir):
        if filename.endswith('.pdf'):
            try:
                pdf_path = os.path.join(folder_path, filename)
                bib_path = os.path.join(folder_path, filename[:-4]+'.bib')
                if not os.path.exists(bib_path):
                    print("\033[38;5;223m"+"There is no corresponding .bib file for "\
                            +filename+" in "+folder_path+"."+"\033[0m")
                    entry = input("\033[38;5;223m"+"Do you have the bibtex record on-hand?"+\
                            " (yes/no)"+"\033[0m").strip().lower()
                    if entry == "yes" or entry == "y":
                        bib_content = self.prompt_and_save_bibtex(bib_path)
                        publication = self.prompt_publication_attributes_bib(bib_content)
                    else:
                        print("\033[38;5;223m"+"Let's construct one:\n"+"\033[0m")
                        print("\033[38;5;223m"+"Opening pdf..."+"\033[0m")
                        open_pdf(pdf_path)
                        bib_content = self.prompt_for_bibtex_record()
                        publication = self.prompt_publication_attributes_bib(bib_content)

            except Exception as e:
                print("\033[38;5;223m"+f"An error occurred: {e}"+"\033[0m")
                traceback.print_exc()
    
    print("\033[38;5;223m"+"Done! Exiting the program."+"\033[0m")


if __name__ == "__main__":
    main()
