
import re
import copy
from copy import deepcopy
import os
import subprocess

class Pdf_get_pages(object):

    def __init__(self, pdf_file):
        """ this class is for splitting pdf pages """
        self.pdf_file=pdf_file
        pdfFileObj = open(self.pdf_file, 'rb')
        ps = subprocess.Popen(('pdfinfo', self.pdf_file), stdout=subprocess.PIPE)
        self.no_pages = int(subprocess.check_output(('grep', '-oP', '(?<=Pages:          )[ A-Za-z0-9]*'), stdin=ps.stdout))
        self.pgno=0
        self.output=""
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
    def basic_cleaning(self, line):
        """ does basic cleaning of line"""
        line+='\n'
        line = re.sub(r':','',line)
        line = re.sub(r'\u2212','-',line)   
        return line     
    def start_pos(self, line_i):
        """ returns starts of a line """
        line_hyphen=1
        line=self.output[line_i]
        line+='\n'
        line = re.sub(r':','',line)
        line = re.sub(r'\u2212','-',line)
        if line[0]=='-':
            line=str(line_hyphen)+'.'+line[1:]
        f=0
        prev_temp_line=copy.deepcopy(line)
        line=re.sub(r'^\s*[\(]?\w+[\.\)](?=\s)','', line) #for removing line numbers. 
        if prev_temp_line!=line:
            f=5                                                    #if this creates problems, include a flag in self.check function to take 3 more characters if this pattern comes in the current line
        starts=[m.start(0) for m in re.finditer(r'(?<=(\s\s))\S', line)]
        ends=[m.start(0) for m in re.finditer(r'\S(?=((\s\s)|\n))', line)]
        if re.search(r'\S', line[0:2]):
            starts.insert(0,0) 
        if  starts and ends and  ends[0]-starts[0]<=2:
            del starts[0]
        return starts
    def empty_flag(self, line_i):
        """ returns a binary variable signifying if a line is empty"""
        line_hyphen=1
        line_i-=1
        if line_i<0 or line_i>=len(self.output):
          return 0
        starts=self.start_pos(line_i)
        if len(starts)<1:
            return 1
        return 0
    def get_last_line(self):
        """ returns the last line of a corpus of text"""
        i=len(self.output)
        while i>=0 and self.empty_flag(i):
          i-=1
        return i
    def clean(self, first_split=0):
        """ this method cleans the text """
        one_lines=[]
        lines_removed={}
        lines_for_tables=[]
        total_lines=0
        w_spce={}
      #  empty_flag=[]
        #empty_flag.append(0)
        line_hyphen=1
        line_end=[':',',','.',';']
        last_line=self.get_last_line()
        last_empty_line=-1
        maxlnline=0
        for line_i, line in enumerate(self.output, 1):
            maxlnline=max(maxlnline, len(line))
            if line_i-1 not in lines_removed:
                lines_removed[line_i-1]=0
            if not re.search('[a-zA-Z]', line):
                lines_removed[line_i-1]=1
            # if self.pgno==1:
            #   print("this->",line, "line_i:", line_i, "here:",empty_flag[line_i], "now:",all_lines[last_line], last_empty_line)
            line+='\n'
            line = re.sub(r':','',line)
            line=re.sub(r'^\s*[\(]?\w+[\.\)](?=\s)','', line) #for removing line numbers. 
            starts=[m.start(0) for m in re.finditer(r'(?<=(\s\s))\S', line)]
            ends=[m.start(0) for m in re.finditer(r'\S(?=((\s\s)|\n))', line)]
            if re.search(r'\S', line[0:2]):
                starts.insert(0,0) 
            if  starts and ends and  ends[0]-starts[0]<=2:
                del starts[0]
                del ends[0]
         #   print("this line starts:",line, starts,"this line ends")

            if len(starts)<1:
              last_empty_line=line_i
              lines_removed[line_i-1]=1
              continue

            if (len(starts)==1) and (line_i<len(self.output) and len(self.start_pos(line_i))==1 ) and ( (self.empty_flag(line_i-1)==1\
                 and self.empty_flag(line_i-2)==1 and self.empty_flag(line_i+2)==1) or   \
               (self.empty_flag(line_i-1)==1 and self.empty_flag(line_i+2)==1 and self.empty_flag(line_i+3)==1) ):
                lines_removed[line_i-1]=1
                lines_removed[line_i]=1

            if  len(starts)==1 and ( (self.empty_flag(line_i-1)==1 and self.empty_flag(line_i-2)==1 and   \
                self.empty_flag(line_i+1)==1) or(self.empty_flag(line_i-1)==1 and self.empty_flag(line_i+1)==1 and self.empty_flag(line_i+2)==1) ):
                lines_removed[line_i-1]=1
            if line_i==last_line:
               num_empty=1
               if last_empty_line>=1 and num_empty<=2 and self.empty_flag(last_empty_line-1)==1:
                  num_empty+=1
             #  print('pratyush1999', "pgno:", self.pgno, "last_empty_line:", last_empty_line, "line_i:", line_i,"num_empty:", num_empty, "empty_flag[last_empty_line]:",empty_flag[last_empty_line])
               if num_empty>=2 and last_empty_line!=-1 and first_split==1:
                 for i in range(last_empty_line+1,line_i+1,1):
                    #print("pratyush1999", "pgno:", self.pgno, all_lines[i])
                    lines_removed[i-1]=1

        return lines_removed, maxlnline   
    def check_split(self, split_wspce, lines_removed_preprocess):
        first_column=""
        second_column=""
        prev=10000
        for line_i, line in enumerate(self.output, 1):
            if lines_removed_preprocess[line_i-1]:
              continue
            if line_i==len(self.output): #:and line[-1] not in line_end:
                #print(line)
                line+='.'

            # if self.pgno==10 and line_i==5:
            #     print("this line:::", split_wspce, line[:split_wspce], w_spce[52], total_lines)
            if split_wspce<len(line)-1 and line[split_wspce]==' ' and line[split_wspce+1]==' ':
                if re.search(r'\w', line[:split_wspce]) or 1:
                    if line_i-prev>=2:
                        return 0, first_column, second_column
                    prev=line_i
                first_column+=line[:split_wspce]
                first_column+='\n'
                second_column+=line[split_wspce:]
                if line[-1]!='\n':
                    second_column+='\n'
            else:
                if len(line)-1<=split_wspce:
                    second_column+='\n'
                if re.search(r'\w', line) or 1:
                    if line_i-prev>=2:
                        return 0, first_column, second_column
                    prev=line_i
                first_column+=line
                if len(line)==0 or line[-1]!='\n':
                    first_column+='\n'
        return 1, first_column, second_column
    def main(self, output, first_split=0):
            # loop through each line in corpus
        one_lines=[]
        self.output=output
        lines_for_tables=[]
        total_lines=0
        lines_removed_preprocess, maxlnline=self.clean(first_split)
        first_page_ends=[]
        second_page_ends=[]
        w_spce={}
        left_w_spce={}
        right_w_spce={}
        for line_i, line in enumerate(self.output, 1):
            line+='\n'
            if lines_removed_preprocess[line_i-1]:
              continue                
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

            if len(starts)<1:
            	continue
            if len(starts)==1 and ends[0]-starts[0]<=2:
             	pass
            else:
            	lines_for_tables.append([copy.deepcopy(starts), line, copy.deepcopy(ends), line_i])       	

            if len(starts)==1 and starts[0]>60:
             	one_lines.append([starts[0], line_i, str_curr])       
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
             outta=[]
             for key, val in w_spce.items():
                if val==w_spce[Keymax] and abs(key-int(maxlnline/2))<=25:
                    Keymax=key
                    outta.append(key)
             # print(*outta, left_w_spce[Keymax], right_w_spce[Keymax], maxlnline, abs(Keymax-int(maxlnline/2))<=25 )
             if  abs(Keymax-int(maxlnline/2))<=25 \
                     and(\
                      min(right_w_spce[Keymax],left_w_spce[Keymax])>=3*max(right_w_spce[Keymax], left_w_spce[Keymax])/4\
                      or min(left_w_spce[Keymax], right_w_spce[Keymax])>=100)\
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
                      min(left_w_spce[key], right_w_spce[key])>=3*max(right_w_spce[key], left_w_spce[key])/4\
                      or min(left_w_spce[key], right_w_spce[key])>=100)\
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
                      min(left_w_spce[key], right_w_spce[key])>=3*max(right_w_spce[key], left_w_spce[key])/4\
                      or min(left_w_spce[key], right_w_spce[key])>=100)\
                     and right_w_spce[key]>10 and left_w_spce[key]>10:
                         split_wspce=key
                   #       print("type 3:",self.pgno,"white space col key:", key, "max length of line in page:",\
                   #       maxlnline, "w_spce of key:",w_spce[key], "right_w_spce:", right_w_spce[key],\
                   #       "left_w_spce:", left_w_spce[key],"total_lines :" , total_lines, "right_w_spce of keymax:", right_w_spce[Keymax],\
                   #   "left_w_spce of keymax:", left_w_spce[Keymax],
                   # "diff bw w_spce and total_lines/total_lines:",100* abs(w_spce[Keymax]-total_lines)/total_lines)
                         break
        first_column=""
        second_column=""
        entr=1
        if split_wspce==1000 and w_spce:
             Keymax = max(w_spce, key=w_spce.get)
             for key, val in w_spce.items():
                if val==w_spce[Keymax] and abs(key-int(maxlnline/2))<=25:
                    Keymax=key
             split, temp_first_column, temp_second_column= self.check_split(Keymax, lines_removed_preprocess)
             if split:
                split_wspce=Keymax
                first_column=temp_first_column
                second_column=temp_second_column    
                entr=0
        if entr:      
          for line_i, line in enumerate(self.output, 1):
              if lines_removed_preprocess[line_i-1]:
                continue
              if line_i==len(self.output): #:and line[-1] not in line_end:
                  #print(line)
                  line+='.'

              # if self.pgno==10 and line_i==5:
              #     print("this line:::", split_wspce, line[:split_wspce], w_spce[52], total_lines)
              if split_wspce<len(line)-1 and line[split_wspce]==' ' and line[split_wspce+1]==' ':
                  first_column+=line[:split_wspce]
                  #if re.findall(r'[a-zA-Z]', line[:split_wspce]):
                 ## first_page_ends+='0'
                  # if first_column[-1]!='\n':
                  first_column+='\n'
                  #first_page_ends+='\n'
                  second_column+=line[split_wspce:]
                  #if re.findall(r'[a-zA-Z]', line[split_wspce:]):
                 # second_page_ends+='0'
                  if line[-1]!='\n':
                    second_column+='\n'
                    #second_page_ends+='\n'
              else:
                  if len(line)-1<=split_wspce:
                    second_column+='\n'
                   # second_page_ends+='0'
                  first_column+=line
                  #first_page_ends+='0'
                  if len(line)==0 or line[-1]!='\n':
                      first_column+='\n'
                    #first_page_ends+='\n'
        # for line in lines_removed:
           # #print(line)
  ##print("removed lines")
 
        #print("final lines")
        # final_lines=""
        # for line_i, line in enumerate(self.output, 1):
        #     if line_i not in lines_removed:
        #       line = re.sub(r'\uf0b7','',line)
        #       final_lines+=line
        #       final_lines+='\n'
        if first_column:
          z=0       
          while first_column and (first_column[-1]=='\n' or first_column[-1]==' '):
            # print(z)
            # z+=1
            first_column=first_column[:-1]
            # first_page_ends.pop()
          first_column+='\n'
        if second_column:
          while len(second_column)>=2 and (second_column[-1]=='\n' or second_column[-1]==' '):
            second_column=second_column[:-1]
            # second_page_ends.pop()
          #if second_column[-1]!='\n':
          if second_column[-1]!='\n':
            second_column+='\n'
          # else:
   #         second_column='\n'
        for line in first_column.splitlines():
            first_page_ends.append(0)
        for line in second_column.splitlines():
            second_page_ends.append(0)
        if first_page_ends:
          first_page_ends[-1]=1
        if second_page_ends:
          second_page_ends[-1]=1
        return first_column, second_column, first_page_ends, second_page_ends
                #print(starts, line)
    def extract_text(self):
        final_output=""
        pg_ends=[]
        for page in range(1,self.no_pages+1):
            self.pgno=page
            command  = ['pdftotext', '-f', str(page), '-l', str(page), '-layout', self.pdf_file, '-']
            output   = subprocess.check_output(command).decode('utf8')
            #print(self.output)
            first_column, second_column, _, _=self.main(self.f1(output), 1)
            if first_column:
              first_first_column, first_second_column, pg1, pg2=self.main(self.f1(first_column), 0)
              final_output+=first_first_column
              pg_ends+=pg1
              pg_ends+=pg2
              #page_ends.
              # final_self.output+='\n'
              #if re.findall(r'\w', first_second_column):
              final_output+=first_second_column
#              final_self.output+='\n'
            if second_column:
              second_column, third_column,pg1,pg2=self.main(self.f1(second_column), 0)
              final_output+=second_column     
              pg_ends+=pg1
              pg_ends+=pg2
       
 #             final_self.output+='\n'
              final_output+=third_column           
  #            final_self.output+='\n'
            # final_self.output+=self.main(self.f1(self.output),2)
        return final_output, pg_ends#.encode('utf8')

if __name__ == '__main__':
    pdf='/home/pratyush1999/Documents/btp/Wealth Management- Relevant Documents/Industry Reports/pwc-asset-management-2020-a-brave-new-world-final.pdf'
    pdftotxt_extract=Pdf_get_pages(pdf)
    #print(pdftotxt_extract.extract_text())
    ret,_ =pdftotxt_extract.extract_text()
    print(ret)
