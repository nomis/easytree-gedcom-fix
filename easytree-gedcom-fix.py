#!/usr/bin/env python3
# easytree-gedcom-fix - Fix EasyTree GEDCOM files
# Copyright 2023-2024  Simon Arlott
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Fix problems with EasyTree GEDCOM files, discarding some information
# that isn't supported (phone/address information on families)

import argparse
import collections
import io

def apply(source, destination):
	rec = None
	rec_n = []
	discard_n = None
	sour_fix = None
	sour_even = []
	sour_note = []

	out_recs = []
	idx = collections.defaultdict(dict)
	idx_count = collections.defaultdict(collections.Counter)

	sour_fields = {
		"FILN": "File Number",
		"REGI": "Register",
		"MEDI": "Media Type",
		"LOCA": "Location of Source",
		"INTV": "Interviewee",
		"INTE": "Interviewer",
		"VOL": "Volume Number",
		"PAGE": "Page",
		"SUBM": "Submitter",
		"FILE": "File Name",
	}

	with open(source, "rt") as i:
		for line in i:
			line = line.split(" ", 2)
			if discard_n is not None:
				if discard_n >= int(line[0]):
					discard_n = None
			if line[0] == "0":
				if sour_fix is not None:
					out_recs[-1].append(sour_fix)
					sour_fix = None
				if sour_even or sour_note:
					out_recs[-1].append(["1", "DATA", "\n"])
				if sour_even:
					out_recs[-1].append(["2", "EVEN", "\n"])
					out_recs[-1].extend(sour_even)
					sour_even = []
				if sour_note:
					out_recs[-1].append(["2", "NOTE", sour_note[0]])
					for note in sour_note[1:]:
						out_recs[-1].append(["3", "CONT", note])
					sour_note = []

				out_recs.append([])
				rec = line[2].strip()
				rec_n = []
			else:
				rec_n.append(line[1])

			if rec == "SOUR":
				if line[0] == "1" and line[1] == "TYPE":
					line[1] = "TITL"
					sour_fix = line
					continue
				if line[0] == "1" and line[1] == "TITL":
					sour_fix = None
				if line[0] == "1" and line[1] in ("DATE", "PLAC"):
					line[0] = "3"
					sour_even.append(line)
					continue
				if line[0] == "1" and line[1] in sour_fields.keys():
					sour_note.append(f"{sour_fields[line[1]]}: {line[2]}")
					continue
			if rec == "INDI" and line[0] == "1" and line[1] == "ADDR":
				# Remove individual addresses (these may require the family address?)
				discard_n = int(line[0])
			if rec == "FAM" and line[0] == "1" and line[1] in ("ADDR", "PHON"): # Not supported
				discard_n = int(line[0])
			if rec == "SUBM" and line[0] == "1" and line[1] == "ADDR": # Remove submitter address
				discard_n = int(line[0])
			if rec == "SUBM" and line[0] == "1" and line[1] == "EMAL":
				line[1] = "EMAIL"
			if line[1] == "CONC": # Need to export at 255 chars per line
				line[1] = "CONT"
			if rec == "NOTE" and line[0] == "2" and line[1] == "SOUR":
				line[0] = "1"

			if discard_n is not None:
				print(f"Discarding {rec} {line}")
				continue

			out_recs[-1].append(line)

			if line[0] == "0" and line[1].startswith("@"):
				idx[line[2].strip()][line[1]] = out_recs[-1]
			if line[2].startswith("@"):
				idx_count[line[1]][line[2].strip()] += 1

		sour_text = {}
		for out_rec in out_recs:
			if out_rec:
				lines = []
				rec_n = []
				for line in out_rec:
					rec_n = rec_n[0:int(line[0])]
					rec_n.append(line)

					# Inline notes that are only used once
					if line[0] == "1" and line[1] == "NOTE" and line[2].startswith("@"):
						note_id = line[2].strip()
						if idx_count["NOTE"][note_id] == 1:
							idx_count["NOTE"][note_id] = 0
							note = idx["NOTE"][note_id]
							# 1 NOTE @N1@
							line = []
							# 0 @N1@ NOTE    -->    1 NOTE ...
							# 1 CONT ...            2 CONT ...
							# 1 CONT ...            2 SOUR @S1@
							# 1 SOUR @S1@
							assert note[1][1] in ("CONT", "CONC"), note
							lines.append(["1", "NOTE", note[1][2]])
							for note_line in note[2:]:
								note_line[0] = str(int(note_line[0]) + 1)
								lines.append(note_line)
							note.clear()

					# Text from the source needs to be part of the source, not added to an XREF
					if len(rec_n) >= 3:
						for i in range(1, len(rec_n) - 1):
							if rec_n[i][1] == "SOUR" and rec_n[i + 1][1] == "TEXT":
								sour_id = rec_n[i][2].strip()
								if rec_n[i + 1][0] == line[0]:
									# First "TEXT" line
									if sour_text.get(sour_id):
										# Concatenate multiple text for the same source
										line = [str(int(line[0]) + 1), "CONT", line[2]]
									sour_text[sour_id] = True
								else:
									# Must be continuation of "TEXT"
									assert line[1] in ("CONT", "CONC"), line
								idx["SOUR"][sour_id].append([str(int(line[0]) - i), line[1], line[2]])
								line = []
								break

					lines.append(line)
				out_rec.clear()
				out_rec.extend(lines)

		with io.open(destination, "wt", newline="\r\n") as o:
			for out_rec in out_recs:
				for line in out_rec:
					line = " ".join(line)
					o.write(line)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(prog="easytree-gedcom-fix", description="Fix EasyTree GEDCOM files")
	parser.add_argument("source", help="Source filename")
	parser.add_argument("destination", help="Destination filename")

	args = parser.parse_args()
	apply(**vars(args))
