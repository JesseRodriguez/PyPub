import os
import shutil
import sqlite3
import platform
import subprocess
from tabulate import tabulate
from typing import Dict, List, Optional, Union, Tuple
import bibtexparser
import traceback
import time
import textwrap

###############################################################################
### Utility functions
###############################################################################
def open_pdf(pdf_path: str) -> None:
    """
    Opens a PDF file using the default application for the operating system.

    Args:
        pdf_path (str): The path to the PDF file to be opened.
    """
    system_platform = platform.system()

    try:
        if system_platform == "Linux":
            subprocess.run(['xdg-open', pdf_path])
        elif system_platform == "Darwin":  # macOS
            subprocess.run(['open', pdf_path])
        elif system_platform == "Windows":
            subprocess.run(['start', pdf_path], shell=True)
        else:
            print("\033[38;5;223m"+f"Unsupported operating system: {system_platform}"+"\033[0m")

    except FileNotFoundError as e:
        print("\033[38;5;223m"+f"An error occurred: {e}"+"\033[0m")
        traceback.print_exc()


def truncate_entries(rows: List[Tuple], col_index: int, length: int) -> List[Tuple]:
    """
    Truncate entries in a specific column to a certain length.

    Args:
        rows (List[Tuple]): The rows of the table.
        col_index (int): The index of the column to truncate.
        length (int): The maximum length of entries in that column.

    Returns:
        List[Tuple]: A new list of rows with truncated entries in the specified column.
    """
    truncated_rows = []
    for row in rows:
        truncated_entry = row[col_index][:length]
        new_row = tuple(truncated_entry if i == col_index else row[i] for i in range(len(row)))
        truncated_rows.append(new_row)
    return truncated_rows


def wrap_text(text, width):
    """Wrap text for a given width."""
    return '\n'.join(textwrap.wrap(text, width))


###############################################################################
### Class
###############################################################################
class Pub:
    def __init__(self, directory_name: str):
        """
        Initializes a new instance of the Pub class.

        Args:
            directory_name (str): The directory name where the SQLite database 
            will be created.
        """
        self.db_path = os.path.join(directory_name, 'publication.db')
        self.create_database()


    def create_database(self):
        """
        Creates the SQLite database and the 'publications' table if they don't 
        already exist.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS publications
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     title TEXT,
                     first_author_last_name TEXT,
                     principal_investigator_last_name TEXT,
                     field TEXT,
                     date_accessed TEXT,
                     date_published TEXT,
                     cited_in_paper BOOLEAN,
                     want_to_cite BOOLEAN,
                     own_paper BOOLEAN,
                     bibtex TEXT,
                     primary_id INTEGER)''')
        conn.commit()
        if 'c' in locals(): c.close()  # Close the cursor if it exists
        conn.close()


    def add_publication(self, publication: Dict[str, Union[str, bool]]):
        """
        Adds a publication to the database.

        Args:
            publication (Dict): A dictionary containing the publication 
            attributes.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''INSERT INTO publications (title,
                         first_author_last_name,
                         principal_investigator_last_name,
                         field, date_accessed, date_published, cited_in_paper,
                         want_to_cite, own_paper, bibtex, primary_id) VALUES
                         (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (publication['title'], publication['first_author_last_name'],\
                       publication['principal_investigator_last_name'],
                       publication['field'], publication['date_accessed'],\
                       publication['date_published'], publication['cited_in_paper'],\
                       publication['want_to_cite'], publication['own_paper'],\
                       publication['bibtex'], publication['primary_id']))
            conn.commit()
        except sqlite3.Error as e:
            print("\033[38;5;223m"+f"SQLite error: {e}"+"\033[0m")
        finally:
            if 'c' in locals(): c.close()  # Close the cursor if it exists
            conn.close()


    def add_publications_from_folder(self, folder_path: str):
        """
        Adds publications from a folder to the database.

        Args:
            folder_path (str): The path of the folder containing the 
                               publications.
        """
        for filename in os.listdir(folder_path):
            if filename.endswith('.pdf'):
                try:
                    pdf_path = os.path.join(folder_path, filename)
                    bib_path = os.path.join(folder_path, filename[:-4]+'.bib')
                    if os.path.exists(bib_path):
                        with open(bib_path, 'r', encoding='utf-8') as bib_file:
                            bib_content = bib_file.read()
                        publication = self.prompt_publication_attributes_bib(bib_content)
                    else:
                        print("\033[38;5;223m"+"There is no corresponding .bib file for "\
                                +filename+" in "+folder_path+"."+"\033[0m")
                        entry = input("\033[38;5;223m"+"Do you have the bibtex record on-hand?"+\
                                " (yes/no)"+"\033[0m").strip().lower()
                        if entry == "yes":
                            bib_content = self.prompt_and_save_bibtex(bib_path)
                            publication = self.prompt_publication_attributes_bib(bib_content)
                        else:
                            print("\033[38;5;223m"+"Let's construct one:\n"+"\033[0m")
                            print("\033[38;5;223m"+"Opening pdf..."+"\033[0m")
                            open_pdf(pdf_path)
                            bib_content = self.prompt_for_bibtex_record()
                            publication = self.prompt_publication_attributes_bib(bib_content)

                    #Handle multiple fields
                    for i in range(len(publication['field'])):
                        pub = publication
                        pub['field'] = publication['field'][i].strip().lower()
                        if i ==  0:
                            new_filename = self.generate_filename(pub)
                            new_filepath = os.path.join(os.path.dirname(self.db_path),\
                                        new_filename)
                            self.add_publication(pub)
                            os.remove(bib_path)
                            shutil.move(pdf_path, new_filepath)
                        else:
                            self.add_publication(pub)
                    
                except Exception as e:
                    print("\033[38;5;223m"+f"An error occurred: {e}"+"\033[0m")
                    traceback.print_exc()


    def prompt_publication_attributes_bib(self, bib_content: str) -> Dict[str, Union[str, bool]]:
        """
        Prompts the user to enter the attributes for a publication.

        Returns:
            Dict: A dictionary containing the publication attributes.
        """
        bib = bibtexparser.loads(bib_content).entries[0]
        print("\033[38;5;223m"+"Adding publication entitled:\n"+"\033[0m")
        print("\033[38;5;223m"+bib['title']+"\n\n"+"\033[0m")

        publication = {
            'title': bib['title'],
            'first_author_last_name': self.First_Author_bib(bib_content),
            'principal_investigator_last_name': self.Last_Author_bib(bib_content),
            'field': input("\033[38;5;223m"+"Enter the field(s), comma-delimited: "+"\033[0m").split(","),
            'date_accessed': input("\033[38;5;223m"+"Enter the date accessed (MM-YY format): "+"\033[0m").strip(),
            'date_published': input("\033[38;5;223m"+"Enter the date published (MM-YY format): "+"\033[0m").strip(),
            'cited_in_paper': 'False',
            'want_to_cite': 'False',
            'own_paper': 'False',
            'bibtex': bib_content,
            'primary_id': self.get_next_available_id()
        }

        cited = input("\033[38;5;223m"+"Has it been cited in one of your papers? (True/False, "+\
                      "T/F): "+"\033[0m").strip().lower()
        want_cite = input("\033[38;5;223m"+"Has it inspired a new project idea/Do you plan to "+\
                          "cite it? (True/False, T/F): "+"\033[0m").strip().lower()
        own_paper = input("\033[38;5;223m"+"Is it one of your own papers? (True/False, "+\
                               "T/F): "+"\033[0m").strip().lower()
        if cited == "true" or cited == "t":
            publication['cited_in_paper'] = "True"
        if want_cite == "true" or want_cite == "t":
            publication['want_to_cite'] = "True"
        if own_paper == "true" or own_paper == "t":
            publication['own_paper'] = "True"
        
        return publication


    def prompt_publication_attributes(self) -> Dict[str, Union[str, bool]]:
        """
        Prompts the user to enter the attributes for a publication. (DEAD FUNC)

        Returns:
            Dict: A dictionary containing the publication attributes.
        """
        # Consider adding validation here
        publication = {
            'title': input("Enter the paper title: ").strip(),
            'first_author_last_name': input("Enter the first author's last name: ").strip(),
            'principal_investigator_last_name': input("Enter the PI's last name: ").strip(),
            'field': input("Enter the field(s), comma-delimited: ").split(","),
            'date_accessed': input("Enter the date accessed (MM-YY format): ").strip(),
            'date_published': input("Enter the date published (MM-YY format): ").strip(),
            'cited_in_paper': input("Has it been cited in one of your papers? (True/False): ").strip(),
            'want_to_cite': input("Has it inspired a new project idea/Do you plan to cite it? (True/False): ").strip(),
            'own_paper': input("Is it one of your own papers? (True/False): ").strip(),
            'bibtex': input("Enter the full BibTeX citation info: ").strip(),
            'primary_id': self.get_next_available_id()
        }
        return publication


    def generate_filename(self, publication: Dict[str, Union[str, bool]]) -> str:
        """
        Generates a new file name for the publication based on its attributes.

        Args:
            publication (Dict): A dictionary containing the publication attributes.

        Returns:
            str: The new file name for the publication.
        """
        attributes = [
            publication['title'],
            publication['first_author_last_name'],
            publication['principal_investigator_last_name'],
            publication['field'],
            publication['date_accessed'],
            publication['date_published'],
            str(publication['cited_in_paper']),
            str(publication['want_to_cite']),
            str(publication['own_paper'])
        ]
        return '_'.join(attributes) + '.pdf'


    def search_publications_by_attribute(self, attribute: str,\
            value: Union[str, bool]) -> List[Optional[Dict[str, Union[str, bool]]]]:
        """
        Searches for publications by a specified attribute and value.

        Args:
            attribute (str): The attribute to search by.
            value (Union[str, bool]): The value to search for in the specified 
                                      attribute.

        Returns:
            List[Optional[Dict]]: A list of publications matching the search query.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            query = "SELECT id, title, first_author_last_name, "+\
                    "principal_investigator_last_name, field, date_accessed, "+\
                    "date_published, cited_in_paper, want_to_cite, "+\
                    f"own_paper, bibtex, primary_id FROM publications WHERE {attribute} = ?"
            c.execute(query, (value,))
            publications = [dict(zip([column[0] for column in c.description], row))\
                            for row in c.fetchall()]
        except sqlite3.Error as e:
            print("\033[38;5;223m"+f"SQLite error: {e}"+"\033[0m")
            traceback.print_exc()
            return []
        finally:
            if 'c' in locals(): c.close()  # Close the cursor if it exists
            conn.close()
            return publications


    def get_all_publications(self) -> List[Optional[Dict[str, Union[str, bool]]]]:
        """
        Fetches all publications from the database and returns them as a list of dictionaries.

        Returns:
            List[Optional[Dict]]: A list of all publications in the database.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            # Query to select all entries from the publications table
            query = "SELECT id, title, first_author_last_name, " + \
                    "principal_investigator_last_name, field, date_accessed, " + \
                    "date_published, cited_in_paper, want_to_cite, " + \
                    "own_paper, bibtex, primary_id FROM publications"

            c.execute(query)
            # Use the cursor's description attribute to get column names and
            # generate dictionaries for each row
            publications = [dict(zip([column[0] for column in c.description], row))
                            for row in c.fetchall()]

        except sqlite3.Error as e:
            print("\033[38;5;223m" + f"SQLite error: {e}" + "\033[0m")
            traceback.print_exc()
            return []

        finally:
            if 'c' in locals():
                c.close()  # Close the cursor if it exists
            conn.close()
            return publications


    def get_distinct_attributes(self) -> List[str]:
        """
        Fetches the distinct column names from the database to use as attributes for searching.

        Returns:
            List[str]: A list of distinct attributes.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("PRAGMA table_info(publications);")
            column_info = c.fetchall()
            return [column[1] for column in column_info]  # column[1] holds the name of the column
        except sqlite3.Error as e:
            print("\033[38;5;223m"+f"SQLite error: {e}"+"\033[0m")
            traceback.print_exc()
            return []
        finally:
            if 'c' in locals(): c.close()  # Close the cursor if it exists
            conn.close()


    def open_publication_pdf(self, publication_id: int) -> None:
        """
        Opens the PDF file corresponding to a given publication.

        Args:
            publication_id (int): The ID of the publication in the SQLite database.

        Raises:
            FileNotFoundError: If the PDF file does not exist.
            KeyError: If the publication with the given ID does not exist.
        """
        try:
            pub_id = self.pub_ID(publication_id)
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            # Retrieve the publication attributes from the database
            query = "SELECT * FROM publications WHERE id = ?"
            c.execute(query, (pub_id,))
            publication = c.fetchone()

            if not publication:
                raise KeyError(f"Publication with ID {publication_id} not found.")

            publication_dict = dict(zip([column[0] for column in c.description], publication))
            pdf_filename = self.generate_filename(publication_dict)
            pdf_path = os.path.join(os.path.dirname(self.db_path), pdf_filename)

            if not os.path.isfile(pdf_path):
                raise FileNotFoundError(f"PDF file {pdf_filename} not found.")

            # Open the PDF file using the system's default PDF viewer
            open_pdf(pdf_path)

        except (sqlite3.Error, FileNotFoundError, KeyError) as e:
            print("\033[38;5;223m"+f"An error occurred: {e}"+"\033[0m")
            traceback.print_exc()
        finally:
            if 'c' in locals(): c.close()  # Close the cursor if it exists
            conn.close()


    def display_publications_table(self, publications: List[Dict[str, Union[str, bool]]]) -> None:
        """
        Displays the list of publications in a formatted table similar to
        that produced by the display_entire_database method.

        Args:
            publications (List[Dict]): A list of dictionaries, each containing
                                       a publication's attributes.
        """
        if not publications:
            print("\033[38;5;223m"+"No publications to display."+"\033[0m")
            return

        # Modify the headers to match display_entire_database
        headers = ["id","Title", "1st auth. LN", "PI LN", "Field", "date acc.", "date pub.", "cited?", "want to cite"]

        # Truncate and format the rows to match display_entire_database
        table_data = []
        for pub in publications:
            row = [
                pub.get('id',''),
                pub.get('title', '')[:20]+'\n'+pub.get('title', '')[20:40],
                pub.get('first_author_last_name', '')[:15],  # Truncate the second column
                pub.get('principal_investigator_last_name', '')[:15],
                pub.get('field', ''),
                pub.get('date_accessed', ''),
                pub.get('date_published', ''),
                pub.get('cited_in_paper', ''),
                pub.get('want_to_cite', ''),
            ]
            table_data.append(row)

        print("\033[38;5;223m"+tabulate(table_data, headers, tablefmt="rounded_grid")+"\033[0m")


    def display_entire_database(self) -> None:
        """
        Display the entire content of the `publications` table in the database in a tabular form.

        This method uses the tabulate library for pretty-printing tables.
        Make sure to install the tabulate package before running this code.
        """
        try:
            # Establish a connection to the SQLite database
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            # Fetch all rows from the table
            c.execute("SELECT * FROM publications")
            rows = c.fetchall()

            # If there are no rows, print a message and return
            if not rows:
                print("\033[38;5;223m"+"No publications to display."+"\033[0m")
                return

            # Fetch column names for the header of the table
            column_names = [desc[0] for desc in c.description]

            # Modify column names for display
            column_names[2] = "1st auth. LN"  # Third column
            column_names[3] = "PI LN"  # Fourth column
            column_names[5] = "date acc."  # Fourth column
            column_names[6] = "date pub."  # Fourth column
            column_names[7] = "cited?"  # Fourth column
            column_names[8] = "want to cite"  # Fourth column

            # Truncate entries as needed
            truncated_rows = []
            for row in rows:
                truncated_row = list(row)
                truncated_row[1] = truncated_row[1][:20]+'\n'+truncated_row[1][20:40]  # Truncate the second column
                truncated_row[2] = truncated_row[2][:15]  # Truncate the third column
                truncated_row[3] = truncated_row[3][:15]  # Truncate the third column
                truncated_row = truncated_row[:-3]  # Omit the final column
                truncated_rows.append(tuple(truncated_row))

            print("\033[38;5;223m"+tabulate(truncated_rows, headers=column_names, tablefmt="rounded_grid")+"\033[0m")

        except sqlite3.Error as e:
            print("\033[38;5;223m"+f"SQLite error: {e}"+"\033[0m")
            traceback.print_exc()

        finally:
            # Closethe connection to the SQLite database
            if 'c' in locals(): c.close()  # Close the cursor if it exists
            conn.close()


    def modify_publication_attribute(self, publication_id: int) -> None:
        """
        Modify an attribute of a publication in the `publications` table by a given publication ID.

        Args:
            publication_id (int): The ID of the publication to modify.

        Returns:
            None
        """
        # Display all available attributes for modification
        try:
            pub_id = self.pub_ID(publication_id)
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT * FROM publications LIMIT 1")
            available_attributes = [desc[0] for desc in c.description[1:-1]]
            print("Available attributes for modification:"+"\033[0m")
            for i, attr in enumerate(available_attributes):
                print(f"{i + 1}. {attr}"+"\033[0m")

            # Ask the user to select an attribute to modify
            choice = int(input("\033[38;5;223m"+"Enter the number corresponding to the attribute you want to modify: "+"\033[0m"))
            selected_attribute = available_attributes[choice-1]

            # Get the new value from the user
            if selected_attribute == "field":
                if 'c' in locals(): c.close()  # Close the cursor if it exists
                conn.close()
                self.modify_field(pub_id)
                return
            else:
                new_value = input("\033[38;5;223m"+f"Enter the new value for {selected_attribute}: "+"\033[0m")

            # Update the record
            query = f"UPDATE publications SET {selected_attribute} = ? WHERE primary_id = ?"
            c.execute(query, (new_value, pub_id))
            conn.commit()
            print("\033[38;5;223m"+f"{selected_attribute} has been updated."+"\033[0m")
            if 'c' in locals(): c.close()  # Close the cursor if it exists
            conn.close()

        except sqlite3.Error as e:
            print("\033[38;5;223m"+f"SQLite error: {e}"+"\033[0m")
            traceback.print_exc()

        except IndexError:
            print("\033[38;5;223m"+"Invalid attribute choice."+"\033[0m")


    def modify_field(self, primary_pub_id: int) -> None:
        """
        Modify the field(s) of a publication in the `publications` table by a given publication ID.

        Args:
            primary_pub_id (int): The primary ID of the publication to modify.

        Returns:
            None
        """
        print("\033[38;5;223m"+"trying search"+"\033[0m")
        pubs = self.search_publications_by_attribute('primary_id', primary_pub_id)
        print("\033[38;5;223m"+"Search completed"+"\033[0m")
        for pub in pubs:
            if pub['id'] != pub['primary_id']:
                print("\033[38;5;223m"+"trying to delete pub with id: "+"\033[0m",pub['id'])
                self.delete_publication_by_id(pub['id'])
                print("\033[38;5;223m"+"deleted pub with id: "+"\033[0m",pub['id'])
            else:
                primary_pub = pub

        new_fields = input("\033[38;5;223m"+f"Enter the new value for field(s), comma-delimited: "+"\033[0m").split(",")
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        for i in range(len(new_fields)):
            if i == 0:
                query = f"UPDATE publications SET field = ? WHERE id = ?"
                c.execute(query, (new_fields[i].strip().lower(), str(primary_pub_id)))
                conn.commit()
                if 'c' in locals(): c.close()  # Close the cursor if it exists
                conn.close()
            else:
                extra_pub = primary_pub
                extra_pub['field'] = new_fields[i].strip().lower()
                self.add_publication(extra_pub)
        
        print("\033[38;5;223m"+"The field(s) has(have) been updated."+"\033[0m")


    def delete_publication_by_id(self, pub_id: int, retry_count: int = 3) -> bool:
        """
        Deletes a publication with the given ID from the `publications` table.

        Args:
            pub_id (int): The ID of the publication to be deleted.
            retry_count (int): Number of times to retry in case of a lock.

        Returns:
            bool: True if the record was deleted successfully, False otherwise.
        """
        while retry_count > 0:
            try:
                # Debugging
                print("\033[38;5;223m"+"Trying to establish a connection..."+"\033[0m")
                
                # Establish a connection to the SQLite database
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                
                # Debugging
                print("\033[38;5;223m"+"Connection established. Preparing to execute DELETE query..."+"\033[0m")
                
                # Prepare SQL query for deleting the record
                query = "DELETE FROM publications WHERE id = ?"
                
                # Execute SQL query
                c.execute(query, (pub_id,))
                
                # Debugging
                print("\033[38;5;223m"+"DELETE query executed. Committing..."+"\033[0m")
                
                # Commit changes
                conn.commit()

                # Debugging
                print("\033[38;5;223m"+"Changes committed."+"\033[0m")

                if c.rowcount >= 1:
                    return True  # Indicate that one or more rows were deleted
                
                return False  # Indicate that no rows were deleted

            except sqlite3.Error as e:
                if str(e) == "database is locked":
                    print("\033[38;5;223m"+"Database is locked, retrying..."+"\033[0m")
                    time.sleep(1)  # Wait for 1 second before retrying
                    retry_count -= 1
                else:
                    print("\033[38;5;223m"+f"SQLite error: {e}"+"\033[0m")
                    return False  # Return False in case of any other error

            finally:
                # Debugging
                print("\033[38;5;223m"+"Closing cursor and connection."+"\033[0m")
                
                # Explicitly close cursor and connection
                c.close()
                conn.close()
        return False  # If the loop completes, return False


    def get_publication_attribute(self, attribute: str, pub_id: int) -> Union[str, None]:
        """
        Fetches the value of a specified attribute for a given publication ID.

        Args:
            attribute (str): The name of the attribute to fetch.
            pub_id (int): The ID of the publication.

        Returns:
            Union[str, None]: The value of the attribute for the publication, or
                              None if not found or an error occurs.
        """
        try:
            # Establish a connection to the SQLite database
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            # Prepare the SQL query to fetch the attribute value for the given publication ID
            query = f"SELECT {attribute} FROM publications WHERE id = ?"

            # Execute the SQL query
            c.execute(query, (pub_id,))

            # Fetch the result
            row = c.fetchone()

            # If no record is found, return None
            if row is None:
                return None

            # The value will be the first (and only) item in the fetched row
            attribute_value = row[0]

            return attribute_value
        except sqlite3.Error as e:
            print("\033[38;5;223m"+f"SQLite error: {e}"+"\033[0m")
            return None  # Returning None in case of error
        finally:
            # Close the connection to the SQLite database
            if 'c' in locals(): c.close()  # Close the cursor if it exists
            conn.close()


    def pub_ID(self, pub_id:int) -> Union[int, None]:
        """
        Gets the primary ID of a publication in the database

        Args:
            pub_id: publication id, primary or not
        """
        return int(self.get_publication_attribute('primary_id', pub_id))


    def generate_bibtex_file(self, filename: str, publications: List[Dict[str, Union[str, bool]]]) -> None:
        """
        Generates a BibTeX file from a list of publications.

        Args:
            filename (str): The name of the BibTeX file to be generated.
            publications (List[Dict]): A list of dictionaries, each containing a publication's attributes.

        Raises:
            IOError: If the file cannot be written.
        """
        try:
            bib_directory = os.path.join(os.path.dirname(self.db_path), 'bibfiles')
            os.makedirs(bib_directory, exist_ok=True)
            file_path = os.path.join(bib_directory, filename + '.bib')
            ids_added = []

            with open(file_path, 'w') as f:
                for publication in publications:
                    if publication['primary_id'] not in ids_added:
                        f.write(publication['bibtex'])
                        f.write('\n\n')
                        ids_added.append(publication['primary_id'])

            print(f"BibTeX file '{filename}.bib' generated successfully."+"\033[0m")

        except IOError as e:
            print(f"An error occurred while writing the BibTeX file: {e}"+"\033[0m")
            traceback.print_exc()


    def generate_bibtex_file_database(self, filename: str) -> None:
        """
        Now do it for the whole database
        """
        self.generate_bibtex_file(filename, self.get_all_publications())


    def prompt_for_bibtex_record(self) -> str:
        """
        Prompts the user to enter the data for each field in a BibTeX article entry.

        Returns:
            str: A BibTeX entry as a string, formatted with the user's input.
        """

        # Prompt user for each field
        entry_type = input("\033[38;5;223m"+"Enter the type of the BibTeX entry (e.g., article, book, etc.): "+"\033[0m")
        citation_key = input("\033[38;5;223m"+"Enter the citation key: "+"\033[0m")
        title = input("\033[38;5;223m"+"Enter the title of the article: "+"\033[0m")
        author = input("\033[38;5;223m"+"Enter the author(s): "+"\033[0m")
        journal = input("\033[38;5;223m"+"Enter the journal name: "+"\033[0m")
        volume = input("\033[38;5;223m"+"Enter the volume: "+"\033[0m")
        number = input("\033[38;5;223m"+"Enter the issue number: "+"\033[0m")
        year = input("\033[38;5;223m"+"Enter the year of publication: "+"\033[0m")
        publisher = input("\033[38;5;223m"+"Enter the publisher: "+"\033[0m")

        # Format the BibTeX entry
        bibtex_entry = f"""
        @{entry_type}{{{citation_key},
        title={{{title}}},
        author={{{author}}},
        journal={{{journal}}},
        volume={{{volume}}},
        number={{{number}}},
        year={{{year}}},
        publisher={{{publisher}}}
        }}
        """

        return bibtex_entry


    def prompt_and_save_bibtex(self, file_path: str) -> str:
        """
        Prompts the user to input an entire BibTeX record, and then saves it to a given file path.

        Parameters:
            file_path (str): The full file path where the BibTeX record will be saved.

        Returns:
            None
        """
        # Prompt the user for the BibTeX record
        lines = []
        print("\033[38;5;223m"+"Paste the entire BibTeX record below. Type 'END' on a new line when done."+"\033[0m")
        while True:
            line = input()
            if line.strip() == 'END':
                break
            lines.append(line)
        bibtex_record = '\n'.join(lines)

        # Validate the record minimally (e.g., check if it starts with '@')
        if not bibtex_record.startswith('@'):
            print("\033[38;5;223m"+"Invalid BibTeX record. The record should start with '@'."+"\033[0m")
            return

        # Save the BibTeX record to the given file path
        with open(file_path, 'w') as bib_file:
            bib_file.write(bibtex_record)

        print("\033[38;5;223m"+f"BibTeX record saved to {file_path}."+"\033[0m")

        return bibtex_record


    def First_Author_bib(self, bib_content: str) -> str:
        """
        Get first author last name from a bibtex record string
        """
        bib_db = bibtexparser.loads(bib_content).entries[0]

        a_list = bib_db['author'].split('and')
        if ',' in a_list[0]:
            Lname = a_list[0].split(',')[0]
        else:
            names = a_list[0].split(' ')
            Lname = names[len(names)-1]
            if len(Lname) == 0:
                Lname = names[len(names)-2]

        return Lname


    def Last_Author_bib(self, bib_content: str) -> str:
        """
        Get Last author (PI) last name from a bibtex record string
        """
        bib_db = bibtexparser.loads(bib_content).entries[0]

        a_list = bib_db['author'].split('and')
        last = len(a_list) - 1
        if ',' in a_list[last]:
            Lname = a_list[last].split(',')[0]
        else:
            names = a_list[last].split(' ')
            Lname = names[len(names)-1]
            if len(Lname) == 0:
                Lname = names[len(names)-2]

        return Lname


    def count_total_entries(self) -> int:
        """
        Query the total number of entries in the `publications` table.

        Returns:
            int: The total number of entries in the `publications` table.
        """
        try:
            # Establish a connection to the SQLite database
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
    
            # Execute the SQL query to count the number of rows in the table
            c.execute("SELECT COUNT(*) FROM publications")

            # Fetch the result; COUNT returns a single row with one column
            row = c.fetchone()

            # The count will be the first (and only) item in the row
            total_entries = row[0]

            return total_entries
        except sqlite3.Error as e:
            print("\033[38;5;223m"+f"SQLite error: {e}"+"\033[0m")
            return 0  # Returning zero in case of error
        finally:
            # Close the connection to the SQLite database
            if 'c' in locals(): c.close()  # Close the cursor if it exists
            conn.close()


    def get_next_available_id(self) -> int:
        """Get the next available ID for inserting a new publication.

        Returns:
            int: The next available ID.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            # Get the maximum ID currently in the database
            c.execute("SELECT MAX(id) FROM publications")
            max_id = c.fetchone()[0]

            # If the table is empty, start from 1; otherwise, increment the maximum ID
            next_id = 1 if max_id is None else max_id + 1
            return next_id
        except sqlite3.Error as e:
            print("\033[38;5;223m"+f"SQLite error: {e}"+"\033[0m")
            traceback.print_exc()
            return -1  # Indicate an error
        finally:
            if 'c' in locals(): c.close()  # Close the cursor if it exists
            conn.close()