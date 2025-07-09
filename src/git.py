import subprocess

# Remaking a git CLI wrapper because there is not much done with git
class Git:

    @staticmethod
    def run(command, cwd=""):
        subprocess.run(["git"] + command, cwd=cwd)
    
    @staticmethod
    def clone(url, cwd=""):
        Git.run(["clone", url], cwd)
    
    @staticmethod
    def pull(cwd=""):
        Git.run(["pull"], cwd)