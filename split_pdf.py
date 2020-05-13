""" this module splits multi column pages of pdf into separate pages """
import re
import copy
import subprocess
import os
import string
import multiprocessing
from joblib import Parallel, delayed
# from multiprocessing import Pool
from tqdm import tqdm


LOG_ENABLE = os.environ["DEPLOYED"] if "DEPLOYED" in os.environ else ''

if LOG_ENABLE == "1":
    from logger import Logger
    LOG = Logger(os.getenv('LOGGER_ADDR'))

class PdfGetPages():
    """ this class makes a pdf page splitter """
    def __init__(self, pdf_file):
        """ this class is for splitting pdf pages """
        self.pdf_file = pdf_file
        self.pgno = 0
        self.output = ""
        self.all_starts = []
        self.no_pages = 0
        self.split = 0

    def get_no_pages(self):
        """ returns the number of pages in a pdf"""
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
        """ this method finds starts, ends and empty of a line """
        line += '\n'
        line = re.sub(r':', '', line)
        if end==0:
            line = re.sub(r'\u2212', '-', line)
        if line[0] == '-':  # replace hyphen if hyphen is used to signify a bulleted point
            line = str(1)+'.'+line[1:]
        line = re.sub(r'^\s*[\(]?\w+[\.\)](?=\s)', '', line)
        starts = [m.start(0) for m in re.finditer(r'(?<=(\s\s))\S', line)]
        ends = [m.start(0) for m in re.finditer(r'\S(?=((\s\s)|\n))', line)]
        if re.search(r'\S', line[0:2]):
            starts.insert(0, 0)
        if starts and ends and ends[0]-starts[0] <= 2:
            del starts[0]
            del ends[0]
        empty = len(starts)<1
       # print("debug:",all_starts[line_i-1], line)# lines_removed[line_i])
        return starts, ends, empty

    def clean(self, first_split=0):
        """ this method cleans the text """
        lines_removed = {}
        line_hyphen = 1
        # starts(index of first cha of each segment separated by > = 2 spaces)
        all_starts = []
        # all_ends = []
        empty = []
        last_line = -1
        empty.append(0)
        for line_i, line in enumerate(self.output, 1):
            starts, ends, e = self.preprocess(line, 0)
            all_starts.append(starts)
            empty.append(e)
            if e==0:
                last_line = line_i
        empty.append(1)
        emp_l = -1
        mxln = 0
        for line_i, line in enumerate(self.output, 1):
            mxln = max(mxln, len(line))
            if line_i-1 not in lines_removed:
                lines_removed[line_i-1] = 0
            if not re.search('[a-zA-Z]', line):
                lines_removed[line_i-1] = 1
            line += '\n'
            line = re.sub(r':', '', line)
            # for removing line numbers.
            line = re.sub(r'^\s*[\(]?\w+[\.\)](?=\s)', '', line)
            starts = all_starts[line_i-1]

            if not re.search(r'\S', line):
                emp_l = line_i
                # lines_removed[line_i-1] = 1
                continue

            if line_i >= 2 and line_i+3 < len(empty) and \
                    (len(starts) == 1) and len(all_starts[line_i]) == 1 \
                    and ((empty[line_i-1] == 1
                          and empty[line_i-2] == 1 and empty[line_i+2] == 1) or
                         (empty[line_i-1] == 1 and empty[line_i+2] == 1 and
                          empty[line_i+3] == 1)):
                lines_removed[line_i-1] = 1
                lines_removed[line_i] = 1

            if line_i >= 2 and line_i+2 < len(empty) and \
                len(starts) == 1 and ((empty[line_i-1] == 1 and empty[line_i-2] == 1 and
                                       empty[line_i+1] == 1) ):
                lines_removed[line_i-1] = 1
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
        """ this method checks if the page can be split """
        first_col = ""
        second_col = ""
        prev = 10000
        for line_i, line in enumerate(self.output, 1):
            if lines_removed_preprocess[line_i-1]:
                continue
            line = re.sub(r'\u2013', '-', line)
            line = re.sub(r'\u2014', '-', line)
            line = re.sub(r'\u201c', '"', line)
            line = re.sub(r'\u201d', '"', line)
            line = re.sub(r'\u2019', "'", line)
            line = re.sub(f'[^{re.escape(string.printable)}]', '', line)
            line = re.sub(r'^\s*\w ', '', line)
            if spl_spce < len(line)-1 and line[spl_spce] == ' ' and line[spl_spce+1] == ' ':
                if re.search(r'\w', line[:spl_spce]) or 1:
                    if line_i-prev >= 2:
                        return 0, first_col, second_col
                    prev = line_i
                first_col += line[:spl_spce]
                first_col += '\n'
                second_col += line[spl_spce:]
                if line[-1] != '\n':
                    second_col += '\n'
            else:
                if len(line)-1 <= spl_spce:
                    second_col += '\n'
                if re.search(r'\w', line) or 1:
                    if line_i-prev >= 2:
                        return 0, first_col, second_col
                    prev = line_i
                first_col += line
                if len(line) == 0 or line[-1] != '\n':
                    first_col += '\n'
        return 1, first_col, second_col

    def find_spl_spce(self, l_spce, r_spce, w_spce, mxln):
        spl_spce = 1000
        if w_spce:
            key_max = max(w_spce, key=w_spce.get)
            sorted(w_spce.items(), key=lambda x: x[1], reverse=True)
            for key, val in w_spce.items():
                if val == w_spce[key_max] and abs(key-int(mxln/2)) <= 25:
                    key_max = key
            if abs(key_max-int(mxln/2)) <= 25 \
                    and(
                            min(r_spce[key_max], l_spce[key_max]) >= 3 *
                            max(r_spce[key_max], l_spce[key_max])/4
                            or min(l_spce[key_max], r_spce[key_max]) >= 100)\
            and r_spce[key_max] > 10 and l_spce[key_max] > 10:
                spl_spce = key_max
            else: 
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
                        spl_spce = key
                        break
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
        first_col = ""
        second_col = ""
        entr = 1
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
        w_spce = {}  # stores the dictoionary of no of lines having whitespace at an index
        l_spce = {}
        r_spce = {}
        for line_i, line in enumerate(self.output, 1):
            line += '\n'
            if lines_removed_preprocess[line_i-1]:
                continue
            for i, letter in enumerate(line):
                if letter != " ":
                    continue
                if i >= 10 and i < len(line)-10 and line[i+1] == " ":
                    nofwords = len(re.findall(r'\S(?=(\s))', line[:i]))
                    if i not in l_spce:
                        l_spce[i] = 0
                    l_spce[i] += nofwords

                    nofwords = len(re.findall(r'\S(?=(\s))', line[i:]))
                    if i not in r_spce:
                        r_spce[i] = 0
                    r_spce[i] += nofwords

                    if i not in w_spce:
                        w_spce[i] = 0
                    w_spce[i] += 1
            for i in range(len(line)-10, mxln-10):
                if i >= 10 and i not in w_spce:
                    w_spce[i] = 0
                if i not in l_spce:
                    l_spce[i] = 0

                if i not in r_spce:
                    r_spce[i] = 0
                if i >= 10:
                    w_spce[i] += 1
                    l_spce[i] += len(re.findall(r'\S(?=(\s))', line[:i]))
        return l_spce, r_spce, w_spce
    def main(self, output, first_split=0):
        """ the main function which returns the splitted pdf pages"""
        self.output = output
        line_end = [':', ',', '.', ';']
        lines_removed_preprocess, mxln = self.clean(first_split)
        first_page_ends = []
        second_page_ends = []
        l_spce, r_spce, w_spce = self.find_spce_dicts(lines_removed_preprocess, mxln)
        spl_spce = self.find_spl_spce(l_spce, r_spce, w_spce, mxln)
        first_col, second_col = self.getcols(w_spce, lines_removed_preprocess, spl_spce, mxln)
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
        """ the caller function splits the given page """
        self.get_no_pages()
        final_output = ""
        pg_ends = []
        self.pgno = page
        command = ['pdftotext', '-f',
                   str(page), '-l', str(page), '-layout', self.pdf_file, '-']
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
        """ this method is the caller function for each page """
        self.get_no_pages()
        final_output = ""
        pg_ends = []
        num_cores = multiprocessing.cpu_count()
        final_output_list = Parallel(n_jobs=num_cores )(delayed(self.extract_page)(page)
                                                               for page in range(1, self.no_pages+1)) 
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