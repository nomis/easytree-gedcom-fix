Fix the GEDCOM output of the Sierra On-Line "Generations" family tree software
"EasyTree" V8.0

Discards some information that isn't supported (phone/address information on
families).

All free-form text that should be multiple lines is exported as word wrapped
text, so export at 255 characters per line to reduce word wrapping and then
correct the data manually.

Recognised custom source fields are moved into a note on an event on the source.

Text on source references are moved to the source itself. Multiple instances of
this will be concatenated in file order.
