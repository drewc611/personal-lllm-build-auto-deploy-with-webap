import mailbox
import os
import re
from pathlib import Path


def sanitize_name(name: str) -> str:
    name = re.sub(r'[^a-zA-Z0-9_\- ]', '_', name)
    name = re.sub(r'\s+', '_', name).strip('_')
    return name[:120] or 'email'


def get_body(message):
    if message.is_multipart():
        parts = []
        for part in message.walk():
            content_type = part.get_content_type()
            if content_type == 'text/plain' and not part.get('Content-Disposition'):
                payload = part.get_payload(decode=True)
                try:
                    parts.append(payload.decode(part.get_content_charset() or 'utf-8', errors='replace'))
                except Exception:
                    parts.append(str(payload))
        return '\n'.join(parts).strip()
    payload = message.get_payload(decode=True)
    if payload is None:
        return ''
    try:
        return payload.decode(message.get_content_charset() or 'utf-8', errors='replace')
    except Exception:
        return str(payload)


def convert_mbox(mbox_path: str, output_dir: str):
    mailbox_path = Path(mbox_path)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    mbox = mailbox.mbox(str(mailbox_path))
    count = 0

    for idx, message in enumerate(mbox):
        subject = message.get('subject', 'no-subject')
        filename = f"{idx:04d}_{sanitize_name(subject)}.txt"
        file_path = output_path / filename

        headers = []
        for header in ('From', 'To', 'Cc', 'Date', 'Subject'):
            value = message.get(header)
            if value:
                headers.append(f"{header}: {value}")

        body = get_body(message)
        content = '\n'.join(headers) + '\n\n' + body

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content.strip() + '\n')
        count += 1

    print(f"Converted {count} email messages into {output_path}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Convert Gmail MBOX export to individual text files')
    parser.add_argument('mbox_path', help='Path to the source .mbox file')
    parser.add_argument('output_dir', help='Directory to write individual email text files')
    args = parser.parse_args()

    convert_mbox(args.mbox_path, args.output_dir)
