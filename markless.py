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
_list_bullets = u'*+-'

def _unichr(code):
  s = "\\U%08x" % code
  return s.decode('unicode-escape')

def count_start(input, char):
  count = 0
  for c in input:
    if c == char:
      count += 1
    else:
      return count
  return count


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

def makelist(in_lines, bullet):
  indent = display_len(bullet)
  joiner = '\n' + ('|' * indent)
  return bullet + joiner.join(in_lines) + '\n'

def makequote(in_lines, mark):
  return mark + ('\n' + mark).join(in_lines) + '\n'

def is_list_start(line):
  line = line.strip()
  for bullet in _list_bullets:
    if line.startswith(bullet):
      return True
  return False

def _emphasis(text, emphasis_char):
  for char in text:
    yield char
    if char.isalnum():
      yield emphasis_char

def emphasis(text, emphasis_char):
  inner = process_run(text)
  return ''.join(_emphasis(inner, emphasis_char))

def emphasis_runs(input, splitter, emphasis_char):
  runs = input.split(splitter)
  parts = []
  for index, run in enumerate(runs):
    if index % 2:
      parts.append(emphasis(run, emphasis_char))
    else:
      parts.append(process_run(run))
  return ''.join(parts)

def process_run(input):
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
    self.list_lines = []
    self.is_list = False

  def output_text(self, line):
    self.output.write(line.encode(ENCODING))

  def flush_text(self):
    if self.text_lines:
      formatted_lines = map(process_run, self.text_lines)
      self.output_text('\n'.join(formatted_lines))
      self.output_text('\n')
      self.text_lines = []

  def flush_list(self):
    if self.list_lines:
      formatted_lines = map(process_run, self.list_lines)
      self.output_text(makelist(formatted_lines, u'• '))
      self.list_lines = []

  def flush_box(self):
    if self.box_lines:
      self.output_text(makebox(self.box_lines, _box_code))
      self.box_lines = []

  def flush_all(self):
    self.flush_box()
    self.flush_text()
    self.flush_list()
    self.is_list = False

  def process_lines(self, lines):
    for line in lines:
      if not line.strip():
        self.flush_all()
        continue
      start_hash = count_start(line, '#')
      if start_hash:
        self.flush_all()
        content = process_run(line[start_hash:].strip())
        if start_hash == 1:
          self.output_text(makebox([content], _box_double))
        elif start_hash == 2:
          self.output_text(makebox([content], _box_heavy))
        else:
          self.output_text(makebox([content], _box_light))
        self.output_text('\n')
        continue
      start_greater = count_start(line, '>')
      if start_greater:
        self.flush_all()
        prefix = u'▌' * start_greater
        self.output_text(makequote([line[start_greater:].strip()], prefix))
        continue
      if line.startswith('    '):
        self.flush_text()
        self.flush_list()
        self.box_lines.append(line[4:].rstrip())
        continue
      self.flush_box()
      if is_list_start(line):
        self.flush_all()
        self.is_list = True
        self.list_lines.append(line[1:].strip())
        continue
      if self.is_list:
        self.list_lines.append(line.strip())
        continue
      self.text_lines.append(line.strip())
    # Flush everything
    self.flush_all()

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
