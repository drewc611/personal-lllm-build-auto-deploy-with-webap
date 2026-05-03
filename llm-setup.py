import argparse
import subprocess
import sys


def run_command(command, description):
    print(f"\n> {description}")
    print(' '.join(command))
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError:
        print(f"Command failed: {' '.join(command)}")
        sys.exit(1)


def setup_gpt():
    run_command(['ollama', 'pull', 'llama3.1:8b-instruct-q4_K_M'], 'Pull the Ollama Llama 3.1 model')
    print('Model pull complete. To interact, run: ollama run llama3.1:8b-instruct-q4_K_M')


def run_gpt():
    print('Launching local GPT. This may be interactive.')
    subprocess.run(['ollama', 'run', 'llama3.1:8b-instruct-q4_K_M'])


def setup_lora():
    run_command([sys.executable, 'fine_tune_lora.py'], 'Run the LoRA fine-tuning template')


def setup_nanogpt():
    run_command([sys.executable, 'train.py'], 'Run the nanoGPT training starter script')


def main():
    parser = argparse.ArgumentParser(description='Personal LLM deployment CLI')
    parser.add_argument('--gpt', action='store_true', help='Install or run the local GPT model')
    parser.add_argument('--lora', action='store_true', help='Run the LoRA fine-tuning workflow')
    parser.add_argument('--nanogpt', action='store_true', help='Run the nanoGPT training workflow')
    parser.add_argument('--all', action='store_true', help='Run all deployment steps in sequence')
    args = parser.parse_args()

    if args.all:
        setup_gpt()
        setup_lora()
        setup_nanogpt()
        return

    if args.gpt:
        setup_gpt()
    elif args.lora:
        setup_lora()
    elif args.nanogpt:
        setup_nanogpt()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
