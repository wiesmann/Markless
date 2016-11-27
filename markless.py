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

def reflow(lines, width):
  block = ' '.join(lines)
  total = 0
  buffer = []
  for word in block.split(' '):
    word_len = display_len(word)
    if word_len + total + len(buffer) > width:
      yield ' '.join(buffer)
      total = 0
      buffer = []
    buffer.append(word)
    total += word_len
  yield ' '.join(buffer)

def _makebox(in_lines, box):
  width = max(map(display_len, in_lines))
  yield box[0] + box[1] * (width + 2) + box[2]
  for line in in_lines:
    l = display_len(line)
    yield box[3] + box[4] + line + box[4] * (width - l + 1) + box[5]
  yield box[6] + box[7] * (width + 2) + box[8]

def makebox(in_lines, box):
  return '\n'.join(_makebox(in_lines, box))

def makelist(in_lines, bullet, width):
  in_lines = tuple(reflow(in_lines, width))
  indent = display_len(bullet)
  joiner = '\n' + (' ' * indent)
  return bullet + joiner.join(in_lines) + '\n'

def makequote(in_lines, mark):
  return mark + ('\n' + mark).join(in_lines) + '\n'

def is_list_start(line):
  line = line.strip()
  for bullet in _list_bullets:
    if line.startswith(bullet):
      return True
  return False

def _emphasis(text, emphasis_char, ):
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
  if input.find('`') >= 0:
    return emphasis_runs(input, '`', _unichr(0x0325))
  return input

def get_columns():
  dimensions = map(int,  os.popen('stty size', 'r').read().split())
  return dimensions[1]

class Processor:
  def __init__(self, columns=None):
    self.box_lines = []
    self.text_lines = []
    self.list_lines = []
    self.is_list = False
    self.buffer = ""
    self.width = columns or get_columns()

  def output_text(self, line):
    self.buffer = self.buffer + line.encode(ENCODING)

  def flush_output(self, output, prepend=None):
    if prepend:
      lines = self.buffer.split('\n')
      lines = map(lambda l : prepend + l, lines)
      self.buffer = '\n'.join(lines)
    output.write(self.buffer)

  def reflow(self, lines):
    return tuple(reflow(lines, self.width))

  def flush_text(self):
    if self.text_lines:
      formatted_lines = map(process_run, self.reflow(self.text_lines))
      self.output_text('\n'.join(formatted_lines))
      self.output_text('\n\n')
      self.text_lines = []

  def flush_list(self):
    if self.list_lines:
      formatted_lines = map(process_run, self.list_lines)
      self.output_text(makelist(formatted_lines, u'• ', self.width - 2))
      self.list_lines = []

  def flush_box(self):
    if self.box_lines:
      self.output_text(makebox(self.box_lines, _box_code))
      self.output_text('\n')
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
        content = self.reflow([process_run(line[start_hash:].strip())])
        if start_hash == 1:
          self.output_text(makebox(content, _box_double))
        elif start_hash == 2:
          self.output_text(makebox(content, _box_heavy))
        else:
          self.output_text(makebox(content, _box_light))
        self.output_text('\n')
        continue
      start_greater = count_start(line, '>')
      if start_greater:
        self.flush_all()
        prefix = u'▌' * start_greater
        self.output_text(makequote([line[start_greater:].strip()], prefix))
        continue
      start_spaces = count_start(line, ' ') + count_start(line, '\t') * 4
      if start_spaces >= 4:
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

def process(input_file, output_file, prefix):
  processor = Processor()
  processor.process(input_file)
  processor.flush_output(output_file, prefix)

def usage(command):
  sys.stderr.write(
      'Usage %s [--prefix <prefix>] [--input <input path>]'
      ' [--output <output path>]' % command)
  sys.exit(os.EX_USAGE)

def main(command, argv):
  prefix = None
  input_path = []
  output_path = None
  arg_role = None
  try:
    for arg in argv:
      if arg_role == 'prefix':
        prefix = arg
        continue
      if arg_role == 'input':
        input_path.append(arg)
        continue
      if arg_role == 'output':
        output_path = arg
        continue
      if arg == '--prefix':
        arg_role = 'prefix'
        continue
      if arg == '--input':
        arg_role = 'input'
        continue
      if arg == '--output':
        arg_role = 'output'
        continue
      usage(command)
    # Arg parsed
    input_files = map(open, input_path)
    if not input_files:
      input_files = [sys.stdin]
    if output_path:
      output_file = open(output_path, 'w')
    else:
      output_file = sys.stdout
    for input_file in input_files:
      process(input_file, output_file, prefix)

  except IndexError:
    usage(command)

  except IOError:
    sys.stderr.write('Reading Error')
    sys.exit(os.EX_DATAERR)


if __name__ == "__main__":
    main(sys.argv[0], sys.argv[1:])
