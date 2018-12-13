# Markless

Markless is a small tool (a _hack_ really) that renders mark-down as plain text, using Unicode modifiers characters.

* Emphasis is rendered using underline modifiers.
* Lists is rendered using pretty bullets.
  Continuation is supported.
* Headers and code are rendered in boxes.
* Code is rendered `with dots below`.

> Blockquote is rendered using block characters
>> Second level

For instance the part above is rendered in the following way:

    ╔══════════╗
    ║ Markless ║
    ╚══════════╝

    Markless is a small tool (a 𝘩𝘢𝘤𝘬 really) that renders mark-down as plain text, using Unicode modifiers characters.

    • Emphasis is rendered using underline modifiers.
    • Lists is rendered using pretty bullets.
      Continuation is supported.
    • Headers and code are rendered in boxes.
    • Code is rendered 𝚠𝚒𝚝𝚑 𝚍𝚘𝚝𝚜 𝚋𝚎𝚕𝚘𝚠.

    ▌ 
    ▌ Blockquote is rendered using block characters
    ▌ 
    █  
    █  Second level
    █  
    ▌ 

     
# Installation

This version of the tool requires the [mistune](https://pypi.org/project/mistune/) library.