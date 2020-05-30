"""Splits multi column pages of pdf into separate pages."""
import re
import subprocess
import os
import string
import multiprocessing
# from joblib import Parallel, delayed


LOG_ENABLE = os.environ["DEPLOYED"] if "DEPLOYED" in os.environ else ''

if LOG_ENABLE == "1":
    from logger import Logger
    LOG = Logger(os.getenv('LOGGER_ADDR'))

class PdfGetPages():
    """Makes a pdf page splitter."""
    def __init__(self, pdf_file):
        """For splitting pdf pages.
            pdf_file: the path of the pdf document.
        """
        self.pdf_file = pdf_file
        self.pgno = 0   #current page number
        self.output = "" #raw text input
        self.all_starts = []   #list of all starts of all lines(starts is defined in later methods)
        self.no_pages = 0 #no of pages in pdf

    def get_no_pages(self):
        """Returns the number of pages in a pdf."""
        try:
            pdf_info = subprocess.Popen(
                ('pdfinfo', self.pdf_file), stdout=subprocess.PIPE)
        except:
            if LOG_ENABLE == "1":
                LOG.error('pdf_to_txt', 'POST', 'NULL', 'NULL', "error in getting information of the pdf")
            print("error in getting information of the pdf")
            return
        try:
            self.no_pages = int(subprocess.check_output(
                ('grep', '-oP', '(?<=Pages:          )[ A-Za-z0-9]*'), stdin=pdf_info.stdout))
        except:
            if LOG_ENABLE == "1":
                LOG.error('pdf_to_txt', 'POST', 'NULL', 'NULL', "error in getting information of the pdf")
            print("error in getting information of the pdf")

    @classmethod
    def preprocess(self, line, end=0):
        """Finds starts, ends and empty of a line.
            starts(index of first character of each segment separated by > = 2 spaces)
            ends(index of last character of each segment separated by > = 2 spaces)
        """
        line += '\n'
        line = re.sub(r':', '', line)
        if end==0:
            line = re.sub(r'\u2212', '-', line)
        if line[0] == '-':  # Replace hyphen if hyphen is used to signify a bulleted point.
            line = str(1)+'.'+line[1:]
        line = re.sub(r'^\s*[\(]?\w+[\.\)](?=\s)', '', line)
        #Segment the line with double space as segmenter and find the starting and ending position of each segment
        starts = [m.start(0) for m in re.finditer(r'(?<=(\s\s))\S', line)]
        ends = [m.start(0) for m in re.finditer(r'\S(?=((\s\s)|\n))', line)]
        #If the 0th position is the starting point of some segment, add it also.
        if re.search(r'\S', line[0:2]):
            starts.insert(0, 0)
        #If the first segmment is very small, it is most likely of the form A. or 1. representing a numbered point.
        #But such a segment is undesirable as it is a part of the line which it is numbering. 
        #Hence, it should be removed.
        if starts and ends and ends[0]-starts[0] <= 2:
            del starts[0]
            del ends[0]
        #If a line doesn't have any thing in starts, it should be empty.
        empty = len(starts)<1
        return starts, ends, empty

    def clean(self, first_split=0):
        """Cleans the text.
            first_split: if it is true, it means the page is being split for the first time.
        """
        lines_removed = {} #Stores a boolean flag for each line representing if the line is removed or not.
        all_starts = [] #Stores starts of all lines.
        empty = []    #Stores a boolean flag denoting if a line is empty.
        last_line = -1 #Denotes the index of last non empty line
        empty.append(0)
        for line_i, line in enumerate(self.output, 1):
            starts, _, e = self.preprocess(line, 0)
            all_starts.append(starts)
            empty.append(e)
            if e==0:
                last_line = line_i
        empty.append(1)
        emp_l = -1 #Stores the last empty line index.
        mxln = 0
        for line_i, line in enumerate(self.output, 1):
            mxln = max(mxln, len(line)) #Stores the maximum length of a line.
            if line_i-1 not in lines_removed:
                lines_removed[line_i-1] = 0 
            if not re.search('[a-zA-Z]', line):
                lines_removed[line_i-1] = 1 #Removes lines with all capital letters which would be most likely a heading/
            line += '\n'
            line = re.sub(r':', '', line)
            line = re.sub(r'^\s*[\(]?\w+[\.\)](?=\s)', '', line) # For removing line numbers. Checks for (1.) or 1. or A.
                                                                # form of numbers
            starts = all_starts[line_i-1]

            if not re.search(r'\S', line):
                emp_l = line_i #if there is no non space chracter in the line , then it is empty.
                # lines_removed[line_i-1] = 1
                continue

            #if the line has just 1 segment if delimited by double space, this means it is a whole line and not 2 lines of
            #separate columns. For such lines, if the next line is also whole and 2 lines previous to the current are empty 
            #and the next line after this block of 2 lines is empty, this implies this block of 2 lines is likely to be an image
            #caption as normal lines wouldn't be separated from the other text by 2 empty lines. Same logic would apply if the block
            #of 2 lines is separated by 2 lines at the bottom and 1 line at the top.
            if line_i >= 2 and line_i+3 < len(empty) and \
                    (len(starts) == 1) and len(all_starts[line_i]) == 1 \
                    and ((empty[line_i-1] == 1
                          and empty[line_i-2] == 1 and empty[line_i+2] == 1) or
                         (empty[line_i-1] == 1 and empty[line_i+2] == 1 and
                          empty[line_i+3] == 1)):
                lines_removed[line_i-1] = 1
                lines_removed[line_i] = 1
            #If a whole line is seprated by 2 lines at the top and 1 line at the bottom, then it is likely to be an image caption.
            if line_i >= 2 and line_i+2 < len(empty) and \
                len(starts) == 1 and ((empty[line_i-1] == 1 and empty[line_i-2] == 1 and
                                       empty[line_i+1] == 1) ):
                lines_removed[line_i-1] = 1
            #Footer detection code. The block of lines from the last empty  line to the last non empty line should
            #make up the footer. But to avoid detecting a main part of text, if the length of the block is >12, do not
            #consider it as a footer. Detection of footer should happen only in the first split of the page. 
            if line_i == last_line:
                num_empty = 1
                if emp_l >= 1 and num_empty <= 2 and empty[emp_l-1] == 1:
                    num_empty += 1
                if num_empty >= 2 and emp_l != -1 and first_split == 1 and line_i-emp_l <= 12:
                    for i in range(emp_l+1, line_i+1, 1):
                        lines_removed[i-1] = 1
        self.all_starts = all_starts
        return lines_removed, mxln

    def check_split(self, spl_spce, lines_removed_preprocess):
        """Checks if the page can be split by a particular index.
            spl_spce: the splitting index
            lines_removed_preprocess: contains the lines which are to be removed
        """
        first_col = ""
        second_col = ""
        prev = 10000 #stores the last non-removed line encountered
        for line_i, line in enumerate(self.output, 1):
            if lines_removed_preprocess[line_i-1]:
                continue
            line = re.sub(r'\u2013', '-', line)
            line = re.sub(r'\u2014', '-', line)
            line = re.sub(r'\u201c', '"', line)
            line = re.sub(r'\u201d', '"', line)
            line = re.sub(r'\u2019', "'", line)
            line = re.sub(f'[^{re.escape(string.printable)}]', '', line) #remove all non printable characters.
            if spl_spce < len(line)-1 and line[spl_spce] == ' ' and line[spl_spce+1] == ' ':
                if line_i-prev >= 2:              
                    return 0, first_col, second_col  #a block of text should not be separated by more than 2 lines.
                prev = line_i
                first_col += line[:spl_spce]
                first_col += '\n'
                second_col += line[spl_spce:]
                if line[-1] != '\n':
                    second_col += '\n'
            else:
                if len(line)-1 <= spl_spce:
                    second_col += '\n'
                if line_i-prev >= 2:
                    return 0, first_col, second_col
                prev = line_i
                first_col += line
                if len(line) == 0 or line[-1] != '\n':
                    first_col += '\n'
        return 1, first_col, second_col
    @classmethod
    def find_spl_spce(self, l_spce, r_spce, w_spce, mxln):
        """Finds the column delimiter space.
            l_spce: the no of words to the left of a split index.
            r_spce: the no of words to the right of a split index.
            w_spce: the no of lines having an index as empty space.
            mxln: max length of a line.
        """
        spl_spce = 1000 #split index is initialised with a large value
        if w_spce:
            key_max = max(w_spce, key=w_spce.get)   #The index which is empty in most lines is a good candidate for split index
            sorted(w_spce.items(), key=lambda x: x[1], reverse=True)
            for key, val in w_spce.items():
                if val == w_spce[key_max] and abs(key-int(mxln/2)) <= 25:
                    key_max = key#The key of w_spce which has the max value and is loated reasonably close to the mid point 
                                    #is a better cadidate for split index.
            if abs(key_max-int(mxln/2)) <= 25 \
                    and(
                            min(r_spce[key_max], l_spce[key_max]) >= 3 *
                            max(r_spce[key_max], l_spce[key_max])/4
                            or min(l_spce[key_max], r_spce[key_max]) >= 100)\
            and r_spce[key_max] > 10 and l_spce[key_max] > 10:  #if the 2 columns have similar no of words and each column is
                spl_spce = key_max                               #reasonably filled.
            else:#Now, we would have to choose some other index which performs better split.
                dict_list = []
                for key, val in w_spce.items():
                    dict_list.append([key, val])
                dict_list = sorted(dict_list, key=lambda x: x[1], reverse=True)
                for key, val in dict_list:
                    if val >= w_spce[key_max]-5 and abs(key-int(mxln/2)) <= int(mxln/5)\
                            and(
                                    min(l_spce[key], r_spce[key]) >= 3 *
                                    max(r_spce[key], l_spce[key])/4
                                    or min(l_spce[key], r_spce[key]) >= 100)\
                                    and r_spce[key] > 10 and l_spce[key] > 10:
                        spl_spce = key        #if the key splits a very large no of lines and follows the conditions of a max
                        break                   #key then it is a good candidate key.
                    if val >= w_spce[key_max]-15 and abs(key-int(mxln/2)) <= int(mxln/5)\
                            and(
                                    min(l_spce[key], r_spce[key]) >= 3 *
                                    max(r_spce[key], l_spce[key])/4
                                    or min(l_spce[key], r_spce[key]) >= 100)\
                                    and r_spce[key] > 10 and l_spce[key] > 10:
                        spl_spce = key
                        break
        return spl_spce
    def getcols(self, w_spce, lines_removed_preprocess, spl_spce, mxln):
        """Splits text into columns.
            w_spce: the no of lines having an index as empty space.
            lines_removed_preprocess: contains the lines which are to be removed
            spl_spce: the splitting index
            mxln: max length of a line.
        """
        first_col = ""
        second_col = ""
        if spl_spce == 1000 and w_spce:
            key_max = max(w_spce, key=w_spce.get)
            for key, val in w_spce.items():
                if val == w_spce[key_max] and abs(key-int(mxln/2)) <= 25:
                    key_max = key
            split, temp_first_col, temp_second_col = self.check_split(
                key_max, lines_removed_preprocess)
            if split:
                spl_spce = key_max
                return temp_first_col, temp_second_col
        for line_i, line in enumerate(self.output, 1):
            if lines_removed_preprocess[line_i-1]:
                continue
            if spl_spce < len(line)-1 and line[spl_spce] == ' ' and line[spl_spce+1] == ' ':
                first_col += line[:spl_spce]
                first_col += '\n'
                second_col += line[spl_spce:]
                if line[-1] != '\n':
                    second_col += '\n'
            else:
                if len(line)-1 <= spl_spce:
                    second_col += '\n'
                first_col += line
                if len(line) == 0 or line[-1] != '\n':
                    first_col += '\n'
        return first_col, second_col
    def find_spce_dicts(self, lines_removed_preprocess, mxln):
        """Finds dictionanry of left, right and white space.
            lines_removed_preprocess: contains the lines which are to be removed
            mxln: max length of a line.
        """
        w_spce = {}  # stores the dictoionary of no of lines having whitespace at an index
        l_spce = {}  #the no of words to the left of a split index.
        r_spce = {}   #the no of words to the right of a split index.
        for line_i, line in enumerate(self.output, 1):
            line += '\n'
            if lines_removed_preprocess[line_i-1]:
                continue
            for i, letter in enumerate(line):
                if letter != " ":
                    continue
                #i should be in a range as start and end of a line might have whitespace and the split index
                # should not be at the fringes
                if i >= 10 and i < len(line)-10 and line[i+1] == " ": 
                    nofwords = len(re.findall(r'\S(?=(\s))', line[:i])) #no of words in a line till ith index.
                    if i not in l_spce:
                        l_spce[i] = 0
                    l_spce[i] += nofwords #no of words to the left of i in the line.

                    nofwords = len(re.findall(r'\S(?=(\s))', line[i:]))
                    if i not in r_spce:
                        r_spce[i] = 0
                    r_spce[i] += nofwords #no of words to the right of i in the line.

                    if i not in w_spce:
                        w_spce[i] = 0
                    w_spce[i] += 1  #as this line has whitespace at ith position.
            #if the len of current line < mxln
            for i in range(len(line)-10, mxln-10):
                if i >= 10 and i not in w_spce:
                    w_spce[i] = 0
                if i not in l_spce:
                    l_spce[i] = 0

                if i not in r_spce:
                    r_spce[i] = 0 #as all the positions in this loop are assumed as witespace in the line.
                if i >= 10:
                    w_spce[i] += 1
                    l_spce[i] += len(re.findall(r'\S(?=(\s))', line[:i]))
        return l_spce, r_spce, w_spce
    def main(self, output, first_split=0):
        """Returns the splitted pdf pages.
            output: raw text input
            first_split: if it is true, it means the page is being split for the first time.
        """
        self.output = output
        lines_removed_preprocess, mxln = self.clean(first_split)
        first_page_ends = [] #boolean flags denoting if the line is the last line of the first column of the page.
        second_page_ends = [] #boolean flags denoting if the line is the last line of the second column of the page.
        l_spce, r_spce, w_spce = self.find_spce_dicts(lines_removed_preprocess, mxln)
        spl_spce = self.find_spl_spce(l_spce, r_spce, w_spce, mxln)
        first_col, second_col = self.getcols(w_spce, lines_removed_preprocess, spl_spce, mxln)
        #remove whitespaces at the end of first_col and second_col.
        if first_col:
            while first_col and (first_col[-1] == '\n' or first_col[-1] == ' '):
                first_col = first_col[:-1]
            first_col += '\n'
        if second_col:
            while len(second_col) >= 2 and (second_col[-1] == '\n' or second_col[-1] == ' '):
                second_col = second_col[:-1]
            if second_col[-1] != '\n':
                second_col += '\n'
        first_page_ends = [0 for line in first_col.splitlines()]
        second_page_ends = [0 for line in second_col.splitlines()]
        if first_page_ends:
            first_page_ends[-1] = 1
        if second_page_ends:
            second_page_ends[-1] = 1
        return first_col, second_col, first_page_ends, second_page_ends
    
    def extract_page(self, page):
        """Splits the given page.
            page: page number of the document.
        """
        final_output = ""
        pg_ends = [] #boolean flags denoting if the line is the last line of the first column of the page.
        self.pgno = page
        command = ['pdftotext', '-f',
                   str(page), '-l', str(page), '-layout', self.pdf_file, '-']#run pdftoext on the document.
        try:
            output = subprocess.check_output(command).decode('utf8')
            output = re.sub(r'  [a-z]  ','', output)
            output = re.sub(r'\n[a-z] ','\n', output)
            output = re.sub(r'\*', '', output)
        except Exception as e:
            if LOG_ENABLE == "1":
                LOG.error('pdf_to_txt', 'POST', 'NULL', 'NULL', "error in reading the pdf")
            print("error in running pdftotext", e)
            return "", []
        first_col, second_col, pg1, pg2 = self.main(
            output.splitlines(), 1)
        if first_col:
            first_first_col, first_second_col, pg1, pg2 = self.main(
                first_col.splitlines(), 0)
            final_output += first_first_col
            pg_ends += pg1
            pg_ends += pg2
            final_output += first_second_col
        if second_col:
            second_col, third_column, pg1, pg2 = self.main(
                second_col.splitlines(), 0)
            final_output += second_col
            pg_ends += pg1
            pg_ends += pg2
            final_output += third_column
        return final_output, pg_ends
    def extract_text(self):
        """Caller function for each page."""
        self.get_no_pages()
        final_output = ""
        pg_ends = []
        num_cores = multiprocessing.cpu_count()
        pool = multiprocessing.Pool()
        final_output_list = pool.map(self.extract_page, range(1, self.no_pages+1))
        pool.close()
        for text, pg_end in final_output_list:
            final_output += text
            pg_ends += pg_end

        return final_output, pg_ends

if __name__ == '__main__':
    PDF = '/home/pratyush1999/Documents/btp/Wealth Management- Relevant Documents/Industry Reports/Wealth-Management-in-India-Challenges-and-Strategies.pdf'
    pdftotxt_extract = PdfGetPages(PDF)
    # print(pdftotxt_extract.extract_text())
    RET, _ = pdftotxt_extract.extract_text()
    print(RET)
