import shutil
import tempfile
from contextlib import contextmanager


import os


from invoke import task


PATH_TO_HERE = os.path.dirname(os.path.abspath(__file__))

PATH_TO_PACKAGE = os.path.join(PATH_TO_HERE, "aiwebscraper")
PATH_TO_APP = os.path.join(PATH_TO_HERE, "app")


@contextmanager
def temporary_directory_copy(source_path, target_path):
    temp_dir_name = os.path.basename(source_path)
    temp_dir_path = os.path.join(target_path, temp_dir_name)

    try:
        shutil.copytree(source_path, temp_dir_path)
        yield temp_dir_path
    finally:
        shutil.rmtree(temp_dir_path)


def read_dotenv(path_to_env_file):
    env_vars = {}

    if os.path.exists(path_to_env_file):
        with open(path_to_env_file, "r") as env_file:
            for line in env_file:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    env_vars[key] = value

    env_string = " ".join([f"-e {key}={value}" for key, value in env_vars.items()])
    return env_string


env_string = read_dotenv(os.path.join(PATH_TO_APP, ".env"))


@task
def setup(c, version=None):
    """
    Setup dev environment, requires conda
    """
    version = version or "3.12"
    suffix = "" if version == "3.12" else version.replace(".", "")
    env_name = f"aiwebscraper{suffix}"

    c.run(f"conda create --name {env_name} python={version} --yes")
    c.run(
        'eval "$(conda shell.bash hook)" '
        f"&& conda activate {env_name} "
        "&& pip install --editable aiwebscraper[dev]"
        "&& pip install -r requirements.txt"
    )

    print(f"Done! Activate your environment with:\nconda activate {env_name}")


@task
def run(c, build_only=False):
    with c.cd("app"):
        with temporary_directory_copy(PATH_TO_PACKAGE, PATH_TO_APP):
            c.run("docker build -t aiwebscraper .")

        if not build_only:
            print("Server will run on http://localhost:8080")
            c.run(f"docker run -p 8080:80 {env_string} aiwebscraper")


@task
def deploy(c):
    with c.cd("app"):
        with temporary_directory_copy(PATH_TO_PACKAGE, PATH_TO_APP):
            c.run("ploomber-cloud deploy")
