
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
    
    def findOccurrences(self, s, ch):
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
    def break_into_pages(self, output):
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
        maxlnline=0
        for line_i, line in enumerate(output, 1):
            maxlnline=max(maxlnline, len(line))
        w_spce={}
        left_w_spce={}
        right_w_spce={}
        for line_i, line in enumerate(output, 1):
            line+='\n'
            for  i, letter in enumerate(line):
                if letter!=" ":
                    continue
                if i>=10 and i<len(line)-10 and line[i+1]==" ":
                    nofwords=len(re.findall(r'\S(?=(\s))', line[:i]))
                    if i not in left_w_spce:
                        left_w_spce[i]=0
                    left_w_spce[i]+=nofwords
                  
                    nofwords=len(re.findall(r'\S(?=(\s))', line[i:]))
                    if i not in right_w_spce:
                        right_w_spce[i]=0
                    right_w_spce[i]+=nofwords

                    if i not in w_spce:
                        w_spce[i]=0
                    w_spce[i]+=1
            for i in range(len(line)-10, maxlnline-10):
                if i>=10 and i not in w_spce:
                    w_spce[i]=0
                if i not in left_w_spce:
                    left_w_spce[i]=0

                if i not in right_w_spce:
                    right_w_spce[i]=0
                if i>=10:
                    w_spce[i]+=1
                    left_w_spce[i]+=len(re.findall(r'\S(?=(\s))', line[:i]))
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
            if ends:
              maxx=max(maxx, max(ends))
            if len(starts)<1:
              lines_removed.append([line_i, str_curr])
              lines_removed_inds.append(line_i)
              continue
            if len(starts)==1 and ends[0]-starts[0]<=2:
              pass
            else:
              lines_for_tables.append([copy.deepcopy(starts), line, copy.deepcopy(ends), line_i])         
        split_wspce=1000
        if w_spce :
             Keymax = max(w_spce, key=w_spce.get)
             sorted(w_spce.items(), key=lambda x: x[1], reverse=True)
             if  abs(Keymax-int(maxlnline/2))<=20 \
                     and(\
                      min(right_w_spce[Keymax],left_w_spce[Keymax])>=3*max(right_w_spce[Keymax], left_w_spce[Keymax])/4\
                      or left_w_spce[Keymax]>=100)\
              and right_w_spce[Keymax]>10 and left_w_spce[Keymax]>10:
                 split_wspce=Keymax
             else:
                 dict_list=[]
                 for key, val in w_spce.items(): 
                    dict_list.append([key, val])
                 dict_list=sorted(dict_list, key=lambda x: x[1], reverse=True)
                 for key, val in dict_list:
                     if val>=w_spce[Keymax]-5 and abs(key-int(maxlnline/2))<=int(maxlnline/5)\
                     and(\
                      left_w_spce[key]>=3*max(right_w_spce[key], left_w_spce[key])/4\
                      or left_w_spce[key]>=100)\
                     and right_w_spce[key]>10 and left_w_spce[key]>10:
                         split_wspce=key
                         break
                     elif val>=w_spce[Keymax]-15 and abs(key-int(maxlnline/2))<=int(maxlnline/5)\
                     and(\
                       left_w_spce[key]>=3*max(right_w_spce[key], left_w_spce[key])/4\
                      or left_w_spce[key]>=100)\
                     and right_w_spce[key]>10 and left_w_spce[key]>10:
                         split_wspce=key
                         break
        first_column=""
        second_column=""
        for line_i, line in enumerate(output, 1):
            if split_wspce<len(line)-1 and line[split_wspce]==' ' and line[split_wspce+1]==' ':
                first_column+=line[:split_wspce]
                first_column+='\n'
                second_column+=line[split_wspce:]
                if line[-1]!='\n':
                    second_column+='\n'
            else:
                first_column+=line
                if len(line)==0 or line[-1]!='\n':
                    first_column+='\n'

        # print("pg starts:",self.pgno)
        # print('------------------------------------------------------------------------------------------')
        # print(first_column)
        # print('------------------------------------------------------------------------------------------')
        # print(second_column)                  
        # print("pg ends:",self.pgno)
        return first_column, second_column

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
        # ##print_str="".join(str(x) for x in all_lines)
        # ##print(##print_str)
        maxlnline=0
        for line_i, line in enumerate(output, 1):
            maxlnline=max(maxlnline, len(line))
        w_spce={}
        left_w_spce={}
        right_w_spce={}
        for line_i, line in enumerate(output, 1):
            line+='\n'
            # if self.pgno==1 and line[58]!=" ":
            #     print(line[:58], line_i)
            # if self.pgno==32 and line_i==6:
            #     for i in line:
            #         prat+=i
            #     print(line[40])
                
            for  i, letter in enumerate(line):
                if letter!=" ":
                    continue
                # if line[i:i+5]=="which" and self.pgno==5 and line_i==9:
                #     print(i+6)
                # if self.pgno==5 and line_i>=4 and line_i<=5:
                #     print(i," ")
                if i>=10 and i<len(line)-10 and line[i+1]==" ":
                    # if self.pgno==32 and line_i==6:
                    #     print(line, i)
                    nofwords=len(re.findall(r'\S(?=(\s))', line[:i]))
                    if i not in left_w_spce:
                        left_w_spce[i]=0
                    left_w_spce[i]+=nofwords
                  
                    nofwords=len(re.findall(r'\S(?=(\s))', line[i:]))
                    if i not in right_w_spce:
                        right_w_spce[i]=0
                    right_w_spce[i]+=nofwords

                    if i not in w_spce:
                        w_spce[i]=0
                    w_spce[i]+=1
            for i in range(len(line)-10, maxlnline-10):
                if i>=10 and i not in w_spce:
                    w_spce[i]=0
                if i not in left_w_spce:
                    left_w_spce[i]=0

                if i not in right_w_spce:
                    right_w_spce[i]=0
                if i>=10:
                    w_spce[i]+=1
                    left_w_spce[i]+=len(re.findall(r'\S(?=(\s))', line[:i]))
            # if self.pgno==50 and w_spce[60]>w_spce_temp:
            #     print(line)
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
            if ends:
            	maxx=max(maxx, max(ends))
            if len(starts)<1:
            	####print(line)
            	lines_removed.append([line_i, str_curr])
            	lines_removed_inds.append(line_i)
            	continue
            if len(starts)==1 and ends[0]-starts[0]<=2:
             	pass
            else:
            	lines_for_tables.append([copy.deepcopy(starts), line, copy.deepcopy(ends), line_i])       	

            if len(starts)==1 and starts[0]>60:
             	one_lines.append([starts[0], line_i, str_curr])       
            prev_end=ends
            prev_start=starts
        # if self.pgno==5:
        #     print(w_spce,maxlnline, max(w_spce, key=w_spce.get), w_spce[max(w_spce, key=w_spce.get)])
        #     print(right_w_spce[62], left_w_spce[62])
        split_wspce=1000
        # if one_w_spce:
        #     one_Keymax = max(one_w_spce, key=one_w_spce.get)
        #     if one_w_spce[one_Keymax]>=total_lines-5:
        #         split_wspce=one_Keymax
        if w_spce :
             Keymax = max(w_spce, key=w_spce.get)
             sorted(w_spce.items(), key=lambda x: x[1], reverse=True)
             # if self.pgno==7:
             #    outta=[]
             #    for key, val in w_spce.items():
             #        if val==w_spce[Keymax]:
             #            outta.append(key)
             #    print("list of max keys:", *outta)
             if  abs(Keymax-int(maxlnline/2))<=20 \
                     and(\
                      min(right_w_spce[Keymax],left_w_spce[Keymax])>=3*max(right_w_spce[Keymax], left_w_spce[Keymax])/4\
                      or left_w_spce[Keymax]>=100)\
              and right_w_spce[Keymax]>10 and left_w_spce[Keymax]>10:
               #   print("type 1:",self.pgno,"col key:", Keymax, "max length of line in page:",\
               #       maxlnline, "w_spce of key:",w_spce[Keymax], "right_w_spce:", right_w_spce[Keymax],\
               #       "left_w_spce:", left_w_spce[Keymax],"total_lines :", total_lines,
               # "diff bw w_spce and total_lines/total_lines:",100* abs(w_spce[Keymax]-total_lines)/total_lines  )
                 split_wspce=Keymax
             else:#if right_w_spce[Keymax]>=10 and left_w_spce[Keymax]>=10:
                 dict_list=[]
                 for key, val in w_spce.items(): 
                    dict_list.append([key, val])
                 dict_list=sorted(dict_list, key=lambda x: x[1], reverse=True)
                 for key, val in dict_list:
                     if val>=w_spce[Keymax]-5 and abs(key-int(maxlnline/2))<=int(maxlnline/5)\
                     and(\
                      left_w_spce[key]>=3*max(right_w_spce[key], left_w_spce[key])/4\
                      or left_w_spce[key]>=100)\
                     and right_w_spce[key]>10 and left_w_spce[key]>10:
                         split_wspce=key
                   #       print("type 2:",self.pgno,"white space col key:", key, "max length of line in page:",\
                   #       maxlnline, "w_spce of key:",w_spce[key], "right_w_spce:", right_w_spce[key],\
                   #       "left_w_spce:", left_w_spce[key],"total_lines :" , total_lines, "right_w_spce of keymax:", right_w_spce[Keymax],\
                   #   "left_w_spce of keymax:", left_w_spce[Keymax],
                   # "diff bw w_spce and total_lines/total_lines:",100* abs(w_spce[Keymax]-total_lines)/total_lines)
                         break
                     elif val>=w_spce[Keymax]-15 and abs(key-int(maxlnline/2))<=int(maxlnline/5)\
                     and(\
                       left_w_spce[key]>=3*max(right_w_spce[key], left_w_spce[key])/4\
                      or left_w_spce[key]>=100)\
                     and right_w_spce[key]>10 and left_w_spce[key]>10:
                         split_wspce=key
                   #       print("type 2:",self.pgno,"white space col key:", key, "max length of line in page:",\
                   #       maxlnline, "w_spce of key:",w_spce[key], "right_w_spce:", right_w_spce[key],\
                   #       "left_w_spce:", left_w_spce[key],"total_lines :" , total_lines, "right_w_spce of keymax:", right_w_spce[Keymax],\
                   #   "left_w_spce of keymax:", left_w_spce[Keymax],
                   # "diff bw w_spce and total_lines/total_lines:",100* abs(w_spce[Keymax]-total_lines)/total_lines)
                         break
        # first_column=""
        # second_column=""
        # for line_i, line in enumerate(output, 1):
        #     # if self.pgno==10 and line_i==5:
        #     #     print("this line:::", split_wspce, line[:split_wspce], w_spce[52], total_lines)
        #     if split_wspce<len(line)-1 and line[split_wspce]==' ' and line[split_wspce+1]==' ':
        #         first_column+=line[:split_wspce]
        #         first_column+='\n'
        #         second_column+=line[split_wspce:]
        #         if line[-1]!='\n':
        #             second_column+='\n'
        #     else:
        #         first_column+=line
        #         if len(line)==0 or line[-1]!='\n':
        #             first_column+='\n'

        # print("pg starts:",self.pgno)
        # print('------------------------------------------------------------------------------------------')
        # print(first_column)
        # print('------------------------------------------------------------------------------------------')
        # print(second_column)                  
        # print("pg ends:",self.pgno)
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
        	#	print(lines_for_tables[j][1])
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
        	#print('--------------------------------------------------------------------------')
        	#print("table ends")#j<len(lines_for_tables) and self.check(lines_for_tables[j][0], lines_for_tables[i][0]) )
        	i=j
        # #print("removed lines")
        # for line in lines_removed:
           # #print(line)
  ##print("removed lines")
 
        #print("final lines")
        final_lines=""
        for line_i, line in enumerate(output, 1):
            if line_i not in lines_removed:
              final_lines+=line
        return final_lines
                #print(starts, line)
    def extract_text(self):
        final_output=""
        for page in range(1,self.no_pages+1):
            self.pgno=page
            command  = ['pdftotext', '-f', str(page), '-l', str(page), '-layout', self.pdf_file, '-']
            output   = subprocess.check_output(command).decode('utf8')
            first_column, second_column=self.break_into_pages(output)
            print(first_column, second_column )
            if first_column:
              final_output+=self.main(self.f1(first_column))
            if second_column:
              final_output+=self.main(self.f1(second_column))
        return final_output

if __name__ == '__main__':
    pdf='/home/pratyush1999/Documents/btp/Wealth Management- Relevant Documents/Product Documents/HDFC Arbitrage Fund.pdf'
    pdftotxt_extract=Pdftotxt_extract(pdf)
    print(pdftotxt_extract.extract_text())
