#!/usr/bin/env python3
import argparse
import io

def apply(source, destination):
	rec = None
	sour_fix = None

	with open(source, "rt") as i:
		with io.open(destination, "wt", newline="\r\n") as o:
			for line in i:
				line = line.split(" ")
				if line[0] == "0":
					if sour_fix is not None:
						o.write(sour_fix)
					rec = line[2].strip()
				if rec == "SOUR":
					if line[0] == "1" and line[1] == "TYPE":
						line[1] = "TITL"
						sour_fix = " ".join(line)
						continue
					if line[0] == "1" and line[1] == "TITL":
						sour_fix = None
				if rec == "INDI" and line[0] == "1"  and line[1] == "ADDR":
					continue
				if rec == "FAM" and line[0] == "1"  and line[1] in ("ADDR", "PHON"): # Not supported
					continue
				if rec == "SUBM" and line[0] == "1"  and line[1] == "EMAL": # Should be EMAIL
					continue
				if line[1] == "CONC": # Need to export at 255 chars per line
					line[1] = "CONT"
				if rec == "NOTE" and line[0] == "2" and line[1] == "SOUR":
					line[0] = "1"
				line = " ".join(line)
				o.write(line)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(prog="easytree-gedcom-fix", description="Fix EasyTree GEDCOM files")
	parser.add_argument("source", help="Source filename")
	parser.add_argument("destination", help="Destination filename")

	args = parser.parse_args()
	apply(**vars(args))
