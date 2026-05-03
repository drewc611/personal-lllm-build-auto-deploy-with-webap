import os
import subprocess
import sys


def main():
    repo_path = os.path.join(os.path.dirname(__file__), 'nanoGPT')
    if os.path.isdir(repo_path):
        print('nanoGPT is already present in this repository.')
        return

    print('Cloning nanoGPT repository into ./nanoGPT...')
    try:
        subprocess.run(['git', 'clone', 'https://github.com/karpathy/nanoGPT.git', 'nanoGPT'], check=True)
        print('nanoGPT clone complete.')
    except subprocess.CalledProcessError:
        print('Failed to clone nanoGPT. Ensure git is installed and the network is reachable.')
        sys.exit(1)


if __name__ == '__main__':
    main()
