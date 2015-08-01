#!/usr/bin/env python

"""Parse csv

Usage:
  csvParser.py <input_file> [--base=PATH]

Arguments:
  <input_file>          input file, TotalSampleList sheet Look Up, downloaded as csv

Options:
  -h --help             Show this screen
  -v --version          Show version
  -b --base=PATH        Path to flowcell folder
  						[default: /mnt/hds/proj/bioinfo/OUTBOX]


"""
from docopt import docopt # help message module
import csv     
import sys      
import os
import re  
		

def main(args): # needed for the use of docopt
	
	# opens the csv file given as argument
	with open(args['<input_file>'], 'r') as file:
		
		#jumps over the 11 first lines in the opened csv
		for i in xrange(11):
			file.readline()

		#the header is saved in header
		header = file.readline()

		
		#Creates the dictionary data from the csv-file and takes the fc-ids (col23) as keys, fields are rows(lists) separated by ",". The fields are stripped from ; in the end and beginning and from whitespace.
		data = {}
		for line in file:
			fields = line.strip().split(",")	
			#field[0], or project ID must match 6 digits
			match = re.search('\d{6}',fields[0])
			if match:																			
				fieldstrip = [field.rstrip(";").lstrip(";").replace(" ","") for field in fields]
				project_ids = fieldstrip[0]
				fc_ids = [fcid.strip() for fcid in fields[23].split(";")]												
				
				for fcid in fc_ids:
					#if fcid is not empty - do next thing
					if fcid != "":	
						#if fcid is not already in data, take the whole row for that key 										
						if not fcid in data:									
							data[fcid] = [fieldstrip]								
						else:
							data[fcid].append(fieldstrip)							
										
			#For every key in data (fd-id), create a file named [fc-id].csv and write the header and the rows for that flowcell
			#base = path(args['--base'])
			for key in data:
				if not os.path.exists(args['--base']+"/Project_"+project_ids+"/"+key):
					#os.makedirs("/Users/emmasernstad/Scripts/OUTBOX/"+"Project_"+project_ids+"/"+key)
					print "Folder doesn't exist for:"+key
					return

				with open(args['--base']+"/Project_"+project_ids+"/"+key+"/"+"sampleList-"+project_ids+"-"+key+".csv","w") as sampleList:
					sampleList.write(header)
					writer = csv.writer(sampleList)
					writer.writerows(data[key])
		
		
		print "Flowcell IDs:" 
		print data.keys()
		print "No of flowcells:"
		print len(data.keys())	



if __name__ == '__main__':
  # Parse docstring defined command line arguments
  args = docopt(__doc__, version='csvParser v1.0')

main(args)

    
