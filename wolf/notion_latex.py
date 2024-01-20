"""
The Notion2Latex class is a utility designed for interacting with the Notion API.

Processing specific operations and subsequently converting the retrieved data from Notion to
LaTeX format.
"""
import json
import os
import subprocess
import time

import jsonschema
import pygit2
import requests
import unidecode
from notion2md.exporter.block import MarkdownExporter

from wolf_core import application


class Notion2Latex(application.Application):
    """
    This class represents the application for converting Notion pages to LaTeX files.
    """

    def __init__(self):
        super().__init__()
        self.validate_schema = {
            "type": "object",
            "properties": {
                "client": {"type": "string"},
                "titre": {"type": "string"},
                "phase_id": {"type": "string"},
                "phase_nom": {"type": "string"},
            },
            "required": ["client", "titre", "phase_id", "phase_nom"],
        }

        os.chdir(os.path.dirname(os.path.realpath(__file__)))
        with open("token.json") as file:
            self.master_file = json.load(file)["notion_master_file"]
            self.token = json.load(file)["github"]

    @staticmethod
    def run_command(cmd):
        """
        Run a command in the shell.

        :param cmd: The command to be run in the shell.
        :return: The output of the command.
        """
        status = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if status.returncode != 0:
            print(f"Error : {status.stderr}")
            return False
        return True

    def get_template(self):
        """
        Retrieves the template for Notion to LaTeX conversion.

        :return: None
        """
        url = ""
        try:
            url = "https://github.com/catie-aq/doc_latex-template.git"
            url_with_token = f"https://{self.token}@{url[8:]}"
            self.run_command("rm -rf doc_latex-template-complex-version")
            pygit2.clone_repository(
                url_with_token,
                "doc_latex-template-complex-version",
                checkout_branch="complex-version",
            )
        except pygit2.GitError as e:
            self.logger.error(f"Error while cloning repository from {url}: {e}")
        except FileNotFoundError as e:
            self.logger.error(f"Unable to open the 'token.json' file: {e}")
        except json.JSONDecodeError as e:
            self.logger.error(
                f"Unable to parse the JSON from 'token.json': {e}"
            )

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
        blocks = req.data["results"]
        files_and_blocks = [
            (rich_text["mention"]["page"]["id"], block)
            for block in blocks
            if block["type"] == "paragraph"
            for rich_text in block["paragraph"]["rich_text"]
            if rich_text["type"] == "mention"
            and rich_text["mention"]["type"] == "page"
        ]
        files, block_saved = (
            zip(*files_and_blocks) if files_and_blocks else ([], [])
        )
        return files, block_saved

    def get_markdown(self, file):
        """
        Get the markdown file from Notion.

        :param file: The file path of the markdown file to process
        :return: Returns a dictionary containing parameter information if the markdown file has
        valid header data
        """
        MarkdownExporter(block_id=file, output_path=".", download=True).export()

        self.run_command(f"unzip -o -d . {file}.zip > /dev/null")
        image_file_types = ["png", "jpg", "jpeg", "svg", "gif", "pdf"]
        for file_type in image_file_types:
            self.run_command(
                f"mv *.{file_type} doc_latex-template-complex-version/src"
            )
        self.run_command(f"rm {file}.zip")

        param_dict = None
        with open(file + ".md") as f:
            data = f.read()
        if data.startswith("---"):
            index = data.find("---", 3)
            header_data = data[: index + 3]
            header_data = header_data.replace("\n\n", "\n")
            body_data = data[index + 3 :]
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
            self.logger.error(
                "JSON Schema validation failed for file: " + file + ".md"
            )
            self.run_command("rm " + file + ".md")
        if "email" in param_dict or "name" in param_dict:
            return None
        return param_dict

    def compile(self, file, param_dict):
        """
        This method compiles a Markdown file into a PDF using the pandoc and xelatex tools.

        :param file: The path of the Markdown file to be compiled.
        :param param_dict: A dictionary containing the parameters for compilation.
        :return: None
        """
        client = (
            unidecode.unidecode(param_dict["client"]).lower().replace("'", "")
        )
        titre = (
            unidecode.unidecode(param_dict["titre"]).lower().replace("'", "")
        )
        phase_id = (
            unidecode.unidecode(param_dict["phase_id"]).lower().replace("'", "")
        )
        phase_nom = (
            unidecode.unidecode(param_dict["phase_nom"])
            .lower()
            .replace("'", "")
        )
        title = client + "_" + titre + "_" + phase_id + "_" + phase_nom
        title = title.replace(" ", "-")

        os.chdir(os.path.dirname(os.path.realpath(__file__)))
        self.run_command(
            "cp " + file + ".md doc_latex-template-complex-version/src"
        )
        os.chdir("doc_latex-template-complex-version/src")
        self.run_command(
            "pandoc " + file + ".md --template=template.tex -o " + file + ".tex"
        )

        success_first = self.run_command(
            "xelatex -interaction=nonstopmode " + file + ".tex"
        )
        success_second = self.run_command(
            "xelatex -interaction=nonstopmode " + file + ".tex  " ">/dev/null"
        )
        success = success_first and success_second
        if not success:
            self.logger.error("Failed to compile file: " + file + ".md")
            return False, None

        self.run_command("mv " + file + ".pdf ../out/" + title + ".pdf")
        self.run_command("mv " + file + ".tex ../out/" + title + ".tex")
        os.chdir("../..")
        self.logger.info("File " + file + ".md compiled successfully.")
        return True, title

    def update_notion(self, success, file_id, block, msg=None):
        """
        Updates the Notion page with the result of the compilation.

        :param success: Boolean value indicating whether the update was successful.
        :param file_id: String representing the ID of the Notion page.
        :param block: Dictionary representing the block on the Notion page.
        :param msg: Optional string representing an additional message to display.
        :return: None
        """
        string_display = (
            " ✅ " + time.strftime("%d/%m/%Y %H:%M:%S", time.localtime())
            if success
            else " ❌ " + time.strftime("%d/%m/%Y %H:%M:%S", time.localtime())
        )
        if msg:
            string_display += " - " + msg
        new_paragraph_block = {
            "paragraph": {
                "rich_text": [
                    {
                        "type": "mention",
                        "mention": {"type": "page", "page": {"id": file_id}},
                        "annotations": {
                            "bold": False,
                            "italic": False,
                            "strikethrough": False,
                            "underline": False,
                            "code": False,
                            "color": "default",
                        },
                        "plain_text": "Test",
                        "href": "https://www.notion.so/" + file_id,
                    },
                    {
                        "type": "text",
                        "text": {"content": string_display, "link": None},
                    },
                ]
            }
        }
        req = self.api("Notion").patch.block(block["id"], new_paragraph_block)
        if not req:
            self.logger.error("Error while updating Notion page.")
            raise Exception("Error while updating Notion page.")

    def _update_and_log_failure(self, file, blocks, index, failure, errmsg):
        self.update_notion(False, file, blocks[index], errmsg)
        failure += 1
        return failure

    def _process_file(self, file, blocks, index, failure):
        param_dict = self.get_markdown(file)
        if param_dict is None:
            return self._update_and_log_failure(
                file,
                blocks,
                index,
                failure,
                "The markdown header is badly formatted.",
            )

        process, title = self.compile(file, param_dict)
        if not process and title is None:
            return self._update_and_log_failure(
                file, blocks, index, failure, "The compilation failed."
            )

        self.update_notion(True, file, blocks[index])
        return failure

    def job(self) -> "application.Status":
        """
        Perform the SyncNotion job.

        This method starts the job by setting the status to "RUNNING."
        It then sets the status to "SUCCESS" and logs the job finished with the current status.

        :return: 'application.Status': The status of the job indicating whether it was
        successful or not.
        """
        self.logger.debug("Notion to LaTeX conversion started.")
        self.get_template()
        files, blocks = self.get_files()

        if files is None:
            return application.Status.ERROR

        failure = 0
        for index, file in enumerate(files):
            failure = self._process_file(file, blocks, index, failure)

        str_msg = f"Notion LaTeX compiled {len(files) - failure} files."
        self.logger.debug(str_msg)

        if failure == len(files):
            return application.Status.ERROR
        else:
            return application.Status.SUCCESS

    @staticmethod
    def get_artifact_suites_url(user, repo, token):
        """
        :param user: A string representing the username or organization name on GitHub.
        :param repo: A string representing the repository name on GitHub.
        :param token: A string representing the access token for authentication with GitHub API.

        :return: A string representing the URL of the artifact suites for the given repository.
        """
        headers = {"Authorization": "token " + token}

        workflows = requests.get(
            f"https://api.github.com/repos/{user}/{repo}/actions/workflows",
            headers=headers,
        ).json()
        workflow_id = workflows["workflows"][0]["id"]
        runs = requests.get(
            f"https://api.github.com/repos/{user}/{repo}/actions/workflows/"
            f"{workflow_id}/runs",
            headers=headers,
        ).json()
        if runs["workflow_runs"]:
            run_id = runs["workflow_runs"][0]["id"]
            run_details = requests.get(
                f"https://api.github.com/repos/{user}/"
                f"{repo}/actions/runs/{run_id}",
                headers=headers,
            ).json()
            try:
                print(run_details["html_url"])
                return run_details["html_url"]
            except KeyError:
                return None
        return None

    def artifact_link_notion(self, link):
        """
        :param link: The link to the artifact that needs to be added to the Notion page.
        :return: Returns True if the Notion page is successfully updated with the artifact link.
        """
        req = self.api("Notion").patch.block(
            "bdff6e80184641609564996d70c8d3fc",
            {
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "Artifacts at "
                                + time.strftime(
                                    "%d/%m/%Y %H:%M:%S", time.localtime()
                                ),
                                "link": {"url": link},
                            },
                        },
                    ]
                }
            },
        )
        if req.status_code != 200:
            self.logger.error(
                "Failed to update Notion page with artifact link."
            )
            self.logger.error(req.data)
            return False
        return True


def main():
    """

    This is the documentation for the method main().

    :returns: None
    """
    __import__("wolf_core.api")
    __import__("wolf.notion")
    app = Notion2Latex()
    result = app.job()
    app.logger.debug("Notion LaTeX finished with status: " + result.name)


def post_run():
    """
    This method, `post_run`, is used to perform certain actions after the main execution of a
    program.
    It is responsible for importing necessary modules, initializing an instance of the
    `Notion2Latex` class,
    loading a token from a JSON file, and calling specific methods of the `Notion2Latex` class.

    :return: None
    """
    __import__("wolf_core.api")
    __import__("wolf.notion")
    app = Notion2Latex()
    with open("token.json") as file:
        token = json.load(file)["github"]
    link = app.get_artifact_suites_url("sedelpeuch", "wolf", token)
    app.artifact_link_notion(link)


if __name__ == "__main__":
    post_run()
