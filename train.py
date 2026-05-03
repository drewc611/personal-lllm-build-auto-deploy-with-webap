import argparse
import os
import subprocess
import sys


def ensure_nanogpt():
    if os.path.isdir('nanoGPT'):
        return
    print('nanoGPT directory not found. Cloning from GitHub...')
    subprocess.run(['git', 'clone', 'https://github.com/karpathy/nanoGPT.git', 'nanoGPT'], check=True)


def main():
    parser = argparse.ArgumentParser(description='nanoGPT training starter helper')
    parser.add_argument('--prepare', action='store_true', help='Clone nanoGPT if missing')
    parser.add_argument('--dry-run', action='store_true', help='Print the nanoGPT command without executing')
    parser.add_argument('--dataset', default='data/example_text.txt', help='Training dataset path')
    parser.add_argument('--epochs', default='5', help='Number of training epochs')
    args = parser.parse_args()

    if args.prepare:
        ensure_nanogpt()
        if args.dry_run:
            return

    if not os.path.isdir('nanoGPT'):
        print('nanoGPT directory not found.')
        print('Run `python3 train.py --prepare` to clone it automatically.')
        if args.dry_run:
            return
        sys.exit(1)

    command = [
        sys.executable,
        'nanoGPT/train.py',
        '--device', 'cpu',
        '--compile', 'off',
        '--eval_iters', '20',
        '--log_interval', '10',
        '--block_size', '128',
        '--batch_size', '4',
        '--n_layer', '4',
        '--n_head', '4',
        '--n_embd', '128',
        '--max_iters', args.epochs,
        '--lr_decay_iters', '50',
        '--dropout', '0.0',
        '--dataset', args.dataset
    ]

    print('nanoGPT command:')
    print(' '.join(command))
    if args.dry_run:
        return

    subprocess.run(command, check=True)


if __name__ == '__main__':
    main()
