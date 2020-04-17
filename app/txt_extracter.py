""" this code extracts text from pdfs """
import re
import copy
import string
from split_pdf import PdfGetPages
#import os


class PdfTxtExtract():
    """ this class performs text extraction on pdfs """

    def __init__(self, pdf_file):
        """ this class is the text extracter class"""
        self.pdf_file = pdf_file
        self.no_pages = 0
        self.pgno = 0

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

    def main(self, output, pg_ends):
        """ the main function which returns the clean text"""
        lines_removed = {}  # lines and line indices which are removed from input
        l_table = []  # stores lines which are part of table
        maxx = 0  # stores the max length of line
        empty = []  # stores  boolean values signifying if the line is empty
        empty.append(0)
        all_starts = []
        all_ends = []
        line_hyphen = 1
        line_end = [':', ',', '.', ';']
        pg_ends_ret = []  # boolean values signifying if the line is the last line of the page
        for line_i, line in enumerate(output, 1):
            line += '\n'
            line = re.sub(r':', '', line)
            if line[0] == '-':  # replace hyphen if hyphen is used to signify a bulleted point
                line = str(line_hyphen)+'.'+line[1:]
                # continue incrementing the counter for the next point.
                line_hyphen += 1
          #  f = 0
            # prev_temp_line=copy.deepcopy(line)
            # for removing line numbers.
            line = re.sub(r'^\s*[\(]?\w+[\.\)](?=\s)', '', line)
            # if prev_temp_line!=line:
            #     f=5                     #sets an offset for lines which have numbered points
            starts = [m.start(0) for m in re.finditer(r'(?<=(\s\s))\S', line)]
            ends = [m.start(0)
                    for m in re.finditer(r'\S(?=((\s\s)|\n))', line)]
            if re.search(r'\S', line[0:2]):
                starts.insert(0, 0)
            if starts and ends and ends[0]-starts[0] <= 2:
                del starts[0]
                del ends[0]
            all_starts.append(starts)
            all_ends.append(ends)
           # print("debug:",all_starts[line_i-1], line)# lines_removed[line_i])
            if len(starts) < 1:
                # print(line)
                empty.append(1)
                continue
            empty.append(0)
        empty.append(1)
        #print("true or not:", len(all_starts)==len(output))
        for line_i, line in enumerate(output, 1):
            line += '\n'
            line = re.sub(r':', '', line)
   #         prev_temp_line=copy.deepcopy(line)
            # for removing line numbers.
            line = re.sub(r'^\s*[\(]?\w+[\.\)](?=\s)', '', line)
            # if prev_temp_line!=line:
            #     f=5
            # stores the index of first character of each segment separated by >=2 space character)
            starts = all_starts[line_i-1]
            # stores the index of last character of each segment separated by >=2 space character)
            ends = all_ends[line_i-1]
         #   print("this line starts:",line, starts,"this line ends")
            if ends:
                maxx = max(maxx, max(ends))
            if len(starts) < 1:
                # print(line_i)
                lines_removed[line_i] = 20
                #print("type1", line)
                continue
            if len(starts) == 1 and ends[0]-starts[0] <= 2:
                pass
            elif len(starts) >= 2:
                l_table.append([starts, line, ends, line_i])
            if line_i >= 2 and line_i+3 < len(empty) and \
                    (len(starts) == 1) and len(all_starts[line_i]) == 1 \
                    and ((empty[line_i-1] == 1
                          and empty[line_i-2] == 1 and empty[line_i+2] == 1) or
                         (empty[line_i-1] == 1 and empty[line_i+2] == 1 and
                          empty[line_i+3] == 1)):
                if pg_ends and pg_ends[line_i-1] == 0 and pg_ends[line_i] == 0:
                    lines_removed[line_i] = 3
                    lines_removed[line_i+1] = 3  # for hadling image caption
                    #print('type2', line)
            if line_i >= 2 and line_i+2 < len(empty) and \
                len(starts) == 1 and ((empty[line_i-1] == 1 and empty[line_i-2] == 1 and
                                       empty[line_i+1] == 1) or
                                      (empty[line_i-1] == 1 and empty[line_i+1] == 1 \
                                       and empty[line_i+2] == 1)):
                if pg_ends and pg_ends and pg_ends[line_i-1] == 0:
                    lines_removed[line_i] = 4  # for hadling image caption
                    #print("type3", line)
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

        final_lines = ""
        line_hyphen = 1
        bullets = ['-']
   #     for line_i, line in enumerate(output, 1):
        # if line_i in lines_removed:
        for line_i, line in enumerate(output, 1):
           # print(line_i, line)
            line = re.sub(r'(?<=[0-9])\s', '.', line)
            if line_i not in lines_removed:
                if pg_ends:
                    pg_ends_ret.append(pg_ends[line_i-1])
                line1 = line.rstrip()
                # add upper case lines as well to the output.
                if (line.isupper() or (not re.search(r'[a-zA-Z]', line))) \
                        and (line1[-1] not in line_end):
                    line += '.'
                line = re.sub(r'\u2013', ':', line)
                line = re.sub(r';', '.', line)
                # code for adding full stop at end of unpunctuated lines
                line = line.lstrip()
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
                    and (line[-1] not in line_end)\
                    and (len(line) <= len(self.init_clean(output[line_i]))-10 or
                         len(line) >= len(self.init_clean(output[line_i]))-10):
                    line += "."
                elif line_i < len(output) and \
                    (re.search(r'^\s*[\(]?\w+[\.\)]', self.init_clean(output[line_i]))) \
                        and (line[-1] not in line_end):
                    line += "."
                # removes non printable characters from a string
                line = re.sub(f'[^{re.escape(string.printable)}]', '', line)
                final_lines += line
                final_lines += ' '
                # final_lines += '\n'
            elif (line_i in lines_removed) and (line_i+2 in lines_removed):
                lines_removed[line_i+1]=1
        return final_lines, pg_ends_ret

    def extract_text(self):
        """ the caller function for calling the main function """
        pdftotxt_extract = PdfGetPages(self.pdf_file)
        output, pg_ends = pdftotxt_extract.extract_text()
        output_orig=copy.deepcopy(output)
        output = re.sub(r'\u2212', '-', output)
        output = re.sub(r'\u2022', '-', output)
        final_output, pg_ends = self.main(output.splitlines(), pg_ends)
        final_output, _ = self.main(
            final_output.splitlines(), pg_ends)  # .encode('utf8')
        final_output = re.sub(r'\.[0-9]+\.', '.', final_output)
        final_output = re.sub(r' \. ', '   ', final_output)
        final_output = re.sub(r'\'', '', final_output)
        final_output = re.sub(r'\"', '', final_output)
        final_output = re.sub(r'\n', '', final_output)
        final_output = re.sub(r'(?<=\s{5})\w+(?=\s)','', final_output)
        final_output = re.sub(r'(?<=\s)\w+(?=\s{7})','', final_output)
        final_output = re.sub(r'(?<=\s)\w+(?=\s\n)','', final_output)
        #return output_orig
        return final_output  # .encode('utf8')


if __name__ == '__main__':
    PDF = '/home/pratyush1999/Documents/btp/Wealth Management- Relevant Documents/final_docs/regtech-revolution-coming.pdf'
    Pdftxt_Extract = PdfTxtExtract(PDF)
    Pdftxt_Extract.extract_text()
    #print(Pdftxt_Extract.extract_text())
    print("{\"content\":\"", Pdftxt_Extract.extract_text(), "\"}")
    # output   = subprocess.check_output(command).decode('utf8')
    # print(output)
