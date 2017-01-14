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
     Markless is a small tool (a h⃨a⃨c⃨k⃨ really) that renders mark-down as plain text,
     using Unicode modifiers characters.
     • Emphasis is rendered using underline modifiers.
     • Lists is rendered using pretty bullets. 
     Continuation is supported.
     • Headers and code are rendered in boxes.
     ▌Blockquote is rendered using block characters
     ▌▌Second level

     
[![Flattr this git repo](http://api.flattr.com/button/flattr-badge-large.png)](https://flattr.com/submit/auto?user_id= ThiasWiesmann&url=https://github.com/wiesmann/Markless&title=Markless&language=en_GB&tags=github&category=software)
