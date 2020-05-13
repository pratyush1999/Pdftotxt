""" this code extracts text from pdfs """
import re
import copy
import string
from split_pdf import PdfGetPages
#import os
import nltk.data
# import language_tool_python
# from multiprocessing import Pool
from joblib import Parallel, delayed
import multiprocessing
import time

class PdfTxtExtract():
    """ this class performs text extraction on pdfs """

    def __init__(self, pdf_file):
        """ this class is the text extracter class"""
        self.pdf_file = pdf_file
        self.no_pages = 0
        self.pgno = 0
        self.dict_output_list = {}
        self.output = ""
    def check(self, list1, list2, flag=0):
        """This method is an addon on the table detection function."""
        st1 = copy.deepcopy(list1)
        st2 = copy.deepcopy(list2)
        while len(st2) < len(st1) and abs(st1[0]-st2[0]) > 5:
            del st1[0]
        while len(st1) < len(st2) and abs(st1[0]-st2[0]) > 5:
            del st2[0]
        for i, j in zip(st1, st2):
            if max(i, j)-min(i, j) > 5+flag:
                return False
        return True

    def init_clean(self, line):
        """ does basic cleaning of line"""
        line += '\n'
        line = re.sub(r':', '', line)
        return line
    def check_roman(self, line):
        """checks if the first word of the line is a roman numeral"""
        roman_nums=['x','X','v','V','i','I']
        i=0
        fl=1
        if line[i]=='(':
            i+=1
        while i<len(line) and line[i].isalpha():
           if line[i] not in roman_nums:
               #print(line, line[i])
               fl=0
           i+=1
        return (fl) or (i<=3)
    def last_word(self, line):
        """ checks if the last word is a possible end word of a line """
        non_ends=['the', 'or', 'and', 'by', 'with', 'of', 'in', 'for', 'your', 'under', 'to', 'very','/','-', 'Global']
        line=line.rstrip().lstrip()
        i1 = len(line)-1
        i2 = len(line)-1
        last_letter=line[-1].lstrip().rstrip()
        if len(line)>=2 and line[-2].lstrip().rstrip()=='/' and last_letter=='-':
            return 1
        # print(line, "last letter::", line[i1], last_letter=='/')
        if last_letter in non_ends:
            return 0
        while i1>0 and not line[i1].isalpha():
            i1 -= 1
            i2 -= 1

        while i2>0 and line[i2].isalpha():
            i2 -= 1
        if not line[i2].isalpha():
            i2 += 1
        last_word=line[i2:i1+1].lstrip().rstrip().lower()
        #print(line, "LAST WORD:", last_word, last_word in non_ends)
        return not last_word in non_ends
    def detect_table(self, l_table, lines_removed, maxx):
        # table detection method
        i = 1
        while i < len(l_table):
            j = i
            if len(l_table[i][0]) == 1:
                i += 1
                continue
            # print('--------------------------------------------------------------------------')
            #print("table starts")
            tble_f = 0
            while j < len(l_table) and (self.check(l_table[j][0], l_table[i][0]) or
                                        self.check(l_table[i][0], l_table[j][0]) or
                                        self.check(l_table[j][0], l_table[j-1][0]) or
                                        self.check(l_table[j-1][0], l_table[j][0]) or
                                        self.check(l_table[j][0], l_table[j-2][0]) or
                                        self.check(l_table[j-2][0], l_table[j][0])):
                if len(l_table[j][0]) == 1 and l_table[j][0][0] <= 10 and \
                        l_table[j][2][0]-l_table[j][0][0] >= 0.6*maxx:
                    tble_f = 1
                    break
                #print("table line",l_table[j][1])
                j += 1
                lines_removed[l_table[j-1][3]] = 5
            if j == i+1 and tble_f == 0:
                i = j
            while j < len(l_table) and (self.check(l_table[j][0], l_table[i][0]) or
                                        self.check(l_table[i][0], l_table[j][0]) or
                                        self.check(l_table[j][0], l_table[j-1][0]) or
                                        self.check(l_table[j-1][0], l_table[j][0]) or
                                        self.check(l_table[j][0], l_table[j-2][0]) or
                                        self.check(l_table[j-2][0], l_table[j][0])):
                if len(l_table[j][0]) == 1 and l_table[j][0][0] <= 10 and \
                        l_table[j][2][0]-l_table[j][0][0] >= 0.6*maxx:
                    break
                #print("table line",l_table[j][1])
                j += 1
                lines_removed[l_table[j-1][3]] = 6
            # print('--------------------------------------------------------------------------')
            #print("table ends")
            i = j
        return lines_removed
    def final_lines(self, lines_removed, pg_ends, empty):
        final_lines = ""
        line_hyphen = 1
        bullets = ['-']
        line_end = [':', ',', '.', ';']
        pg_ends_ret = []  # boolean values signifying if the line is the last line of the page
   #     for line_i, line in enumerate(output, 1):
        # if line_i in lines_removed:
        output = self.output
        for line_i, line in enumerate(output, 1):
            if line_i not in lines_removed:
                if pg_ends:
                    pg_ends_ret.append(pg_ends[line_i-1])
                line = line.rstrip()
                line = line.lstrip()
                # add upper case lines as well to the output.
                line = re.sub(r'^(?<=[0-9])\s', '.', line)
                if (line.isupper() or (not re.search(r'[a-zA-Z]', line))) \
                        and (line[-1] not in line_end):
                    line += '.'
                line = re.sub(r'\u2013', ':', line)
                line = re.sub(r';', '.', line)
                # code for adding full stop at end of unpunctuated lines
                if len(line) >= 2 and line[0].isalpha() and line[1] == ')':
                    line = line[0]+'.'+line[2:]
                if line and line[0] == '-':
                    # print(line)
                    next_ind = 1
                    if len(line) >= 2 and line[1] == '-':
                        next_ind = 2
                    line = str(line_hyphen)+'.'+line[next_ind:]
                    line_hyphen += 1
                elif line and line_i < len(output) and (len(line) <= 2 or line[-2] in line_end)\
                        and self.init_clean(output[line_i]) not in bullets:
                    line_hyphen = 1
                line = line.rstrip()
               # or  re.findall(r'^\s*[A-Z]', self.init_clean(output[line_i]))
                if line_i < len(output) and \
                    (re.search(r'^\s*[A-Z]', self.init_clean(output[line_i]))) \
                    and (line[-1] not in line_end and self.last_word(line))\
                    and (len(line) <= len(self.init_clean(output[line_i]))-10 or
                         len(line) >= len(self.init_clean(output[line_i]))-10):
                    line += "."
                if line_i < len(output) and \
                    (re.search(r'^[\(]?\w+[\.\)]', self.init_clean(output[line_i])) and self.check_roman(output[line_i])) \
                        and (line[-1] not in line_end):
                    line += "."
                elif line_i < len(output) and (line_i+1 in lines_removed and not empty[line_i+1]) and (line[-1] not in line_end) \
                    and self.last_word(line):
                    line += '.'
                # if not self.last_word(line):
                #     lines_removed.pop(self.add_line(line_i, lines_removed), None)
                # removes non printable characters from a string
                #line = re.sub(f'[^{re.escape(string.printable)}]', '', line)
                final_lines += line
                final_lines += ' '
                final_lines += '\n'

            elif (line_i in lines_removed) and (line_i+2 in lines_removed):
                lines_removed[line_i+1]=1
        return final_lines, pg_ends_ret

    def main(self, output, pg_ends):
        """ the main function which returns the clean text"""
        self.output = output
        start_time = time.time()
        lines_removed = {}  # lines and line indices which are removed from input
        l_table = []  # stores lines which are part of table
        maxx = 0  # stores the max length of line
        empty = []  # stores  boolean values signifying if the line is empty
        empty.append(0)
        all_starts = []
        all_ends = []
        line_hyphen = 1
        num_cores = multiprocessing.cpu_count()
        for line in output:
            starts, ends, e = PdfGetPages.preprocess(line, 1)
            all_starts.append(starts)
            all_ends.append(ends)
            empty.append(e)
        empty.append(1)

        for line_i, line in enumerate(output, 1):
            line += '\n'
            line = re.sub(r':', '', line)
            # for removing line numbers.
            line = re.sub(r'^\s*[\(]?\w+[\.\)](?=\s)', '', line)
            # stores the index of first character of each segment separated by >=2 space character)
            starts = all_starts[line_i-1]
            # stores the index of last character of each segment separated by >=2 space character)
            ends = all_ends[line_i-1]
            if ends:
                maxx = max(maxx, max(ends))
            if len(starts) < 1:
                lines_removed[line_i] = 20
                continue
            if len(starts) == 1 and ends[0]-starts[0] <= 2:
                pass
            elif len(starts) >= 2:
                l_table.append([starts, line, ends, line_i])
                if len(starts)>=3:
                    lines_removed[line_i]=22
            if line_i >= 2 and line_i+3 < len(empty) and \
                    (len(starts) == 1) and len(all_starts[line_i]) == 1 \
                    and ((empty[line_i-1] == 1
                          and empty[line_i-2] == 1 and empty[line_i+2] == 1) or
                         (empty[line_i-1] == 1 and empty[line_i+2] == 1 and
                          empty[line_i+3] == 1)):
                if pg_ends and pg_ends[line_i-1] == 0 and pg_ends[line_i] == 0:
                    lines_removed[line_i] = 3
                    lines_removed[line_i+1] = 3  # for hadling image caption
            if line_i >= 2 and line_i+2 < len(empty) and \
                len(starts) == 1 and ((empty[line_i-1] == 1 and empty[line_i-2] == 1 and
                                       empty[line_i+1] == 1) or
                                      (empty[line_i-1] == 1 and empty[line_i+1] == 1 \
                                       and empty[line_i+2] == 1)):
                if pg_ends and pg_ends and pg_ends[line_i-1] == 0:
                    lines_removed[line_i] = 4  # for hadling image caption
        lines_removed=self.detect_table(l_table, lines_removed, maxx)
        final_lines, pg_ends_ret = self.final_lines(lines_removed, pg_ends, empty)
        return final_lines, pg_ends_ret
    def del_broken_l(self, final_output, output):
        """ this method removes broken lines from text """
        tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
        final_output_list = tokenizer.tokenize(final_output)
        output_list = tokenizer.tokenize(output)
        dict_output_list = {}
        for item in output_list:
            if item not in dict_output_list:
                dict_output_list[item] = 1
            else:
                dict_output_list[item] += 1
        dict_final_output_list = {}
        for item in final_output_list:
            if item not in dict_final_output_list:
                dict_final_output_list[item] = 1
            else:
                dict_final_output_list[item] += 1
        final_output = ""
        for line in final_output_list:
            if line in dict_output_list and len(line.split())>=5 and len(line.split())<60 and re.search(r'[A-Z]', line[0])\
             and dict_final_output_list[line]==1:
                line = re.sub(r'\u2014', '-', line)
                line = re.sub(r'\u201c', '"', line)
                line = re.sub(r'\u201d', '"', line)
                line = re.sub(r'\u2019', "'", line)
                line = re.sub(f'[^{re.escape(string.printable)}]', '', line)
                final_output += line
                final_output += ' '
        return final_output

    def extract_text(self):
        """ the caller function for calling the main function """
        pdftotxt_extract = PdfGetPages(self.pdf_file)
        pdftotxt_extract.split = 1
        output, pg_ends = pdftotxt_extract.extract_text()
        output = re.sub(r'(?<=[a-z])\.[0-9]+', '.', output)
        output = re.sub(r'(?<=\s{5})[0-9]+(?=\s)','', output)
        output = re.sub(r'(?<=\s)[0-9]+(?=\s{7})','', output)
        output = re.sub(r'\u2212', '-', output)
        output = re.sub(r'\u2022', '-', output)
        final_output, pg_ends = self.main(output.splitlines(), pg_ends)
        final_output, _ = self.main(
            final_output.splitlines(), pg_ends)  # .encode('utf8')
        final_output = re.sub(r' \. ', '   ', final_output)
        final_output = re.sub(r'\n', '', final_output)
        final_output = re.sub(r'\. \.', '.', final_output)        
        final_output = re.sub(r'[ \n]+',' ', final_output)
        output = re.sub(r'[ \n]+',' ', output)
        final_output = self.del_broken_l(final_output, output)
        return final_output 


if __name__ == '__main__':
    # PDF = '/home/pratyush1999/Documents/btp/large.pdf'
    PDF = '/home/pratyush1999/Documents/btp/Wealth Management- Relevant Documents/Product Documents/IDFC-Asset-Allocation-Fund-of-Fund_07162018011346-1.pdf'
    Pdftxt_Extract = PdfTxtExtract(PDF)
    #Pdftxt_Extract.extract_text()
    print(Pdftxt_Extract.extract_text())
    #print("{\"content\":\"", Pdftxt_Extract.extract_text(), "\" , \"summary_percentage\": 100}")
    # output   = subprocess.check_output(command).decode('utf8')
    # print(output)
