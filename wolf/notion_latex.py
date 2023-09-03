"""
The Notion2Latex class is a utility designed for interacting with the Notion API.

Processing specific operations and subsequently converting the retrieved data from Notion to LaTeX format.
"""
import base64
import difflib
import json
import os
import subprocess
import time

import jsonschema
import pygit2
import schedule
import unidecode
from github import Github, InputGitTreeElement
from notion2md.exporter.block import MarkdownExporter

from wolf_core import application


class Notion2Latex(application.Application):
    """
    Notion2Latex

    This class is used for converting Notion markdown files to LaTeX format.

    Methods:
        - get_files(): Retrieves files from Notion and returns a list of file IDs.
        - get_markdown(file): Get the markdown file from Notion.
        - compile (file, param_dict): Compile a Markdown file into a PDF using the pandoc and xelatex tools.
        - job(): Perform the SyncNotion job.

    Attributes:
        - frequency: The frequency of when the job should be executed.
        - validate_schema: The schema used for validating the markdown files.
    """

    def __init__(self):
        super().__init__()
        self.frequency = schedule.every(5).minutes
        self.validate_schema = {
            "type": "object",
            "properties": {
                "client": {"type": "string"},
                "titre": {"type": "string"},
                "phase_id": {"type": "string"},
                "phase_nom": {"type": "string"},
            },
            "required": ["client", "titre", "phase_id", "phase_nom"]
        }
        self.logger.error(os.getcwd())
        os.chdir(os.path.dirname(os.path.realpath(__file__)))
        with open('token.json') as file:
            token = json.load(file)['github_doc_publish']
        self.master_file = "39b8866e6090425c8d1fe799b74956c3"
        self.github = Github(token)
        self.repo = self.github.get_user().get_repo('doc_latex-compiled-result-wolf')

    @staticmethod
    def run_command(cmd):
        """
        Run a command in the shell.

        :param cmd: The command to be run in the shell.
        :return: The output of the command.
        """
        status = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if status.returncode != 0:
            return False
        return True

    def get_template(self):
        """
        Retrieves the template for Notion to LaTeX conversion.

        :return: None
        """
        url = ""
        try:
            with open('token.json') as file:
                token = json.load(file)['github_doc_latex']
            url = "https://github.com/catie-aq/doc_latex-template.git"
            url_with_token = f"https://{token}@{url[8:]}"
            self.run_command("rm -rf doc_latex-template-complex-version")
            pygit2.clone_repository(url_with_token, "doc_latex-template-complex-version",
                                    checkout_branch="complex-version")

            with open('token.json') as file:
                token = json.load(file)['github_doc_publish']
            url = "https://github.com/catie-aq/doc_latex-compiled-result-wolf.git"
            url_with_token = f"https://{token}@{url[8:]}"
            self.run_command("rm -rf doc_latex-compiled-result-wolf")
            pygit2.clone_repository(url_with_token, "doc_latex-compiled-result-wolf")

        except pygit2.GitError as e:  # Catch the pygit2.GitError exception
            self.logger.error(f"Error while cloning repository from {url}: {e}")
        except FileNotFoundError as e:  # Catch the FileNotFoundError exception for 'token.json'
            self.logger.error(f"Unable to open the 'token.json' file: {e}")
        except json.JSONDecodeError as e:  # Catch the JSONDecodeError for malformed JSON in 'token.json'
            self.logger.error(f"Unable to parse the JSON from 'token.json': {e}")

    def get_files(self):
        """
        Retrieves files from Notion and returns a list of file IDs.

        :return: A list of file IDs.
        """
        req = self.api("Notion").get.block_children(self.master_file)
        if req.status_code != 200:
            self.logger.error("Failed to get files from Notion.")
            return None, None

        files, block_saved = self.get_files_from_results(req)
        self.logger.info(f"Get {len(files)} files from Notion.")

        return files, block_saved

    @staticmethod
    def get_files_from_results(req):
        """
        :param req: The request object containing the results from Notion API.
        :return: A tuple containing two lists - files and block_saved.
                 - files: List of page IDs extracted from the results.
                 - block_saved: List of blocks that contain the extracted page IDs.
        """
        files = []
        block_saved = []
        blocks = req.data["results"]

        for block in blocks:
            if block["type"] == "paragraph":
                for rich_text in block["paragraph"]["rich_text"]:
                    if rich_text["type"] == "mention" and rich_text["mention"]["type"] == "page":
                        files.append(rich_text["mention"]["page"]["id"])
                        block_saved.append(block)
        return files, block_saved

    def get_markdown(self, file):
        """
        Get the markdown file from Notion.

        :param file: The file path of the markdown file to process
        :return: Returns a dictionary containing parameter information if the markdown file has valid header data
        """
        MarkdownExporter(block_id=file, output_path='.', download=True).export()
        self.run_command("unzip -o -d . " + file + ".zip > /dev/null")
        self.run_command("mv *.png doc_latex-template-complex-version/src")
        self.run_command("mv *.jpg doc_latex-template-complex-version/src")
        self.run_command("mv *.jpeg doc_latex-template-complex-version/src")
        self.run_command("mv *.svg doc_latex-template-complex-version/src")
        self.run_command("mv *.gif doc_latex-template-complex-version/src")
        self.run_command("rm " + file + ".zip")
        param_dict = None
        with open(file + ".md") as f:
            data = f.read()
        if data.startswith("---"):
            index = data.find("---", 3)
            header_data = data[:index + 3]
            header_data = header_data.replace("\n\n", "\n")
            body_data = data[index + 3:]
            param_dict = {}
            header_data_line_process = ""
            for line in header_data.splitlines():
                if line.startswith("- nom"):
                    line = "  " + line
                elif line.startswith("email"):
                    line = "    " + line
                else:
                    try:
                        key, value = line.split(":")
                        param_dict[key.strip()] = value.strip()
                    except ValueError:
                        pass
                header_data_line_process += line + "\n"
            with open(file + ".md", "w") as f:
                f.write(header_data_line_process.lstrip())
                f.write(body_data)
        try:
            jsonschema.validate(param_dict, self.validate_schema)
        except jsonschema.exceptions.ValidationError:
            self.logger.error("JSON Schema validation failed for file: " + file + ".md")
            self.run_command("rm " + file + ".md")
        if "email" in param_dict or "name" in param_dict:
            return None
        return param_dict

    @staticmethod
    def check_diff(current, last):
        """
        Compares the contents of two files and returns True if there is a difference,
        otherwise returns False.

        :param current: Path to the current file
        :param last: Path to the previous file
        :type current: str
        :type last: str
        :return: True if there is a difference, otherwise False
        :rtype: bool
        """
        if os.path.isfile(current) and os.path.isfile(last):
            with open(current) as cur, open(last) as las:
                diff = difflib.ndiff(cur.readlines(), las.readlines())
                count = sum(1 for line in diff if line.startswith('+') or line.startswith('-'))
            if count == 0:
                return False
        return True

    def compile(self, file, param_dict):
        """
        This method compiles a Markdown file into a PDF using the pandoc and xelatex tools.

        :param file: The path of the Markdown file to be compiled.
        :param param_dict: A dictionary containing the parameters for compilation.
        :return: None
        """
        client = unidecode.unidecode(param_dict["client"]).lower().replace("'", "")
        titre = unidecode.unidecode(param_dict["titre"]).lower().replace("'", "")
        phase_id = unidecode.unidecode(param_dict["phase_id"]).lower().replace("'", "")
        phase_nom = unidecode.unidecode(param_dict["phase_nom"]).lower().replace("'", "")
        title = client + "_" + titre + "_" + phase_id + "_" + phase_nom
        title = title.replace(" ", "-")

        file_path_tex = file + ".tex"
        file_name_tex = param_dict["client"] + "/" + title + ".tex"

        last_compiled_path_tex = "../../doc_latex-compiled-result-wolf/" + file_name_tex

        os.chdir(os.path.dirname(os.path.realpath(__file__)))
        self.run_command("cp " + file + ".md doc_latex-template-complex-version/src")
        os.chdir("doc_latex-template-complex-version/src")
        self.run_command("pandoc " + file + ".md --template=template.tex -o " + file + ".tex")

        diff = self.check_diff(file_path_tex, last_compiled_path_tex)
        if not diff:
            self.logger.info("No diff between {} and {}".format(file_path_tex, last_compiled_path_tex))
            return False, title

        success_first = self.run_command("xelatex -interaction=nonstopmode " + file + ".tex  >/dev/null")
        success_second = self.run_command("xelatex -interaction=nonstopmode " + file + ".tex  >/dev/null")
        success = success_first and success_second
        if not success:
            self.logger.error("Failed to compile file: " + file + ".md")
            return False, None

        self.run_command("mv " + file + ".pdf ../out/" + title + ".pdf")
        self.run_command("mv " + file + ".tex ../out/" + title + ".tex")
        os.chdir("../..")
        return True, title

    def publish_compiled(self, param_dict, title):
        """
        Publishes the compiled PDF file to a GitHub repository.

        :param param_dict: A dictionary containing parameters for publishing the compiled PDF.
        :param title: The title of the PDF file.
        :return: None
        """
        file_path = "doc_latex-template-complex-version/out/" + title + ".pdf"
        file_path_tex = "doc_latex-template-complex-version/out/" + title + ".tex"
        file_name = param_dict["client"] + "/" + title + ".pdf"
        file_name_tex = param_dict["client"] + "/" + title + ".tex"

        # noinspection PyBroadException
        try:
            commit_message = 'Add ' + file_name + ' on GitHub'
            master_ref = self.repo.get_git_ref('heads/master')
            master_sha = master_ref.object.sha
            base_tree = self.repo.get_git_tree(master_sha)
            with open(file_path, 'rb') as input_file:
                data = input_file.read()
            data = base64.b64encode(data).decode("utf-8")

            with open(file_path_tex, 'rb') as input_file:
                data_tex = input_file.read()
            data_tex = base64.b64encode(data_tex).decode("utf-8")

            blob = self.repo.create_git_blob(data, "base64")
            blob_tex = self.repo.create_git_blob(data_tex, "base64")
            element = InputGitTreeElement(file_name, '100644', 'blob', sha=blob.sha)
            element_tex = InputGitTreeElement(file_name_tex, '100644', 'blob', sha=blob_tex.sha)
            element_list = [element, element_tex]
            tree = self.repo.create_git_tree(element_list, base_tree=base_tree)
            parent = self.repo.get_git_commit(master_sha)
            commit = self.repo.create_git_commit(commit_message, tree, [parent])
            master_ref.edit(commit.sha)
        except Exception as e:
            self.logger.error(f"Le fichier PDF {file_name} n'a pas pu être poussé sur le repo.")
            return None
        self.logger.info(f"Le fichier PDF {file_name} a été poussé sur le repo avec succès.")
        return "https://github.com/{}/{}/blob/{}/{}".format(self.repo.owner.login, self.repo.name, master_ref.ref,
                                                            file_name)

    def update_notion(self, success, file_id, block, msg=None, link=None):
        """
        Updates the Notion page with the result of the compilation.

        :param success: Boolean value indicating whether the update was successful.
        :param file_id: String representing the ID of the Notion page.
        :param block: Dictionary representing the block on the Notion page.
        :param msg: Optional string representing an additional message to display.
        :param link: Optional string representing the GitHub link.
        :return: None
        """
        string_display = " ✅ " + time.strftime("%d/%m/%Y %H:%M:%S", time.localtime()) \
            if success else " ❌ " + time.strftime("%d/%m/%Y %H:%M:%S", time.localtime())
        if msg:
            string_display += " - " + msg
        new_paragraph_block = {
            'paragraph': {
                'rich_text': [
                    {
                        'type': 'mention',
                        'mention': {
                            'type': 'page',
                            'page': {
                                'id': file_id
                            }
                        },
                        'annotations': {
                            'bold': False,
                            'italic': False,
                            'strikethrough': False,
                            'underline': False,
                            'code': False,
                            'color': 'default'
                        },
                        'plain_text': 'Test',
                        'href': 'https://www.notion.so/' + file_id
                    },
                    {
                        'type': 'text',
                        'text': {
                            'content': string_display,
                            'link': None
                        },
                    }
                ]
            }
        }
        if link:
            # noinspection PyTypeChecker
            new_paragraph_block['paragraph']['rich_text'].append({
                'type': 'text',
                'text': {
                    'content': " - Github link",
                    'link': {
                        'url': link
                    }
                }
            })
        req = self.api("Notion").patch.block(block["id"], new_paragraph_block)
        if not req:
            self.logger.error("Error while updating Notion page.")
            raise Exception("Error while updating Notion page.")

    def job(self) -> application.Status:
        """
        Perform the SyncNotion job.

        This method starts the job by setting the status to "RUNNING."
        It then sets the status to "SUCCESS" and logs the job finished with the current status.

        :return: application.Status The status of the job indicating whether it was successful or not.
        """
        self.logger.debug("Notion to LaTeX conversion started.")
        self.get_template()
        files, blocks = self.get_files()
        if files is None:
            self.set_status(application.Status.ERROR)
            self.health_check = {"message": "Failed to get files from Notion."}
            return application.Status.ERROR
        failure = 0
        for file in files:
            param_dict = self.get_markdown(file)
            if param_dict is None:
                self.update_notion(False, file, blocks[files.index(file)], "The markdown header is badly formatted.")
                failure += 1
                continue
            process, title = self.compile(file, param_dict)
            print(process, title)
            if not process and title is not None:
                continue
            if not process and title is None:
                self.update_notion(False, file, blocks[files.index(file)], "The compilation failed.")
                failure += 1
                continue
            link = self.publish_compiled(param_dict, title)
            if link is None:
                self.update_notion(False, file, blocks[files.index(file)], "The PDF could not be published.")
                failure += 1
                continue
            self.update_notion(True, file, blocks[files.index(file)], link=link)

        self.run_command("rm -rf doc_latex-template-complex-version")
        self.run_command("rm -rf doc_latex-compiled-result-wolf")
        self.run_command("rm -r *.md")

        str_msg = "SyncNotion compiled {} files.".format(len(files))
        self.logger.debug(str_msg)

        if failure == len(files):
            self.set_status(application.Status.ERROR)
            self.health_check = {"message": "All files failed to compile."}
            return application.Status.ERROR
        else:
            self.set_status(application.Status.SUCCESS)
            self.health_check = {"message": str_msg}
            return application.Status.SUCCESS

    def __del__(self):
        try:
            self.run_command("rm -rf doc_latex-template-complex-version")
            self.run_command("rm -r *.md")
        except FileNotFoundError:
            pass
