
import re
import copy
from copy import deepcopy
import os
import subprocess
import PyPDF2 
# text = re.sub(r'\n\w+[.]?\n','',text) # for removing page numbers and serial numbers(can be alphabets as well)
# text = re.sub(r'[\w\s]+\n{2,}','',text)  #for removing  headings
# text = re.sub(r'\n{2,}[\w\s]','',text)  #for removing  headings u can remove those lines which contain only 3 words


class Pdftotxt_extract(object):

    def __init__(self, pdf_file):
        self.pdf_file=pdf_file
        pdfFileObj = open(self.pdf_file, 'rb')
        pdfReader = PyPDF2.PdfFileReader(pdfFileObj)  
        self.no_pages=pdfReader.numPages 
        pdfFileObj.close() 
        self.pgno=0
    def f1(self, foo): 
        return foo.splitlines()
    
    def findOccurrences(s, ch):
        return [i for i, letter in enumerate(s) if letter == ch]

    def check(self, a1, b1, f=0):
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
    #at the last remove those lines whose previous and next lines have been removed
    def main(self, output):
            # loop through each line in corpus
        prev_start=[]
        prev_end=[]
        prev_lines=[]
        one_lines=[]
        lines_removed=[]
        lines_removed_inds=[]
        lines_for_tables=[]
        maxx=0
        counter={}
        actual_counter={}
        total_lines=0
        # all_lines=[]
        # for line_i, line in enumerate(output, 1):
        #     line+='\n'
        #     starts=[m.start(0) for m in re.finditer(r'(?<=(\s\s))\S', line)]
        #     ends=[m.start(0) for m in re.finditer(r'\S(?=((\s\s)|\n))', line)]
        #     if len(all_lines)>0:
        #         temp_all_lines=deepcopy(all_lines[-1])
        #         if len(temp_all_lines)<len(line):
        #             if len(temp_all_lines)>1:
        #                 temp_all_lines=temp_all_lines[:len(temp_all_lines)-1]
        #             else:
        #                 temp_all_lines=""
        #             while len(temp_all_lines)<len(line)-1:
        #                 temp_all_lines+=" "
        #             temp_all_lines+='\n'
        #         insrt=1
        #         for st, en in zip(starts, ends):
        #             if re.search(r'\S', temp_all_lines[st:en+1]):
        #                 insrt=0
        #             else:
        #                 temp_all_lines=temp_all_lines[:st]+line[st:en+1]+temp_all_lines[en+1:]
        #         if insrt==1:
        #             all_lines[-1]=deepcopy(temp_all_lines)
        #         else:
        #             all_lines.append(line)
        #     else:
        #         all_lines.append(line)
        # #print_str="".join(str(x) for x in all_lines)
        # #print(#print_str)
        w_spce={}
        for line_i, line in enumerate(output, 1):
            line+='\n'
            for i in findOccurrences(line, " "):
                if i not in w_spce:
                    w_spce[i]=0
                w_spce[i]+=1
            total_lines+=1
            line = re.sub(r':','',line)
            f=0
            prev_temp_line=copy.deepcopy(line)
            line=re.sub(r'^\s*[\(]?\w+[\.\)](?=\s)','', line) #for removing line numbers. 
            if prev_temp_line!=line:
                f=5                                                    #if this creates problems, include a flag in self.check function to take 3 more characters if this pattern comes in the current line
            str_curr=''.join(line)
            starts=[m.start(0) for m in re.finditer(r'(?<=(\s\s))\S', line)]
            ends=[m.start(0) for m in re.finditer(r'\S(?=((\s\s)|\n))', line)]
            if re.search(r'\S', line[0:2]):
                starts.insert(0,0) 
            if  starts and ends and  ends[0]-starts[0]<=2:
                del starts[0]
                del ends[0]

            starts_str=" ".join(str(x) for x in starts)
            # if self.pgno==9:
            #     #print(self.pgno, " ".join(str(x) for x in starts))                
            indiv=1
            # if self.pgno==20:
            #     #print(line, starts, "endofline")
            if len(starts)>0:
                for key in counter:
                    if starts_str in key:
                        counter[key]+=1
                        temp_key=key.split(" ")
                        # if self.pgno==20:
                        #     #print(line, ";", temp_key,";", starts, int(temp_key[0])==starts[0])
                        if int(temp_key[0])==starts[0]:
                            actual_counter[key]+=1
                        indiv=0
            if indiv==1 and len(starts)>1:
                if starts_str in counter:
                    counter[starts_str]+=1
                    actual_counter[starts_str]+=1
                else:
                    counter[starts_str]=1
                    actual_counter[starts_str]=1
            if ends:
            	maxx=max(maxx, max(ends))
            if len(starts)<1:
            	###print(line)
            	lines_removed.append([line_i, str_curr])
            	lines_removed_inds.append(line_i)
            	continue
            if len(starts)==1 and ends[0]-starts[0]<=2:
             	pass
            else:
            	lines_for_tables.append([copy.deepcopy(starts), line, copy.deepcopy(ends), line_i])       	

            if not re.search(r'\S\s+\S', line):
            	###print(line)
                pass
            if len(starts)==1 and starts[0]>60:
             	one_lines.append([starts[0], line_i, str_curr])       
            prev_end=ends
            prev_start=starts
            if len(prev_lines)<2:
            	prev_lines.append(line)
            else:
            	str1=''.join(prev_lines[-1])
            	str2=''.join(prev_lines[-2])
            	for (s, e) in zip(starts, ends):
            		padsize1=max(len(str1), e)
            		padsize2=max(len(str2), e)
            		str1=str1.ljust(padsize1)
            		str2=str2.ljust(padsize2)
            		# if not re.search(r'\S', str1[s:e+1]) and not re.search(r'\S', str2[s:e+1]) :
            		# 	###print(line)
            	prev_lines[-2]=prev_lines[-1]
            	prev_lines[-1]=line
        if counter :
            Keymax = max(counter, key=counter.get)
            if counter[Keymax]>total_lines/4:# and actual_counter[Keymax]>total_lines/6:
                #print(self.pgno, Keymax,":;k'", actual_counter[Keymax], counter[Keymax], total_lines)# counter[Keymax], total_lines)       
        i=0  
        while i<len(one_lines):
          	j=i
          	while j<len(one_lines) and one_lines[j][0]==one_lines[i][0]:
          		j+=1
          		if j-i==1:
          			lines_removed.append(one_lines[i][1])
          			lines_removed_inds.append(line_i)
          	i=j

        i=1
        while i<len(lines_for_tables):
        	j=i
        	if len(lines_for_tables[i][0])==1:
        		i+=1
        		continue
        	print('--------------------------------------------------------------------------')
        	print("table starts")
        	f=0
        	while j<len(lines_for_tables) and (self.check(lines_for_tables[j][0], lines_for_tables[i][0]) or\
             self.check(lines_for_tables[i][0], lines_for_tables[j][0]) or self.check(lines_for_tables[j][0], lines_for_tables[j-1][0]) or \
             self.check(lines_for_tables[j-1][0], lines_for_tables[j][0]) or self.check(lines_for_tables[j][0], lines_for_tables[j-2][0]) or \
             self.check(lines_for_tables[j-2][0], lines_for_tables[j][0]) ):
        		if len(lines_for_tables[j][0])==1 and lines_for_tables[j][0][0]<=10 and lines_for_tables[j][2][0]-lines_for_tables[j][0][0]>=0.6*maxx:
        			f=1
        			break
        		print(lines_for_tables[j][1])
        		j+=1;lines_removed.append(lines_for_tables[j-1][3])
        	if j==i+1 and f==0:
        		i1=i
        		i=j  
        	while j<len(lines_for_tables) and (self.check(lines_for_tables[j][0], lines_for_tables[i][0]) or self.check(lines_for_tables[i][0], lines_for_tables[j][0]) or self.check(lines_for_tables[j][0], lines_for_tables[j-1][0]) or self.check(lines_for_tables[j-1][0], lines_for_tables[j][0])\
               or self.check(lines_for_tables[j][0], lines_for_tables[j-2][0]) or self.check(lines_for_tables[j-2][0], lines_for_tables[j][0])) :
        		if len(lines_for_tables[j][0])==1 and lines_for_tables[j][0][0]<=10 and lines_for_tables[j][2][0]-lines_for_tables[j][0][0]>=0.6*maxx:
        			break
        		print(lines_for_tables[j][1])
        		j+=1;lines_removed.append(lines_for_tables[j-1][3])
        	print('--------------------------------------------------------------------------')
        	print("table ends")#j<len(lines_for_tables) and self.check(lines_for_tables[j][0], lines_for_tables[i][0]) )
        	i=j
        # print("removed lines")
        # for line in lines_removed:
           # print(line)
  #print("removed lines")
 
        # print("final lines")
        # for line_i, line in enumerate(output, 1):
        #     if line_i not in lines_removed or 1:
        #         starts=[m.start(0) for m in re.finditer(r'(?<=(\s\s))\S', line)]
        #         print(starts, line)
    def extract_text(self):
        final_output=[]
        for page in range(1,self.no_pages+1):
            self.pgno=page
            command  = ['pdftotext', '-f', str(page), '-l', str(page), '-layout', self.pdf_file, '-']
            output   = subprocess.check_output(command).decode('utf8')
            final_output.append(self.main(self.f1(output)))
        return final_output

if __name__ == '__main__':
    pdf='Banking Regulations.pdf'
    pdftotxt_extract=Pdftotxt_extract(pdf)
    print(pdftotxt_extract.extract_text())
