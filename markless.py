#!/usr/bin/python
# -*- coding: utf-8 -*-
# © Matthias Wiesmann

"""
This tool renders simple markdown input as plain text.
Rendering is done by using special Unicode Features.
"""

import os
import re
import sys
import itertools
import unicodedata

ENCODING = 'utf-8'

_box_light =  u'┌─┐│ │└─┘'
_box_double = u'╔═╗║ ║╚═╝'
_box_heavy =  u'┏─┓┃ ┃┗─┛'
_box_code =   u'╭─╮┃ ┃╰─╯'

def _unichr(code):
  s = "\\U%08x" % code
  return s.decode('unicode-escape')

def display_len(input):
  len = 0
  for c in input:
    if unicodedata.category(c) != 'Mn':
      len += 1
  return len

def _makebox(in_lines, box):
  width = max(map(display_len, in_lines))
  yield box[0] + box[1] * (width + 2) + box[2]
  for line in in_lines:
    l = display_len(line)
    yield box[3] + box[4] + line + box[4] * (width - l + 1) + box[5]
  yield box[6] + box[7] * (width + 2) + box[8]

def makebox(in_lines, box):
  return '\n'.join(_makebox(in_lines, box))

def _emphasis(text, emphasis_char):
  for char in text:
    yield char
    if char.isalnum():
      yield emphasis_char

def emphasis(text, emphasis_char):
  inner = process_block(text)
  return ''.join(_emphasis(inner, emphasis_char))

def emphasis_runs(input, splitter, emphasis_char):
  runs = input.split(splitter)
  parts = []
  for index, run in enumerate(runs):
    if index % 2:
      parts.append(emphasis(run, emphasis_char))
    else:
      parts.append(process_block(run))
  return ''.join(parts)

def process_block(input):
  if input.startswith('###'):
    return makebox([process_block(input[3:].strip())], _box_light)
  if input.startswith('##'):
    return makebox([process_block(input[2:].strip())], _box_heavy)
  if input.startswith('#'):
    return makebox([process_block(input[1:].strip())], _box_double)
  # List
  if input.startswith('*') or input.startswith('+') or input.startswith('-'):
    return u'•' + process_block(input[1:])
  # Blockquote
  if input.startswith('>>'):
    return u'█' + process_block(input[2:])
  if input.startswith('>'):
    return u'▌' + process_block(input[1:])
  # Emphasis
  if input.find('___') >= 0:
    return emphasis_runs(input, '___', _unichr(0x0333))
  if input.find('__') >= 0:
    return emphasis_runs(input, '__', _unichr(0x0332))
  if input.find('_') >= 0:
    return emphasis_runs(input, '_', _unichr(0x20E8))
  return input

class Processor:
  def __init__(self, output):
    self.output = output
    self.box_lines = []
    self.text_lines = []

  def output_line(self, line):
    self.output.write(line.encode(ENCODING))

  def flush_text(self):
    if self.text_lines:
      for line in self.text_lines:
        self.output_line(process_block(line))
      self.output_line('\n')
      self.text_lines = []

  def flush_box(self):
    if self.box_lines:
      self.output_line(makebox(self.box_lines, _box_code))
      self.box_lines = []

  def process_lines(self, lines):
    for line in lines:
      if line.startswith('    '):
        self.flush_text()
        self.box_lines.append(line[4:].rstrip())
        continue
      self.flush_box()
      self.text_lines.append(line)
    # Flush everything
    self.flush_box()
    self.flush_text()

  def process(self, input_file):
    lines = itertools.imap(lambda l : l.decode(ENCODING), input_file)
    self.process_lines(lines)

def process(input_file, output_file):
  processor = Processor(output_file)
  processor.process(input_file)

def main(argv):
  try:
    if argv:
      input_file = open(argv[0])
    else:
      input_file = sys.stdin
    if len(argv) >= 2:
      output_file = open(argv[1], 'w')
    else:
      output_file = sys.stdout
    process(input_file, output_file)
  except IndexError:
    sys.stderr.write('Error please specify input file\n')
    sys.exit(os.EX_USAGE)
  except IOError:
    sys.stderr.write('Could not read file %r\n' % argv[0])
    sys.exit(os.EX_DATAERR)


if __name__ == "__main__":
    main(sys.argv[1:])
