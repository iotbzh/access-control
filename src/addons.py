from src.git import Git
from src.gateways import Gateways
from src.plugins import Plugins
from src.models import db, dbs, Addon

import shutil
from pathlib import Path
import os
import glob
import subprocess

class Addons:

    @staticmethod
    def import_new(url, app):
        Git.clone(url, ".addons")
        repo_name = url.split("/")[-1].split(".")[0]

        # This should be executed with app context
        dbs.add(Addon(uid=repo_name, git_url=url))
        dbs.commit()

        # Get all subfolders of gateways and plugins from the git repo
        # And create symlink, no need to import them, the server should be restarting instead
        for src in glob.glob(f".addons/{repo_name}/gateways/*"):
            module_name = os.path.basename(src)
            if not os.path.exists(f"gateways/{module_name}"):
                subprocess.run(["ln", "-s", f"../{src}", module_name], cwd="gateways")

        for src in glob.glob(f".addons/{repo_name}/plugins/*"):
            module_name = os.path.basename(src)
            if not os.path.exists(f"plugins/{module_name}"):
                subprocess.run(["ln", "-s", f"../{src}", module_name], cwd="plugins")

    @staticmethod
    def update(uid):
        # Git pull in the repo folder
        Git.pull(f".addons/{uid}")
    
    @staticmethod
    def remove(uid):
        dbs.execute(db.delete(Addon).where(Addon.uid == uid))
        dbs.commit()

        # Dont raise error if cannot remove
        # Should send message to logger
        def safe_remove(path):
            try: os.remove(path)
            except: pass

        # Remove all symlinks
        for src in glob.glob(f".addons/{uid}/gateways/*"):
            safe_remove(f"gateways/{os.path.basename(src)}")
        for src in glob.glob(f".addons/{uid}/plugins/*"):
            safe_remove(f"plugins/{os.path.basename(src)}")
        
        # Remove cloned repo
        shutil.rmtree(f".addons/{uid}", ignore_errors=True)