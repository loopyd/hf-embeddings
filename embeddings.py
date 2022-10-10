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

from dataclasses import dataclass
from enum import Enum
from os import remove
import re
import sys
from xmlrpc.client import boolean
import requests
from requests import get
import os.path
import json
import time
from bs4 import BeautifulSoup
from picklescan.scanner import scan_huggingface_model
import pyclamd
import hashlib

class RepoFileType(Enum):
    EMBEDDING = 1
    IMAGE = 2

@dataclass
class RepoFile:
    repo_id: str
    url: str
    file_name: str
    file_type: RepoFileType
    sha256_checksum: str
    md5_checksum: str
    is_pickle_clean: bool
    is_accessable: bool
    is_non_empty: bool
    needs_downloaded: bool

    def sync(self):
        # Check make sure URL accessable.
        self.url = self.get_url()
        self.is_accessable = self.url_exists()
        if self.is_accessable == False:
            return False
        # Check file does not exist.
        self.needs_downloaded = not self.file_exists()
        # Check file size is empty.
        if self.needs_downloaded == False:
            self.file_size = os.path.getsize(self.file_name)
            self.is_non_empty = (self.file_size != 0)
            if self.is_non_empty == False:
                self.needs_downloaded = True
        # Check sha256 and md5 checksum don't match entry
        if self.needs_downloaded == False:
            self.needs_downloaded = ( not self.md5_checksum == hashlib.md5(open(self.file_name,'rb').read()).hexdigest() or not self.sha256_checksum == hashlib.sha256(open(self.file_name,'rb').read()).hexdigest() )
        # Check no pickle infections
        if self.needs_downloaded == False:
            self.is_pickle_clean = (scan_huggingface_model(self.repo_id).infected_files == 0)
            if not self.is_pickle_clean:
                remove(self.file_name)
                return False
        # Download the file if need to
        if self.needs_downloaded == True:
            if self.file_exists() == True:
                remove(self.file_name)
            with open(self.file_name, "wb") as file:
                response = get(self.url)
                file.write(response.content)
        # Ensure file exists
        if not self.file_exists():
            return False
        # Ensure no pickle malware
        self.is_pickle_clean = (scan_huggingface_model(self.repo_id).infected_files == 0)
        if not self.is_pickle_clean:
            remove(self.file_name)
            return False
        # Ensure checksum data
        self.md5_checksum = hashlib.md5(open(self.file_name,'rb').read()).hexdigest()
        self.sha256_checksum = hashlib.sha256(open(self.file_name,'rb').read()).hexdigest()

    def url_exists(self):
        response = get(self.url)
        if response.status_code == 200:
            return True
        else:
            return False

    def file_exists(self):
        return os.path.isfile(self.file_name) 
    
    def get_url(self):
        if self.file_type == RepoFileType.EMBEDDING:
            return f"https://huggingface.co/{self.repo_id}/resolve/main/learned_embeds.bin"
        if self.file_type == RepoFileType.IMAGE:
            return f"https://huggingface.co/{self.repo_id}/resolve/main/concept_images/{n}.jpeg"

def save_settings(my_settings):
    with open('embeddings-config.json', "w") as file:
        file.write(json.dumps(my_settings))

def load_settings():
    if not os.path.exists('embeddings-config.json'):
        settings = dict(
            concepts_library_url='https://huggingface.co/sd-concepts-library',
            embeddings_dir='./embeddings/',
            embeddings_samples_dir='./embeddings_samples/',
            allow_list=[],
            deny_list=[],
            download_images=False,
            max_images=4
        )
        save_settings(settings)
    data = dict()
    with open('embeddings-config.json', "r") as file:
        data = json.loads(file.read())
    return data

def append_unique(arr, element):
    if element not in arr:
        arr.append(element)
    return arr

def get_concepts_library():
    print(f"Loading latest embedding repository list")
    sys.stdout.flush()
    page = requests.get(settings['concepts_library_url'])
    soup = BeautifulSoup(page.content, "html.parser")
    soup_models = soup.find(id="models")
    soup_parent = soup_models.parent
    soup_data = soup_parent['data-props']
    soup_data_json = json.loads(soup_data)
    soup_repos=soup_data_json["repos"]
    repo_count=len(soup_repos)
    repo_suffix=("" if repo_count == 1 else "s")
    print(f"Found {repo_count} repo{repo_suffix}")
    print(f"")
    sys.stdout.flush()
    return soup_repos

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

settings = load_settings()

if not os.path.exists(settings['embeddings_dir']):
    os.makedirs(settings['embeddings_dir'])

if settings['download_images']:
    if not os.path.exists(settings['embeddings_samples_dir']):
        os.makedirs(settings['embeddings_samples_dir'])

repos = get_concepts_library()
status = dict(
    skipped_repos=0,
    failed_repos=0,
    downloaded_repos=0,
    already_downloaded_repos=0,
    downloaded_images=0,
    failed_images=0,
    already_downloaded_images=0
)
for repo in repos:
    repo_id=repo["id"].replace("sd-concepts-library/","")
    if len(settings['allow_list']) > 0 and repo_id not in settings['allow_list']:
        status['skipped_repos']=status['skipped_repos']+1
        continue
    if len(settings['deny_list']) > 0 and repo_id in settings['deny_list']:
        status['skipped_repos']=status['skipped_repos']+1
        continue
    print(f"Processing {repo_id}")
    sys.stdout.flush()
    url=get_url_for_learned_embeddings(repo_id)
    filename=f"{settings['embeddings_dir']}{repo_id}.bin"
    if file_exists(filename) and os.path.getsize(filename) == 0:
        os.remove(filename)
    if not file_exists(filename):
        print(f"  > Downloading {url} to {filename}")
        sys.stdout.flush()
        download_result = download(url,filename, repo_id)
        if download_result == False:
            print(f"  > Check for {filename} failed, added {repo_id} to deny list.")
            os.remove(filename)
            settings['deny_list'] = append_unique(settings['deny_list'], repo_id)
            status['failed_repos']=status['failed_repos']+1
            sys.stdout.flush()
        else:
            status['downloaded_repos']=status['downloaded_repos']+1
    else:
        print(f"  > Already downloaded")
        status['already_downloaded_repos']=status['already_downloaded_repos']+1
        sys.stdout.flush()
    if settings["download_images"] == True:
        img_id=0
        no_more_images=False
        while not no_more_images:
            time.sleep(0.1)
            url=get_url_for_image_sample(repo_id, img_id)
            filename=f"{settings['embeddings_samples_dir']}{repo_id}.{img_id}.jpeg"
            if file_exists(filename):
                print(f"  > Already downloaded {img_id}.jpeg")
                status['already_downloaded_images']=status['already_downloaded_images']+1
                sys.stdout.flush()
            else:
                if url_exists(url):
                    if not file_exists(filename):
                        print(f"  > Downloading {img_id}.jpeg to {filename}")
                        sys.stdout.flush()
                        download_result = download(url, filename, repo_id)
                        if download_result == False:
                            print(f"  > Check for {filename} failed, cleansed file")
                            os.remove(filename)
                            sys.stdout.flush()
                            status['failed_images']=status['failed_images']+1
                        else:
                            status['downloaded_images']=status['downloaded_images']+1
                else:
                    no_more_images=True
            img_id=img_id+1
            if img_id >= settings['max_images']:
                no_more_images=True

save_settings(settings)

# This prints output.
if status["downloaded_repos"] > 0:
    suffix=("" if status['downloaded_repos'] == 1 else "s")
    print(f"Downloaded {status['downloaded_repos']} repo{suffix}")
if status["already_downloaded_repos"] > 0:
    suffix=("" if status['already_downloaded_repos'] == 1 else "s")
    print(f"Already downloaded {status['already_downloaded_repos']} repo{suffix}")
if status["skipped_repos"] > 0:
    suffix=("" if status['skipped_repos'] == 1 else "s")
    print(f"Skipped {status['skipped_repos']} repo{suffix}")

if settings["download_images"] == True:
    if status["downloaded_images"] == True:
        suffix=("" if status['downloaded_images'] == 1 else "s")
        print(f"Downloaded {status['downloaded_images']} image{suffix}")
    if status["already_downloaded_images"] == True:
        suffix=("" if status['already_downloaded_images'] == 1 else "s")
        print(f"Already downloaded {status['already_downloaded_images']} image{suffix}")

if status['failed_repos'] > 0:
    suffix=("" if status['failed_repos'] == 1 else "s")
    print(f"{status['failed_repos']} repo{suffix} failed.")
if status['failed_images'] > 0:
    suffix=("" if status['failed_images'] == 1 else "s")
    print(f"{status['failed_images']} image{suffix} failed.")
print("")
print("Done.")
