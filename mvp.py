import re
import copy
from copy import deepcopy
import os
import subprocess
# import fitz


class Pdftotxt_extract(object):

    def __init__(self, pdf_file):
        self.pdf_file=pdf_file
        # doc = fitz.open(self.pdf_file)
        self.no_pages=0#doc.pageCount
        self.pgno=0
    def f1(self, foo): 
        return foo.splitlines()
    
    def findOccurrences(self, s, ch):
        return [i for i, letter in enumerate(s) if letter == ch]
    def first_word(self,s1):
        s=s1.lstrip()
        spces=self.findOccurrences(s, ' ')
        spces.append(len(s))
        return s[:spces[0]]
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
    def main(self, output):
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
        w_spce={}
        empty_flag=[]
        empty_flag.append(0)
        all_starts=[]
        line_hyphen=1
        line_end=[':',',','.',';']
        all_lines=[]
        all_lines.append("")
        for line_i, line in enumerate(output, 1):
                line+='\n'
                total_lines+=1
                line = re.sub(r':','',line)
                line = re.sub(r'\u2212','-',line)
                all_lines.append(line)
        for line_i, line in enumerate(output, 1):
            line+='\n'
            total_lines+=1
            line = re.sub(r':','',line)
            line = re.sub(r'\u2212','-',line)
            if line[0]=='-':
                line=str(line_hyphen)+'.'+line[1:]
                line_hyphen+=1
            elif line_i+1<len(all_lines) and (len(line)<=2 or line[-2] in line_end )and all_lines[line_i+1][0]!='-':
                line_hyphen=1
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
            all_starts.append(starts)
            if len(starts)<1:
                lines_removed.append([line_i, str_curr])
                lines_removed_inds.append(line_i)
                empty_flag.append(1)
                continue
            empty_flag.append(0)
        empty_flag.append(1)
        for line_i, line in enumerate(output, 1):
            line+='\n'
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
         #   print("this line starts:",line, starts,"this line ends")
            starts_str=" ".join(str(x) for x in starts)
            if ends:
            	maxx=max(maxx, max(ends))
            if len(starts)<1:

            	lines_removed.append([line_i, str_curr])
            	lines_removed.append(line_i)
            	continue
            if len(starts)==1 and ends[0]-starts[0]<=2:
             	pass
            else:
            	lines_for_tables.append([copy.deepcopy(starts), line, copy.deepcopy(ends), line_i])       	

        
            if len(starts)==1 and starts[0]>60:
             	one_lines.append([starts[0], line_i, str_curr])
            if line_i>=2 and line_i+3<len(empty_flag) and (len(starts)==1)and len(all_starts[line_i])==1 and ( (empty_flag[line_i-1]==1\
                 and empty_flag[line_i-2]==1 and empty_flag[line_i+2]==1) or   \
               (empty_flag[line_i-1]==1 and empty_flag[line_i+2]==1 and empty_flag[line_i+3]==1) ):
                lines_removed.append(line_i)   
                lines_removed.append(line_i+1)   

            if line_i>=2 and line_i+2<len(empty_flag) and len(starts)==1 and ( (empty_flag[line_i-1]==1 and empty_flag[line_i-2]==1 and   \
                empty_flag[line_i+1]==1) or( empty_flag[line_i-1]==1 and empty_flag[line_i+1]==1 and empty_flag[line_i+2]==1) ):
                lines_removed.append(line_i)     
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
            	prev_lines[-2]=prev_lines[-1]
            	prev_lines[-1]=line
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
        	# print('--------------------------------------------------------------------------')
        	# print("table starts")
        	f=0
        	while j<len(lines_for_tables) and (self.check(lines_for_tables[j][0], lines_for_tables[i][0]) or\
             self.check(lines_for_tables[i][0], lines_for_tables[j][0]) or self.check(lines_for_tables[j][0], lines_for_tables[j-1][0]) or \
             self.check(lines_for_tables[j-1][0], lines_for_tables[j][0]) or self.check(lines_for_tables[j][0], lines_for_tables[j-2][0]) or \
             self.check(lines_for_tables[j-2][0], lines_for_tables[j][0]) ):
        		if len(lines_for_tables[j][0])==1 and lines_for_tables[j][0][0]<=10 and lines_for_tables[j][2][0]-lines_for_tables[j][0][0]>=0.6*maxx:
        			f=1
        			break
        		#print(lines_for_tables[j][1])
        		j+=1;lines_removed.append(lines_for_tables[j-1][3])
        	if j==i+1 and f==0:
        		i1=i
        		i=j  
        	while j<len(lines_for_tables) and (self.check(lines_for_tables[j][0], lines_for_tables[i][0]) or self.check(lines_for_tables[i][0], lines_for_tables[j][0]) or self.check(lines_for_tables[j][0], lines_for_tables[j-1][0]) or self.check(lines_for_tables[j-1][0], lines_for_tables[j][0])\
               or self.check(lines_for_tables[j][0], lines_for_tables[j-2][0]) or self.check(lines_for_tables[j-2][0], lines_for_tables[j][0])) :
        		if len(lines_for_tables[j][0])==1 and lines_for_tables[j][0][0]<=10 and lines_for_tables[j][2][0]-lines_for_tables[j][0][0]>=0.6*maxx:
        			break
        	#	print(lines_for_tables[j][1])
        		j+=1;lines_removed.append(lines_for_tables[j-1][3])
        	# print('--------------------------------------------------------------------------')
        	# print("table ends")
        	i=j
 
        final_lines=""
        line_hyphen=1
        # start_words=['The', 'These', 'It', 'A', 'An', 'For', 'To', 'Where', 'Anyone', '']
        for line_i, line in enumerate(output, 1):
            if line_i not in lines_removed and not line.isupper():
                line = re.sub(r'\uf0b7','',line)
                line = re.sub(r'\u2212','-',line)
                line = re.sub(r'\u2019','',line)
                line = re.sub(r'\u2018','',line)
                line = re.sub(r';','.',line)
                line = re.sub(r'\'','',line)
                line = re.sub(r'\"','',line)
                if len(line)>=2 and line[0].isalpha() and line[1]==')':
                    line=line[0]+'.'+line[2:]
                if line and line[0]=='-':
                    line=str(line_hyphen)+'.'+line[1:]
                    line_hyphen+=1
                elif line and line_i+1<len(all_lines) and (len(line)<=2 or line[-2] in line_end )and all_lines[line_i+1][0]!='-':
                    line_hyphen=1
                line=line.rstrip()# or  re.findall(r'^\s*[A-Z]', all_lines[line_i+1])
             #   if line_i+1<len(all_lines) and (re.findall(r'^\s*[A-Z]', all_lines[line_i+1]) )    and (line[-1] not in line_end):
                    # print('---------------')
                #     print(line)
                #     # print(all_lines[line_i+1])
                #   #  print(self.first_word(all_lines[line_i+1]))
                #     # print('-------------------')
                #     line+="."
                # print('--------')
                # if line_i+1<len(all_lines) and (re.findall(r'^\s*[\(]?\w+[\.\)](?=\s)', all_lines[line_i+1])  )    and (line[-1] not in line_end):
                #     line+="."

                line = re.sub(r'\u2013',':',line)
                final_lines+=line
                final_lines+=' '
                final_lines+='\n'
        return final_lines
    def extract_text(self):
        final_output=""
        # for page in range(1,self.no_pages+1):
        #     self.pgno=page
        command  = ['pdftotext', '-layout', self.pdf_file, '-']
        output   = subprocess.check_output(command).decode('utf8')
        final_output+=self.main(self.f1(self.main(self.f1(output))))
        # final_output+='\n'
        return final_output

if __name__ == '__main__':
    pdf='/home/pratyush1999/Documents/btp/large.pdf'
    pdftotxt_extract=Pdftotxt_extract(pdf)
    #pdftotxt_extract.extract_text()
    print(pdftotxt_extract.extract_text())
    #print("{\"content\":\"", pdftotxt_extract.extract_text(), "\"}")
    # command  = ['curl', '-i', '-X', 'POST', 'http://10.4.24.5:8004/library_summary', '-d',  pdftotxt_extract.extract_text()]
    # output   = subprocess.check_output(command).decode('utf8')
    # print(output)