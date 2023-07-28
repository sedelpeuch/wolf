"""
The Notion2Latex class is a utility designed for interacting with the Notion API.

Processing specific operations and subsequently converting the retrieved data from Notion to LaTeX format.
"""
import base64
import json
import os
import subprocess

import jsonschema
import pygit2
import schedule
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
        self.frequency = schedule.every(5).seconds
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
        self.master_file = "011f57a503864878b9e777d80932706d"
        with open('token.json') as file:
            token = json.load(file)['github_doc_publish']
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
            raise RuntimeError("Failed to run command: " + cmd + "\n" + status.stderr)
        return True

    def get_files(self):
        """
        Retrieves files from Notion and returns a list of file IDs.

        :return: A list of file IDs.
        """
        req = self.api("Notion").get.block_children(self.master_file)
        if req.status_code != 200:
            self.logger.error("Failed to get files from Notion.")
            return None
        files = []
        blocks = req.data["results"]
        for block in blocks:
            if block["type"] == "paragraph":
                for rich_text in block["paragraph"]["rich_text"]:
                    if rich_text["type"] == "mention":
                        if rich_text["mention"]["type"] == "page":
                            files.append(rich_text["mention"]["page"]["id"])
        return files

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
            except jsonschema.exceptions.ValidationError as e:
                self.logger.error("JSON Schema validation failed for file: " + file + ".md" + "\n" + str(e))
                self.set_status(application.Status.ERROR)
                return application.Status.ERROR
            finally:
                self.logger.warning(
                    "JSON Schema validation passed for file: " + file + ".md." + " Beginning compilation "
                                                                                 "...")
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
        self.run_command(
            "pandoc " + file + ".md --template=template.tex -o " + file + ".tex && xelatex "
            + file + ".tex interaction=nonstopmode >/dev/null"
        )
        self.run_command("rm *.aux *.log *.out")
        self.run_command("rm " + file + ".md " + file + ".tex")
        title = (param_dict["client"] + "_" + param_dict["titre"]).lower()
        title = title.replace(" ", "-")
        self.run_command("mv " + file + ".pdf ../out/" + title + ".pdf")
        os.chdir("../..")
        self.run_command("rm " + file + ".md")
        return title

    def publish_compiled(self, file, title):
        """
        Publishes the compiled PDF file to the Notion page.

        :param file: The path to the compiled PDF file.
        :type file: str
        :param title: The title of the Notion page.
        :type title: str
        :return: None
        """
        pdf_file_location = "doc_latex-template-complex-version/out/" + title + ".pdf"
        # with open(pdf_file_location, "rb") as f:
        #     data = f.read()
        # base64content = base64.b64encode(data)
        # tree = self.repo.get_git_tree("master")
        # element = InputGitTreeElement(path=pdf_file_location, mode='100644', type='blob',
        #                               content=base64content.decode())
        # tree_data = self.repo.create_git_tree(tree=[element], base_tree=tree)
        # parents = [self.repo.get_git_commit(sha="master")]
        #
        # commit = self.repo.create_git_commit(message='Add PDF', tree=tree_data, parents=parents)
        # self.repo.head_ref.edit(sha=commit.sha)

        block_object = {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": pdf_file_location,
                            "link": None
                        }
                    }
                ]
            }
        }
        req = self.api("Notion").patch.block_children(self.master_file, [block_object])

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
        self.logger.debug("SyncNotion job started.")
        self.get_template()
        files = self.get_files()
        if files is None:
            self.set_status(application.Status.ERROR)
            self.health_check = {"message": "Failed to get files from Notion."}
            return application.Status.ERROR
        for file in files:
            param_dict = self.get_markdown(file)
            if param_dict is None:
                self.set_status(application.Status.ERROR)
                self.health_check = {"message": "JSON Schema validation failed for file: " + file + ".md"}
                return application.Status.ERROR
            title = self.compile(file, param_dict)
            self.publish_compiled(file, title)
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
