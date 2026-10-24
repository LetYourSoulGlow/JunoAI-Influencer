"""Plain-text (UTF-8) version of 'The Silence I Come From' for pasting into a publisher's editor.

Usage: python3 build_txt_en.py <translation_en.json> <out.txt>
One blank line between paragraphs, a marker line before each chapter, no formatting.
"""
import sys, re, json

src, out = sys.argv[1], sys.argv[2]
tr = json.load(open(src))
paras = [''] * (max(map(int, tr)) + 2)
for k, v in tr.items(): paras[int(k)] = v.strip()

MARK = '=' * 40
lines = [
    'Joanna Dorobisz', '', 'THE SILENCE I COME FROM', 'Coming Back to Who You Truly Are', '', MARK, '',
    'Copyright © Joanna Dorobisz',
    'Translated from the Polish "Cisza, z której pochodzę".',
    'All rights reserved. No part of this book may be reproduced or distributed without the author’s written permission, except for brief quotations in reviews.',
    'This book is not a substitute for therapy or professional help. If you are experiencing abuse or are in crisis, please contact a professional or a local helpline.',
    'Let Your Soul Glow · letyoursoulglow.net/eng',
]
blocks = ['\n\n'.join(lines[:5]), '\n\n'.join(lines[7:])]
# blocks are joined by a blank line; bullet runs stay together on consecutive lines
ul = []
def flush():
    global ul
    if ul: blocks.append('\n'.join('• ' + x for x in ul))
    ul = []

n = 0
for i, t in enumerate(paras):
    if i == 0 or not t:
        flush(); continue
    if t.startswith('•'):
        ul.append(t.lstrip('•').strip()); continue
    flush()
    m = re.match(r'^Chapter\s+(\d+):\s*(.+)$', t)
    if m or t.startswith('Conclusion:') or t == 'Epilogue':
        if m: head = f'CHAPTER {m.group(1)}\n{m.group(2)}'
        elif t == 'Epilogue': head = 'EPILOGUE'
        else: head = 'CONCLUSION\n' + t.split(':', 1)[1].strip()
        blocks.append(f'\n{MARK}\n{head}\n{MARK}'); n += 1; continue
    blocks.append(t)
flush()
open(out, 'w', encoding='utf-8').write('\n\n'.join(blocks).replace('\n\n\n' + MARK, '\n\n' + MARK) + '\n')
print('chapters:', n)
