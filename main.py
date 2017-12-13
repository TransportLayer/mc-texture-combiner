#!/usr/bin/env python3.6

###############################################################################
#   Minecraft Texture Combiner - Creates a complete texture pack              #
#   Copyright (C) 2017  TransportLayer                                        #
#                                                                             #
#   This program is free software: you can redistribute it and/or modify      #
#   it under the terms of the GNU Affero General Public License as published  #
#   by the Free Software Foundation, either version 3 of the License, or      #
#   (at your option) any later version.                                       #
#                                                                             #
#   This program is distributed in the hope that it will be useful,           #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of            #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             #
#   GNU Affero General Public License for more details.                       #
#                                                                             #
#   You should have received a copy of the GNU Affero General Public License  #
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.     #
###############################################################################

import argparse
import zipfile
import urllib.request
import tempfile
import sys
import os

def pack_textures(assets_path, dst):
    print("Compressing combined pack...")
    pack = zipfile.ZipFile(dst, mode='x')
    for dirname, subdirs, files in os.walk(assets_path):
        for file in files:
            absname = os.path.abspath(os.path.join(dirname, file))
            arcname = f"assets/{absname[len(os.path.abspath(assets_path)) + 1:]}"
            pack.write(absname, arcname)
    pack.close()

def recursive_copy(src, dst, current=[]):
    for filename in os.listdir(f"{src}/{'/'.join(current)}"):
        if os.path.isdir(f"{src}/{'/'.join(current)}/{filename}"):
            current.append(filename)
            os.makedirs(f"{dst}/{'/'.join(current)}/{filename}", exist_ok=True)
            recursive_copy(src, dst, current)
            del(current[-1:])
        elif os.path.isfile(f"{src}/{'/'.join(current)}/{filename}"):
            with open(f"{src}/{'/'.join(current)}/{filename}", "rb") as src_file:
                if os.path.exists(f"{dst}/{'/'.join(current)}/{filename}"):
                    os.remove(f"{dst}/{'/'.join(current)}/{filename}")
                with open(f"{dst}/{'/'.join(current)}/{filename}", "wb") as dst_file:
                    dst_file.write(src_file.read())
        else:
            print(f"Ignoring {dst}/{'/'.join(current)}/{filename} (not a file or directory)")

def get_textures(file, dir):
    print("Extracting...")
    zip = zipfile.ZipFile(file)
    zip_dir = tempfile.TemporaryDirectory(dir=dir)
    zip.extractall(path=zip_dir.name)
    zip.close()

    print("Copying textures...")
    for dirname in ("blockstates", "models", "textures"):
        os.makedirs(f"{dir}/t/assets/minecraft/{dirname}", exist_ok=True)
        recursive_copy(f"{zip_dir.name}/assets/minecraft/{dirname}", f"{dir}/t/assets/minecraft/{dirname}")

    print("Cleaning up extracted files...")
    zip_dir.cleanup()

def get_local_client(path, store):
    print(f"Using local client at {path}...")
    with open(path, "rb") as f:
        store.seek(0, 2)
        store.write(f.read())
        store.seek(0, 2)

def download(version, file):
    url = f"https://s3.amazonaws.com/Minecraft.Download/versions/{version}/{version}.jar"
    sys.stdout.write(f"Downloading Minecraft {version}...")
    sys.stdout.flush()

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36"})
    try:
        with urllib.request.urlopen(req) as r:
            file.seek(0, 2)
            file.write(r.read())
            sys.stdout.write(" Downloaded (")
            sys.stdout.flush()
            file.seek(0, 2)
            print(f"{file.tell()} bytes)")
            file.seek(0, 2)
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}")

def main():
    parser = argparse.ArgumentParser(description="Minecraft Texture Combiner")
    parser.add_argument("-V", "--version", type=str, metavar="VERSION", dest="VERSION", help="minecraft version", action="store", default="1.12", required=False)
    parser.add_argument("-c", "--use-client", dest="USE_CLIENT", help="use .minecraft instead of downloading", action="store_true")
    parser.add_argument("-j", "--jar", type=str, metavar="PATH", dest="CLIENT", help="path to client jar", action="store", default="", required=False)
    parser.add_argument("-p", "--pack", type=str, metavar="PATH", dest="PACK", help="path to texture pack", action="store", required=True)
    parser.add_argument("-o", "--output", type=str, metavar="FILE", dest="FILE", help="new texture pack path", action="store", required=True)
    SETTINGS = vars(parser.parse_args())

    jar_file = tempfile.TemporaryFile()
    work_dir = tempfile.TemporaryDirectory()

    if SETTINGS["USE_CLIENT"]:
        print("WARNING: Automatically finding .minecraft may not work on Windows. You may need to use the -j option instead.")
        get_local_client(os.path.expanduser(f"~/.minecraft/versions/{SETTINGS['VERSION']}/{SETTINGS['VERSION']}.jar"), jar_file)
    elif not SETTINGS["CLIENT"] == "":
        get_local_client(os.path.expanduser(SETTINGS["CLIENT"]), jar_file)
    else:
        download(SETTINGS["VERSION"], jar_file)

    get_textures(jar_file, work_dir.name)
    print("Cleaning up Minecraft jar...")
    jar_file.close()
    print("Loading external texture pack...")
    get_textures(SETTINGS["PACK"], work_dir.name)
    pack_textures(f"{work_dir.name}/t/assets", os.path.expanduser(SETTINGS["FILE"]))
    print("Cleaning up...")
    work_dir.cleanup()

    print("Done.")

if __name__ == "__main__":
    main()
