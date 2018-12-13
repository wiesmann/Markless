#!/opt/local/bin/python2.7
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
import mistune

ENCODING = 'utf-8'

_box_light =  u'┌─┐│ │└─┘┬┴'
_box_double = u'╔═╗║ ║╚═╝╦╩'
_box_heavy =  u'┏─┓┃ ┃┗─┛┳┻'
_box_code =   u'╭─╮┃ ┃╰─╯┳┻'

_list_separator = chr(0x0B)  # Line Tabulation
_cell_separator = chr(0x1E)  # Record separator
_row_separator = chr(0x1D)  # Group separator

def get_columns():
  dimensions = map(int,  os.popen('stty size', 'r').read().split())
  return dimensions[1]

def _unichr(code):
  s = "\\U%08x" % code
  return s.decode('unicode-escape')

def display_len(input):
  if not input:
    return 0
  len = 0
  for c in input:
    if unicodedata.category(c) != 'Mn':
      len += 1
  return len

def max_display_len(inputs):
  return max(map(display_len, inputs))

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
  return '\n' + '\n'.join(_makebox(in_lines, box)) + '\n'

def pad_cell(line, widths, padding=1):
  for element, width in zip(line, widths):
    element = element.strip()
    pad = width - display_len(element)
    yield u' ' * (pad + padding) + element + u' '

def _maketable(in_cells, box, widths):
  heads = map(lambda w: box[1] * (w + 2), widths)
  yield box[0] + box[9].join(heads) + box[2]
  for line in in_cells:
    yield box[3] + box[3].join(pad_cell(line, widths)) + box[3]
  yield box[6] + box[10].join(heads) + box[8]

def maketable(in_cells, box, widths):
  return '\n' + '\n'.join(_maketable(in_cells, box, widths)) + '\n'


def _shift_modify(text, emphasis_char):
  for char in text:
    if char.isalnum():
      offset = ord(char)
      if offset >= ord('A') and offset <= ord('Z'):
        yield _unichr(emphasis_char + offset - ord('A'))
        continue
      if offset >= ord('a') and offset <= ord('z'):
        yield _unichr(emphasis_char + offset - ord('a') + 26)
        continue
    yield char

def emphasis(text, emphasis_char):
  return ''.join(_shift_modify(text, emphasis_char))

def _join_modify(text, modifier):
  for char in text:
    if char.isalnum():
      yield char
      yield modifier
    else:
      yield char

def strike(text):
  return ''.join(_join_modify(text, _unichr(0x0336)))

def block_indent(line):
  if line.startswith(u'▌ '):
    return u'█ '+ line[1:]
  if line.startswith(u'█ '):
    return u'█▌ ' + line[2:]
  return u'▌ ' + line

def filter_at_end(items):
  items = list(items)
  while items:
    if items[-1]:
      break
    items.pop()
  return tuple(items)

def encode_block(text):
  return ('\n%s\n' % text).encode(ENCODING)

def encode_lines(lines):
  return encode_block('\n'.join(lines))

class MarklessRenderer(mistune.Renderer):

  def __init__(self):
    super(MarklessRenderer, self).__init__()
    self._cell_counter = 0

  def linebreak(self):
    return '\n'

  def text(self, text):
    return text

  def paragraph(self, text):
    lines = text.decode(ENCODING).split('\n')
    return encode_lines(reflow(lines, get_columns()))

  def link(self, link, title, content):
    return "[" + content + "]"

  def strikethrough(self, text):
    uni_data = text.decode(ENCODING)
    return strike(uni_data).encode(ENCODING)

  def emphasis(self, text):
    uni_data = text.decode(ENCODING)
    return emphasis(uni_data, 0x1D608).encode(ENCODING)

  def double_emphasis(self, text):
    uni_data = text.decode(ENCODING)
    return emphasis(uni_data, 0x1D5D4).encode(ENCODING)

  def codespan(self, text):
    uni_data = text.decode(ENCODING)
    return emphasis(uni_data, 0x1D670).encode(ENCODING)

  def hrule(self):
    return encode_block(u'–' * get_columns())

  def header(self, text, level, raw=None):
    lines = text.decode(ENCODING).split('\n')
    if level == 1:
      box = _box_double
    elif level == 2:
      box = _box_heavy
    else:
      box = _box_light
    return makebox(lines, box).encode(ENCODING)

  def block_code(self, code, lang):
    uni_lines = filter_at_end(code.decode(ENCODING).split('\n'))
    return makebox(uni_lines, _box_code).encode(ENCODING)

  def block_quote(self, text):
    uni_lines = text.decode(ENCODING).split('\n')
    uni_lines = itertools.imap(block_indent, uni_lines)
    return encode_lines(uni_lines)

  def list(self, body, ordered=True):
    items = filter(None, body.decode(ENCODING).split(_list_separator))
    list_lines = []
    for counter, item in enumerate(items):
      if ordered:
        bullet = unicode(counter + 1) + ') '
      else:
        bullet = u'• '
      indent = display_len(bullet)
      lines = filter(None, item.split('\n'))
      list_lines.append(bullet + lines[0])
      for line in lines[1:]:
        list_lines.append(' ' * indent + line)

    return encode_lines(list_lines)

  def list_item(self, text):
    return text + _list_separator

  def table(self, header, body):
    content = header + '\n' + body
    uni_lines = filter(None, content.decode(ENCODING).split(_row_separator))
    uni_cells = map(lambda line: line.split(_cell_separator), uni_lines)
    rotated = list(itertools.izip_longest(*uni_cells))
    widths = map(max_display_len, rotated)
    return encode_block(maketable(uni_cells, _box_double, widths))

  def table_row(self, content):
    self._cell_counter = 0
    return content.strip() + _row_separator

  def table_cell(self, content, **flags):
    uni_data = content.decode(ENCODING)
    if self._cell_counter:
      uni_data = _cell_separator + uni_data
    self._cell_counter+=1
    return uni_data.encode(ENCODING)


def process(input_file, output_file, prefix):
  renderer = MarklessRenderer()
  markdown = mistune.Markdown(renderer=renderer)
  output_file.write(markdown(input_file.read()))

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
