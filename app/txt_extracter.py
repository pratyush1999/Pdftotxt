import re
import copy
from copy import deepcopy
import os
import subprocess
from split_pdf import Pdf_get_pages
import string



class Pdftotxt_extract(object):

    def __init__(self, pdf_file):
        """ this class is the text extracter class"""
        self.pdf_file=pdf_file
        self.no_pages=0
        self.pgno=0
    def f1(self, foo): 
        """ this method splits the lines of input"""
        return foo.splitlines()
    def findOccurrences(self, s, ch):
        """ this method is a utility for finding the no of occurrences of a character in a string"""
        return [i for i, letter in enumerate(s) if letter == ch]
    def check(self, a1, b1, f=0):
       # """This method is an addon on the table detection function."""
    	a=copy.deepcopy(a1)
    	b=copy.deepcopy(b1)
    	while len(b)<len(a) and abs(a[0]-b[0])>5:
    		del a[0]
    	while len(a)<len(b) and abs(a[0]-b[0])>5:
    		del b[0]
    	for i,j in zip(a,b):
    	    if max(i,j)-min(i,j)>5+f:
    	    	return False
    	return True
    def basic_cleaning(self, line):
        """ does basic cleaning of line"""
        line+='\n'
        line = re.sub(r':','',line)
        return line     
    def main(self, output, pg_ends):
        """ the main function which returns the clean text"""
        lines_removed={}#stores the lines and line indices of lines which are removed from input
        lines_for_tables=[] #stores lines which are part of table
        maxx=0 #stores the max length of line
        w_spce={} #stores the dictoionary of no of lines having whitespace at an index
        empty_flag=[]# stores  boolean values signifying if the line is empty
        empty_flag.append(0) 
        all_starts=[] #stores all the starts(which stores the index of first character of each segment separated by >=2 space character)
        all_ends=[]
        line_hyphen=1 #
        line_end=[':',',','.',';'] #stores all the characters which signify the end of a sentence
        all_lines=[] #stores all lines of input
        pg_ends_ret=[] #stores boolean values signifying if the line is the last line of the page
        for line_i, line in enumerate(output, 1):
            line+='\n'
            line = re.sub(r':','',line)
            if line[0]=='-':                        #replace hyphen with numbers if hyphen is used to signify point of a list of points
                line=str(line_hyphen)+'.'+line[1:]
                line_hyphen+=1                      #continue incrementing the counter for the next point.
            f=0
            # prev_temp_line=copy.deepcopy(line)
            line=re.sub(r'^\s*[\(]?\w+[\.\)](?=\s)','', line) #for removing line numbers. 
            # if prev_temp_line!=line:
            #     f=5                     #sets an offset for lines which have numbered points                             
            starts=[m.start(0) for m in re.finditer(r'(?<=(\s\s))\S', line)]
            ends=[m.start(0) for m in re.finditer(r'\S(?=((\s\s)|\n))', line)]
            if re.search(r'\S', line[0:2]):
                starts.insert(0,0) 
            if  starts and ends and  ends[0]-starts[0]<=2:
                del starts[0]
                del ends[0]
            all_starts.append(starts)
            all_ends.append(ends)
            if len(starts)<1:
                #print(line)
                empty_flag.append(1)
                continue
            empty_flag.append(0)
        empty_flag.append(1)
        for line_i, line in enumerate(output, 1):
            if line_i not in lines_removed:
                lines_removed[line_i]=0
            line+='\n'
            line = re.sub(r':','',line)
            f=0
   #         prev_temp_line=copy.deepcopy(line)
            line=re.sub(r'^\s*[\(]?\w+[\.\)](?=\s)','', line) #for removing line numbers. 
            # if prev_temp_line!=line:
            #     f=5                                                    #if this creates problems, include a flag in self.check function to take 3 more characters if this pattern comes in the current line
            starts=all_starts[line_i-1]#stores the index of first character of each segment separated by >=2 space character)
            ends=all_ends[line_i-1]#stores the index of last character of each segment separated by >=2 space character)
         #   print("this line starts:",line, starts,"this line ends")
            if ends:
            	maxx=max(maxx, max(ends))
            if len(starts)<1:
            	lines_removed[line_i]=1
            	continue
            if len(starts)==1 and ends[0]-starts[0]<=2:
             	pass
            elif len(starts)>=2:
            	lines_for_tables.append([starts, line, ends, line_i])      	
            if line_i>=2 and line_i+3<len(empty_flag) and (len(starts)==1)and len(all_starts[line_i])==1 and ( (empty_flag[line_i-1]==1\
                 and empty_flag[line_i-2]==1 and empty_flag[line_i+2]==1) or   \
               (empty_flag[line_i-1]==1 and empty_flag[line_i+2]==1 and empty_flag[line_i+3]==1) ):
                #print('type0', line, empty_flag[line_i-1]==1 and empty_flag[line_i+2]==1 and empty_flag[line_i+3]==1, all_lines[line_i+3])
                if pg_ends and  pg_ends[line_i-1]==0 and pg_ends[line_i]==0:
                    lines_removed[line_i]=1   
                    lines_removed[line_i+1]=1  #for hadling image caption

            if line_i>=2 and line_i+2<len(empty_flag) and len(starts)==1 and ( (empty_flag[line_i-1]==1 and empty_flag[line_i-2]==1 and   \
                empty_flag[line_i+1]==1) or( empty_flag[line_i-1]==1 and empty_flag[line_i+1]==1 and empty_flag[line_i+2]==1) ):
               # print('type1', line)
                if pg_ends and pg_ends and pg_ends[line_i-1]==0:
                    lines_removed[line_i]=1     #for hadling image caption
           
        #table detection method
        i=1
        while i<len(lines_for_tables):
        	j=i
        	if len(lines_for_tables[i][0])==1:
        		i+=1
        		continue
        	#print('--------------------------------------------------------------------------')
        	#print("table starts")
        	f=0
        	while j<len(lines_for_tables) and (self.check(lines_for_tables[j][0], lines_for_tables[i][0]) or\
             self.check(lines_for_tables[i][0], lines_for_tables[j][0]) or self.check(lines_for_tables[j][0], lines_for_tables[j-1][0]) or \
             self.check(lines_for_tables[j-1][0], lines_for_tables[j][0]) or self.check(lines_for_tables[j][0], lines_for_tables[j-2][0]) or \
             self.check(lines_for_tables[j-2][0], lines_for_tables[j][0]) ):
        		if len(lines_for_tables[j][0])==1 and lines_for_tables[j][0][0]<=10 and lines_for_tables[j][2][0]-lines_for_tables[j][0][0]>=0.6*maxx:
        			f=1
        			break
        		#print(lines_for_tables[j][1])
        		j+=1;lines_removed[lines_for_tables[j-1][3]]=1
        	if j==i+1 and f==0:
        		i1=i
        		i=j  
        	while j<len(lines_for_tables) and (self.check(lines_for_tables[j][0], lines_for_tables[i][0]) or self.check(lines_for_tables[i][0], lines_for_tables[j][0]) or self.check(lines_for_tables[j][0], lines_for_tables[j-1][0]) or self.check(lines_for_tables[j-1][0], lines_for_tables[j][0])\
               or self.check(lines_for_tables[j][0], lines_for_tables[j-2][0]) or self.check(lines_for_tables[j-2][0], lines_for_tables[j][0])) :
        		if len(lines_for_tables[j][0])==1 and lines_for_tables[j][0][0]<=10 and lines_for_tables[j][2][0]-lines_for_tables[j][0][0]>=0.6*maxx:
        			break
        		#print(lines_for_tables[j][1])
        		j+=1;lines_removed[lines_for_tables[j-1][3]]=1
        	#print('--------------------------------------------------------------------------')
        	#print("table ends")
        	i=j
 
        final_lines=""
        line_hyphen=1
        bullets=['-']
        last_line=""
        for line_i, line in enumerate(output, 1):
            if lines_removed[line_i]==0:
                if pg_ends:
                    pg_ends_ret.append(pg_ends[line_i-1])
                if line.isupper() or (not re.search(r'[a-zA-Z]',line)):  #add upper case lines as well to the output.
                    line+='.'
                line = re.sub(r'\u2013',':',line)
                line = re.sub(r';','.',line)
                line = re.sub(r'\'','',line)
                line = re.sub(r'\"','',line)
                #code for adding full stop at end of unpunctuated lines
                line=line.lstrip()
                if len(line)>=2 and line[0].isalpha() and line[1]==')':
                    line=line[0]+'.'+line[2:]
                if line and line[0] in bullets:
                    line=str(line_hyphen)+'.'+line[1:]
                    line_hyphen+=1
                elif line and line_i<len(output) and (len(line)<=2 or line[-2] in line_end )and self.basic_cleaning(output[line_i]) not in bullets:
                    line_hyphen=1
                line=line.rstrip()# or  re.findall(r'^\s*[A-Z]', self.basic_cleaning(output[line_i]))
                if line_i<len(output) and (re.search(r'^\s*[A-Z]', self.basic_cleaning(output[line_i])) )    and (line[-1] not in line_end) and (len(line)<=len(self.basic_cleaning(output[line_i]))-10 or len(line)>=len(self.basic_cleaning(output[line_i]))-10):
                     line+="."
                elif line_i<len(output) and (re.search(r'^\s*[\(]\w+[\.\)](?=\s)', self.basic_cleaning(output[line_i]))  )    and (line[-1] not in line_end):
                     line+="."
                line=re.sub(f'[^{re.escape(string.printable)}]', '', line)#removes non printable characters from a string
                final_lines+=line
                final_lines+=' '
                final_lines+='\n'
                last_line=line
        return final_lines, pg_ends_ret
    def extract_text(self):
        pdftotxt_extract=Pdf_get_pages(self.pdf_file)
       # command  = ['pdftotext',  '-layout', self.pdf_file, '-']
       # output   = subprocess.check_output(command).decode('utf8')
        #pg_ends=[]
        output, pg_ends=pdftotxt_extract.extract_text()
        output = re.sub(r'\u2212','-', output)
        output = re.sub(r'\u2022','-', output)
        final_output, pg_ends=self.main(output.splitlines(), pg_ends)
        final_output, _=self.main(final_output.splitlines(), pg_ends)#.encode('utf8')
        final_output=re.sub(r'\.+','.',final_output)
        return final_output#.encode('utf8')

if __name__ == '__main__':
    pdf='/home/pratyush1999/Documents/btp/Wealth Management- Relevant Documents/Original PDFs/Regtech in Financial Services.pdf'
    pdftotxt_extract=Pdftotxt_extract(pdf)
    #pdftotxt_extract.extract_text()
   # print(pdftotxt_extract.extract_text())
    print("{\"content\":\"", pdftotxt_extract.extract_text(), "\"}")
    # command  = ['curl', '-i', '-X', 'POST', 'http://127.0.0.1:5000/library_summary', '-d',  "pdftotxt_extract.extract_text()"]
    # output   = subprocess.check_output(command).decode('utf8')
    # print(output)
