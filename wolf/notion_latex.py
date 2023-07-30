"""
The Notion2Latex class is a utility designed for interacting with the Notion API.

Processing specific operations and subsequently converting the retrieved data from Notion to LaTeX format.
"""
import base64
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
        self.frequency = schedule.every(1).minutes
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
        with open('token.json') as file:
            token = json.load(file)['github_doc_publish']
            self.master_file = json.load(file)['notion_master_file']
        self.github = Github(token)
        self.repo = self.github.get_user().get_repo('compiled_result_latex')

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

    def get_files(self):
        """
        Retrieves files from Notion and returns a list of file IDs.

        :return: A list of file IDs.
        """
        req = self.api("Notion").get.block_children(self.master_file)
        if req.status_code != 200:
            self.logger.error("Failed to get files from Notion.")
            return None, None
        files = []
        block_saved = []
        blocks = req.data["results"]
        for block in blocks:
            if block["type"] == "paragraph":
                for rich_text in block["paragraph"]["rich_text"]:
                    if rich_text["type"] == "mention":
                        if rich_text["mention"]["type"] == "page":
                            files.append(rich_text["mention"]["page"]["id"])
                            block_saved.append(block)
        self.logger.info("Get {} files from Notion.".format(len(files)))
        return files, block_saved

    def get_markdown(self, file):
        """
        Get the markdown file from Notion.

        :param file: The file path of the markdown file to process
        :return: Returns a dictionary containing parameter information if the markdown file has valid header data
        """
        MarkdownExporter(block_id=file, output_path='.', download=True).export()
        self.run_command("unzip -o -d . " + file + ".zip > /dev/null")
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
                f.write(header_data_line_process[:index + 12].lstrip())
                f.write(body_data)
        try:
            jsonschema.validate(param_dict, self.validate_schema)
        except jsonschema.exceptions.ValidationError:
            self.logger.error("JSON Schema validation failed for file: " + file + ".md")
            self.run_command("rm " + file + ".md")
        return param_dict

    def compile(self, file, param_dict):
        """
        This method compiles a Markdown file into a PDF using the pandoc and xelatex tools.

        :param file: The path of the Markdown file to be compiled.
        :param param_dict: A dictionary containing the parameters for compilation.
        :return: None
        """
        self.run_command("cp " + file + ".md doc_latex-template-complex-version/src")
        os.chdir("doc_latex-template-complex-version/src")
        success_first = self.run_command(
            "pandoc " + file + ".md --template=template.tex -o " + file + ".tex && xelatex "
            + file + ".tex interaction=nonstopmode >/dev/null"
        )
        success_second = self.run_command(
            "xelatex " + file + ".tex interaction=nonstopmode >/dev/null"
        )
        success = success_first and success_second
        if not success:
            self.logger.error("Failed to compile file: " + file + ".md")
            return None
        self.run_command("rm *.aux *.log *.out")
        self.run_command("rm " + file + ".md " + file + ".tex")

        client = unidecode.unidecode(param_dict["client"]).lower().replace("'", "")
        titre = unidecode.unidecode(param_dict["titre"]).lower().replace("'", "")
        phase_id = unidecode.unidecode(param_dict["phase_id"]).lower().replace("'", "")
        phase_nom = unidecode.unidecode(param_dict["phase_nom"]).lower().replace("'", "")
        title = client + "_" + titre + "_" + phase_id + "_" + phase_nom
        title = title.replace(" ", "-")
        self.run_command("mv " + file + ".pdf ../out/" + title + ".pdf")
        os.chdir("../..")
        self.run_command("rm " + file + ".md")
        return title

    def publish_compiled(self, param_dict, title):
        """
        Publishes the compiled PDF file to a GitHub repository.

        :param param_dict: A dictionary containing parameters for publishing the compiled PDF.
        :param title: The title of the PDF file.
        :return: None
        """
        file_path = "doc_latex-template-complex-version/out/" + title + ".pdf"
        file_name = param_dict["client"] + "/" + title + ".pdf"

        # noinspection PyBroadException
        try:
            commit_message = 'Add ' + file_name + ' on GitHub'
            master_ref = self.repo.get_git_ref('heads/master')
            master_sha = master_ref.object.sha
            base_tree = self.repo.get_git_tree(master_sha)
            with open(file_path, 'rb') as input_file:
                data = input_file.read()
            data = base64.b64encode(data).decode("utf-8")
            blob = self.repo.create_git_blob(data, "base64")
            element = InputGitTreeElement(file_name, '100644', 'blob', sha=blob.sha)
            tree = self.repo.create_git_tree([element], base_tree=base_tree)
            parent = self.repo.get_git_commit(master_sha)
            commit = self.repo.create_git_commit(commit_message, tree, [parent])
            master_ref.edit(commit.sha)
        except Exception:
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
        except pygit2.GitError as e:  # Catch the pygit2.GitError exception
            self.logger.error(f"Error while cloning repository from {url}: {e}")
        except FileNotFoundError as e:  # Catch the FileNotFoundError exception for 'token.json'
            self.logger.error(f"Unable to open the 'token.json' file: {e}")
        except json.JSONDecodeError as e:  # Catch the JSONDecodeError for malformed JSON in 'token.json'
            self.logger.error(f"Unable to parse the JSON from 'token.json': {e}")

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
        for file in files:
            param_dict = self.get_markdown(file)
            if param_dict is None:
                self.update_notion(False, file, blocks[files.index(file)], "The markdown header is badly formatted.")
                continue
            title = self.compile(file, param_dict)
            if title is None:
                self.update_notion(False, file, blocks[files.index(file)], "The compilation failed.")
                continue
            link = self.publish_compiled(param_dict, title)
            if link is None:
                self.update_notion(False, file, blocks[files.index(file)], "The PDF could not be published.")
                continue
            self.update_notion(True, file, blocks[files.index(file)], link=link)

        self.set_status(application.Status.SUCCESS)
        str_msg = "SyncNotion compiled {} files.".format(len(files))
        self.run_command("rm -rf doc_latex-template-complex-version")
        self.logger.debug(str_msg)
        self.health_check = {"message": str_msg}
        return application.Status.SUCCESS

    def __del__(self):
        try:
            self.run_command("rm -rf doc_latex-template-complex-version")
        except FileNotFoundError:
            pass
