import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def validate_data(data_path):
    if not os.path.exists(data_path):
        raise FileNotFoundError(f'Data file not found: {data_path}')

    count = 0
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                raise ValueError(f'Invalid JSONL line: {line}')
            if 'prompt' not in item or 'completion' not in item:
                raise ValueError('Each record must include prompt and completion fields.')
            count += 1
    return count


def chunk_text(text, max_chars=4000):
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    chunks = []
    current = ''
    for paragraph in paragraphs:
        if len(current) + len(paragraph) + 2 <= max_chars:
            current = f'{current}\n\n{paragraph}'.strip()
        else:
            if current:
                chunks.append(current)
            if len(paragraph) <= max_chars:
                current = paragraph
            else:
                for i in range(0, len(paragraph), max_chars):
                    chunks.append(paragraph[i:i + max_chars].strip())
                current = ''
    if current:
        chunks.append(current)
    return chunks


def prepare_jsonl_from_dir(sample_dir, output_path, prompt_template, max_chars):
    sample_dir = Path(sample_dir)
    if not sample_dir.exists() or not sample_dir.is_dir():
        raise FileNotFoundError(f'Writing sample directory not found: {sample_dir}')

    files = list(sample_dir.rglob('*.md')) + list(sample_dir.rglob('*.txt'))
    if not files:
        raise FileNotFoundError(f'No .md or .txt files found in {sample_dir}')

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0

    with output_path.open('w', encoding='utf-8') as out:
        for path in files:
            text = path.read_text(encoding='utf-8').strip()
            if not text:
                continue
            for chunk in chunk_text(text, max_chars=max_chars):
                prompt = prompt_template.replace('{text}', chunk)
                item = {'prompt': prompt, 'completion': chunk}
                out.write(json.dumps(item, ensure_ascii=False) + '\n')
                count += 1

    print(f'Prepared {count} examples from {len(files)} files into {output_path}')
    return output_path


def run_lora_training(model, data_path, output_path, epochs, lora_r, lora_alpha, lora_dropout, dry_run):
    command = [
        sys.executable,
        '-m',
        'mlx_lm.train',
        '--model',
        model,
        '--data',
        str(data_path),
        '--output',
        str(output_path),
        '--epochs',
        str(epochs),
        '--lora-r',
        str(lora_r),
        '--lora-alpha',
        str(lora_alpha),
        '--lora-dropout',
        str(lora_dropout),
    ]

    print('LoRA training command:')
    print(' '.join(command))
    if dry_run:
        return

    subprocess.run(command, check=True)


def main():
    parser = argparse.ArgumentParser(description='LoRA fine-tuning script for a local LLM')
    parser.add_argument('--data', default='data/example_data.jsonl', help='Path to JSONL training data')
    parser.add_argument('--prepare-dir', help='Directory of .md/.txt writing samples to convert into JSONL')
    parser.add_argument('--prompt-template', default='Write the following text in my voice:\n\n{text}', help='Template used to build prompt/completion pairs')
    parser.add_argument('--output', default='llama3.1-lora', help='Output adapter path')
    parser.add_argument('--model', default='llama3.1:8b-instruct-q4_K_M', help='Base model to fine-tune')
    parser.add_argument('--epochs', type=int, default=3, help='Training epochs')
    parser.add_argument('--lora-r', type=int, default=8, help='LoRA rank')
    parser.add_argument('--lora-alpha', type=int, default=16, help='LoRA alpha value')
    parser.add_argument('--lora-dropout', type=float, default=0.1, help='LoRA dropout')
    parser.add_argument('--max-chars', type=int, default=4000, help='Maximum characters per sample chunk')
    parser.add_argument('--train', action='store_true', help='Run LoRA training after preparing data')
    parser.add_argument('--dry-run', action='store_true', help='Print generated commands without executing')
    args = parser.parse_args()

    if args.prepare_dir:
        args.data = prepare_jsonl_from_dir(args.prepare_dir, args.data, args.prompt_template, args.max_chars)

    count = validate_data(args.data)
    print(f'Validated {count} records from {args.data}')

    if args.train:
        run_lora_training(
            args.model,
            args.data,
            args.output,
            args.epochs,
            args.lora_r,
            args.lora_alpha,
            args.lora_dropout,
            args.dry_run,
        )
    else:
        print('\nTo train, rerun with --train.')
        print('Example:')
        print(f'  python3 fine_tune_lora.py --data {args.data} --output {args.output} --train')


if __name__ == '__main__':
    main()
