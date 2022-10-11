#!/bin/python

####
# Designed for use with https://github.com/AUTOMATIC1111/stable-diffusion-webui
# Run this file from the root of the repo
#
# Updated by saber7ooth#7527 for more download reliability and filesystem
# auto-correction, as well as read from embeddings-config.json on run.  You
# can now configure pre-run or keep tabs daily as the json file is updated
# correctly based upon the state of the huggingface repo.
#
# Usage in prompt: Put embedding name in prompt (using moxxi.pt and borderlands.pt)
# e.g. moxxi on a beach, in the style of borderlands sharp, clear lines, detailed
# or
# e.g. <moxxi> on a beach, in the style of <borderlands> sharp, clear lines, detailed
# <> are not required but can be used (and may give better results)
###

import logging
from pydantic import BaseModel
from enum import Enum
from os import remove
import sys
import requests
from requests import get
import os.path
import json
from bs4 import BeautifulSoup
from picklescan.scanner import scan_huggingface_model
import pyclamd
import hashlib
from typing import List

_log = logging.getLogger("sd_embeddings_sync")


class RepoFileType(Enum):
    HFEMBEDDING = 1
    HFIMAGE = 2


class RepoState(Enum):
    ALLOW = 1
    DENY = 2


class RepoFile(BaseModel):
    repo_id: str = ""
    repo_state: int = RepoState.ALLOW
    url: str = ""
    file_name: str = ""
    file_type: RepoFileType = RepoFileType.HFEMBEDDING
    sha256_checksum: str = ""
    md5_checksum: str = ""
    is_pickle_clean: bool = False
    is_accessable: bool = False
    is_non_empty: bool = False
    needs_downloaded: bool = True


class RepoStatus:
    def __init__(self):
        self.skipped_repos: int = 0
        self.failed_repos: int = 0
        self.downloaded_repos: int = 0
        self.already_downloaded_repos: int = 0
        self.downloaded_images: int = 0
        self.failed_images: int = 0
        self.already_downloaded_images: int = 0

    def print_status(self):
        std_out = ""
        if self.downloaded_repos > 0:
            suffix = "" if self.downloaded_repos == 1 else "s"
            std_out += f"Downloaded {self.downloaded_repos} repo{suffix}\n\r"
        if self.already_downloaded_repos > 0:
            suffix = "" if self.already_downloaded_repos == 1 else "s"
            std_out += f"Already downloaded {self.already_downloaded_repos} repo{suffix}\n\r"
        if self.skipped_repos > 0:
            suffix = "" if self.skipped_repos == 1 else "s"
            std_out += f"Skipped {self.skipped_repos} repo{suffix}\n\r"
        if self.downloaded_images > 0:
            suffix = "" if self.downloaded_images == 1 else "s"
            std_out += f"Downloaded {self.downloaded_images} image{suffix}\n\r"
        if self.already_downloaded_images > 0:
            suffix = "" if self.already_downloaded_images == 1 else "s"
            std_out += f"Already downloaded {self.already_downloaded_images} image{suffix}\n\r"
        if self.failed_repos > 0:
            suffix = "" if self.failed_repos == 1 else "s"
            print(f"{self.failed_repos} repo{suffix} failed.")
        if self.failed_images > 0:
            suffix = "" if self.failed_images == 1 else "s"
            print(f"{self.failed_images} image{suffix} failed.")
        print("")
        print("Done.")


class Settings(BaseModel):
    concepts_library_url: str = "https://huggingface.co/sd-concepts-library"
    embedding_config_file: str = "./embeddings/embeddings.json"
    embeddings_dir: str = "./embeddings/"
    embeddings_samples_dir: str = "./embeddings/embeddings_samples/"
    allow_list: List[RepoFile] = List[RepoFile]
    deny_list: List[RepoFile] = List[RepoFile]
    download_images: bool = False
    max_images: int = 4


class SettingsManager:
    def init(self):
        self.settings = Settings()
        self.repo_file_managers = List[RepoFileManager]()
        if not os.path.exists(self.settings.embeddings_dir):
            os.makedirs(self.settings.embeddings_dir)
        if self.settings.download_images:
            if not os.path.exists(self.settings.embeddings_samples_dir):
                os.makedirs(self.settings.embeddings_samples_dir)

    def save(self):
        with open(self.settings.embedding_config_file, "w") as file:
            file.write(self.settings.json(models_as_dict=False))

    def load(self):
        self.repo_file_managers.clear()
        if not os.path.exists(self.settings.embedding_config_file):
            self.save()
        with open(self.settings.embedding_config_file, "r") as file:
            self.settings = Settings.parse_raw(json.loads(file.read()))
            for item in self.settings.allow_list:
                self.repo_file_managers.append(RepoFileManager(item))
            for item in self.settings.deny_list:
                self.repo_file_managers.append(RepoFileManager(item))

    # Search in allow list is by repo_id
    def in_allow(self, allow):
        return [item for item in self.repo_file_managers if item.repo_file.repo_id == allow and item.repo_file.repo_state == RepoState.ALLOW] is not None

    # Search in deny list is by repo_id
    def in_deny(self, deny):
        return [item for item in self.repo_file_managers if item.repo_file.repo_id == deny and item.repo_file.repo_state == RepoState.DENY] is not None

    # Add allow item to list
    def add_allow(self, allow):
        self.settings.allow_list.append(allow)
        self.repo_file_managers.append(RepoFileManager(allow))

    # Delete allow item from list
    def del_allow(self, allow):
        self.settings.allow_list.remove(allow)
        self.repo_file_managers = List([item for item in self.repo_file_managers if not item.repo_file != allow])

    # Add deny item to list
    def add_deny(self, deny):
        self.settings.deny_list.append(deny)
        self.repo_file_managers.append(RepoFileManager(deny))

    # Delete deny item from list
    def del_deny(self, deny):
        self.settings.deny_list.remove(deny)
        self.repo_file_managers = List([item for item in self.repo_file_managers if not item.repo_file != deny])


class RepoFileManager:
    def __init__(self, repo_file):
        self.repo_file = repo_file

    def sync(self):
        # Check make sure URL accessable.
        self.repo_file.url = self.get_url()
        self.repo_file.is_accessable = self.url_exists()
        if self.repo_file.is_accessable is False:
            return False
        # Check file does not exist.
        self.repo_file.needs_downloaded = not self.file_exists()
        # Check file size is empty.
        if self.repo_file.needs_downloaded is False:
            self.repo_file.file_size = os.path.getsize(self.repo_file.file_name)
            self.repo_file.is_non_empty = self.repo_file.file_size != 0
            if self.repo_file.is_non_empty is False:
                self.repo_file.needs_downloaded = True
        # Check sha256 and md5 checksum don't match entry
        if self.repo_file.needs_downloaded is False:
            self.repo_file.needs_downloaded = (
                not self.repo_file.md5_checksum == hashlib.md5(open(self.repo_file.file_name, "rb").read()).hexdigest()
                or not self.repo_file.sha256_checksum == hashlib.sha256(open(self.repo_file.file_name, "rb").read()).hexdigest()
            )
        # Check no pickle infections
        if self.repo_file.needs_downloaded is False:
            self.is_pickle_clean = scan_huggingface_model(self.repo_file.repo_id).infected_files == 0
            if not self.is_pickle_clean:
                remove(self.repo_file.file_name)
                return False
        # Download the file if need to
        if self.repo_file.needs_downloaded is True:
            if self.file_exists() is True:
                remove(self.repo_file.file_name)
            with open(self.repo_file.file_name, "wb") as file:
                response = get(self.repo_file.url)
                file.write(response.content)
        # Ensure file exists
        if not self.repo_file.file_exists():
            return False
        # Ensure no pickle malware
        self.repo_file.is_pickle_clean = scan_huggingface_model(self.repo_file.repo_id).infected_files == 0
        if not self.repo_file.is_pickle_clean:
            remove(self.repo_file.file_name)
            return False
        # Ensure checksum data
        self.repo_file.md5_checksum = hashlib.md5(open(self.repo_file.file_name, "rb").read()).hexdigest()
        self.repo_file.sha256_checksum = hashlib.sha256(open(self.repo_file.file_name, "rb").read()).hexdigest()

    def url_exists(self):
        response = get(self.repo_file.url)
        if response.status_code == 200:
            return True
        else:
            return False

    def file_exists(self):
        return os.path.isfile(self.repo_file.file_name)

    def get_url(self):
        if self.repo_file.file_type == RepoFileType.HFEMBEDDING:
            return f"https://huggingface.co/{self.repo_file.repo_id}/resolve/main/learned_embeds.bin"
        if self.repo_file.file_type == RepoFileType.HFIMAGE:
            n = os.path.basename(str(self.repo_file.file_name))
            return f"https://huggingface.co/{self.repo_file.repo_id}/resolve/main/concept_images/{n}"


class RepoManager:
    def __init__(self):
        self.settings_manager = SettingsManager()
        self.settings_manager.init()
        self.settings_manager.load()
        self.repo_status = RepoStatus()

    def load_concepts_library(self):
        print("Loading latest embedding repository list")
        sys.stdout.flush()
        page = requests.get(self.settings_manager.settings.concepts_library_url)
        soup = BeautifulSoup(page.content, "html.parser")
        soup_models = soup.find(id="models")
        soup_parent = soup_models.parent
        soup_data = soup_parent["data-props"]
        soup_data_json = json.loads(soup_data)
        soup_repos = soup_data_json["repos"]
        repo_count = len(soup_repos)
        repo_suffix = "" if repo_count == 1 else "s"
        print(f"Found {repo_count} repo{repo_suffix}")
        print("")
        sys.stdout.flush()
        for item in soup_repos:
            if (not self.settings_manager.in_allow(item)) and (not self.settings_manager.in_deny(item)):
                self.settings_manager.add_allow(item)

    def test_pyclamd():
        try:
            cd = pyclamd.ClamdUnixSocket()
            cd.ping()
            return True
        except pyclamd.ConnectionError:
            cd = pyclamd.ClamdNetworkSocket()
            try:
                cd.ping()
                return True
            except pyclamd.ConnectionError:
                return False

    def sync_all(self):
        self.load_concepts_library()
        for repo in self.settings_manager.settings.allow_list:
            print(f"Processing {repo.repo_id}...")

        self.settings_manager.save()
