import subprocess
import sys


def git_pull():
    print('Checking for updates from origin...')
    subprocess.run(['git', 'fetch', '--all'], check=True)
    result = subprocess.run(['git', 'status', '-uno'], capture_output=True, text=True)
    print(result.stdout)
    subprocess.run(['git', 'pull', '--ff-only'], check=True)


def main():
    try:
        git_pull()
    except subprocess.CalledProcessError:
        print('Unable to update repository automatically.')
    print('Running llm-setup process...')
    subprocess.run([sys.executable, 'llm-setup.py', '--all'], check=False)


if __name__ == '__main__':
    main()
