import os
import yaml
from typing import Tuple, Any
from lib.Pub import Pub
import sqlite3


def create_yaml_file() -> None:
    """Creates a YAML file to store the directory paths."""
    data = {
        "LibDir": input("\033[38;5;223m"+"Enter the directory path for the database: "+"\033[0m"),
        "PubSortDir": input("\033[38;5;223m"+"Enter the directory path for sorting publications: "+"\033[0m")
    }
    
    with open("config.yaml", "w") as file:
        yaml.dump(data, file)


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


def print_commands() -> None:
    """Prints the available commands."""
    print("\033[38;5;223m"+"Available commands:"+"\033[0m")
    print("\033[38;5;223m"+"- add: Add publications from the sorting directory"+"\033[0m")
    print("\033[38;5;223m"+"- search: Search for publications by attribute"+"\033[0m")
    print("\033[38;5;223m"+"- display: Display entire database in one table"+"\033[0m")
    print("\033[38;5;223m"+"- bibtex: Create .bib file using entire database"+"\033[0m")
    print("\033[38;5;223m"+"- modify: Modify one of the attributes for a given publication"+"\033[0m")
    print("\033[38;5;223m"+"- remove: Remove a publication fromt he database"+"\033[0m")
    print("\033[38;5;223m"+"- view: View the .pdf corresponding to a given publication"+"\033[0m")
    print("\033[38;5;223m"+"- exit: Exit the program"+"\033[0m")


def get_command() -> str:
    """
    Prompts the user to enter a command.

    Returns:
        str: The command entered by the user.
    """
    return input("\033[38;5;223m"+"Enter a command: "+"\033[0m").strip().lower()


def handle_view_command(pub: Pub, pub_id: int) -> None:
    """
    Handles the 'view' command.

    Args:
        pub (Pub): The Pub object for interacting with the publications database.
        pub_id (int): The ID of the publication in the SQLite database.
    """
    pub.open_publication_pdf(pub_id)


def handle_modify_command(pub: Pub, pub_id: int) -> None:
    """
    Handles the 'modify' command.

    Args:
        pub (Pub): The Pub object for interacting with the publications database.
        pub_id (int): The ID of the publication in the SQLite database.
    """
    pub.modify_publication_attribute(pub_id)


def handle_add_command(pub: Pub) -> None:
    """
    Handles the 'add' command.

    Args:
        pub (Pub): The Pub object for interacting with the publications database.
    """
    pub_sort_dir = load_directory_paths()[1]
    pub.add_publications_from_folder(pub_sort_dir)
    print("\033[38;5;223m"+"Publications added successfully."+"\033[0m")


def handle_search_command(pub: Pub) -> None:
    """
    Handles the 'search' command.

    Args:
        pub (Pub): The Pub object for interacting with the publications database.
    """
    attributes = pub.get_distinct_attributes()
    
    # Inform the user about the available attributes
    conn = sqlite3.connect(pub.db_path)
    c = conn.cursor()
    c.execute("SELECT * FROM publications LIMIT 1")
    available_attributes = [desc[0] for desc in c.description[1:-1]]
    print("\033[38;5;223m"+"Available attributes for modification:"+"\033[0m")
    for i, attr in enumerate(available_attributes):
        print("\033[38;5;223m"+f"{i + 1}. {attr}"+"\033[0m")

    # Ask the user to select an attribute to modify
    choice = int(input("\033[38;5;223m"+"Enter the number corresponding to "+\
                       "the attribute you want to search by: "+"\033[0m"))
    attribute = available_attributes[choice-1]
    if 'c' in locals(): c.close()  # Close the cursor if it exists
    conn.close()

    value = input("\033[38;5;223m"+"Enter the value to search for in "+\
                  f"{attribute}: "+"\033[0m")  # Prompt for the value as well

    if attribute in ["cited_in_paper", "inspired_project", "own_paper"]:
        value = value.lower() == 'true'  # Convert to boolean if it's one of the boolean attributes

    publications = pub.search_publications_by_attribute(attribute, value)
    pub.display_publications_table(publications)

    user_choice = input("\033[38;5;223m"+"What would you like to do next? (bibtex/view/search/"+\
                        "exit to main menu): "+"\033[0m").strip().lower()
    
    if user_choice == "bibtex" or user_choice == 'b':
        filename = input("\033[38;5;223m"+"Enter the filename for the BibTeX "+\
                         "file (not including .bib): "+"\033[0m")
        pub.generate_bibtex_file(filename, publications)
        print("\033[38;5;223m"+"Note that .bib files are places in the bibfiles/ sub-directory in the database directory."+"\033[0m")
    elif user_choice == "view" or user_choice == 'v':
        publication_id = int(input("\033[38;5;223m"+"Enter the publication ID "+\
                                   "to view: "+"\033[0m"))
        pub.open_publication_pdf(publication_id)
    elif user_choice == "search" or user_choice == 's':
        handle_search_command(pub)


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


def main() -> None:
    """The main function to run the script."""
    lib_dir, _ = load_directory_paths()
    pub = Pub(lib_dir)
    fancy_welcome_message()

    while True:
        print_commands()
        command = get_command()

        if command == "add" or command == "a":
            handle_add_command(pub)
        elif command == "search" or command == "s":
            handle_search_command(pub)
        elif command == "view" or command == "v":
            pub_id = int(input("\033[38;5;223m"+"Enter the publication ID:"+"\033[0m"))
            handle_view_command(pub, pub_id)
        elif command == "modify" or command == "m":
            pub_id = int(input("\033[38;5;223m"+"Enter the publication ID:"+"\033[0m"))
            handle_modify_command(pub, pub_id)
        elif command == "remove" or command == "r":
            pub_id = int(input("\033[38;5;223m"+"Enter the publication ID:"+"\033[0m"))
            pub.delete_publication_by_id(pub_id)
        elif command == "bibtex" or command == "b":
            filename = input("\033[38;5;223m"+"Enter the file name (without the .bib):"+"\033[0m")
            pub.generate_bibtex_file_database(filename)
            print("\033[38;5;223m"+"Note that .bib files are places in the bibfiles/ sub-directory in the database directory."+"\033[0m")
        elif command == "display" or command == "d":
            pub.display_entire_database()
        elif command == "exit" or command == "e":
            break
        else:
            print("\033[38;5;223m"+"Invalid command. Please try again."+"\033[0m")
    
    print("\033[38;5;223m"+"Exiting the program."+"\033[0m")


if __name__ == "__main__":
    main()