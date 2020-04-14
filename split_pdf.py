""" this module splits multi column pages of pdf into separate pages """
import re
import copy
import subprocess


class PdfGetPages():
    """ this class makes a pdf page splitter """
    def __init__(self, pdf_file):
        """ this class is for splitting pdf pages """
        self.pdf_file = pdf_file
        self.pgno = 0
        self.output = ""
        self.all_starts = []
        # self.all_ends = []
        self.no_pages = 0
        try:
            pdf_info = subprocess.Popen(
                ('pdfinfo', self.pdf_file), stdout=subprocess.PIPE)
        except:
            print("error in getting the information of the pdf")
            return
        try:
            self.no_pages = int(subprocess.check_output(
                ('grep', '-oP', '(?<=Pages:          )[ A-Za-z0-9]*'), stdin=pdf_info.stdout))
        except:
            print("error in getting the information of the pdf")

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
            line += '\n'
            line = re.sub(r':', '', line)
            line = re.sub(r'\u2212', '-', line)
            if line[0] == '-':
                line = str(line_hyphen)+'.'+line[1:]
                line_hyphen += 1
            # for removing line numbers.
            line = re.sub(r'^\s*[\(]?\w+[\.\)](?=\s)', '', line)
            starts = [m.start(0) for m in re.finditer(r'(?<=(\s\s))\S', line)]
            ends = [m.start(0)
                    for m in re.finditer(r'\S(?=((\s\s)|\n))', line)]
            if re.search(r'\S', line[0:2]):
                starts.insert(0, 0)
            if starts and ends and ends[0]-starts[0] <= 2:
                del starts[0]
                del ends[0]
            all_starts.append(starts)
            # all_ends.append(ends)
            if len(starts) < 1:
                empty.append(1)
                continue
            empty.append(0)
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
            #ends = all_ends[line_i-1]
         #   print("this line starts:",line, starts,"this line ends")

            if len(starts) < 1:
                emp_l = line_i
                lines_removed[line_i-1] = 1
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
                                       empty[line_i+1] == 1) or
                                      (empty[line_i-1] == 1 and empty[line_i+1] == 1 \
                                       and empty[line_i+2] == 1)):
                lines_removed[line_i-1] = 1
            if line_i == last_line:
                num_empty = 1
                if emp_l >= 1 and num_empty <= 2 and empty[emp_l-1] == 1:
                    num_empty += 1
                if num_empty >= 2 and emp_l != -1 and first_split == 1 and line_i-emp_l <= 12:
                    for i in range(emp_l+1, line_i+1, 1):
                      # print("pratyush1999", "pgno:", self.pgno, self.output[i-1])
                        lines_removed[i-1] = 1
        self.all_starts = all_starts
        # self.all_ends = all_ends
        return lines_removed, mxln

    def check_split(self, spl_spce, lines_removed_preprocess):
        """ this method checks if the page can be split """
        first_col = ""
        second_col = ""
        prev = 10000
        for line_i, line in enumerate(self.output, 1):
            if lines_removed_preprocess[line_i-1]:
                continue
            if line_i == len(self.output):  # :and line[-1] not in line_end:
                # print(line)
                line += '.'

            # if self.pgno==10 and line_i==5:
            #     print("this line:::", spl_spce, line[:spl_spce], w_spce[52], total_lines)
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

    def main(self, output, first_split=0):
        """ the main function which returns the splitted pdf pages"""
        self.output = output
        line_end = [':', ',', '.', ';']
        lines_removed_preprocess, mxln = self.clean(first_split)
        first_page_ends = []
        second_page_ends = []
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
            line = re.sub(r':', '', line)
            # for removing line numbers.
            line = re.sub(r'^\s*[\(]?\w+[\.\)](?=\s)', '', line)
            starts = self.all_starts[line_i-1]
            #ends = self.all_ends[line_i-1]
            if len(starts) < 1:
                continue

        # if self.pgno==5:
        #     print(r_spce[62], l_spce[62])
        spl_spce = 1000
        # if one_w_spce:
        #     one_key_max = max(one_w_spce, key=one_w_spce.get)
        #     if one_w_spce[one_key_max]>=total_lines-5:
        #         spl_spce=one_key_max
        if w_spce:
            key_max = max(w_spce, key=w_spce.get)
            sorted(w_spce.items(), key=lambda x: x[1], reverse=True)
            # if self.pgno==7:
            outta = []
            for key, val in w_spce.items():
                if val == w_spce[key_max] and abs(key-int(mxln/2)) <= 25:
                    key_max = key
                    outta.append(key)
            # print(*outta, l_spce[key_max], r_spce[key_max], mxln, abs(key_max-int(mxln/2))<=25 )
            if abs(key_max-int(mxln/2)) <= 25 \
                    and(
                            min(r_spce[key_max], l_spce[key_max]) >= 3 *
                            max(r_spce[key_max], l_spce[key_max])/4
                            or min(l_spce[key_max], r_spce[key_max]) >= 100)\
            and r_spce[key_max] > 10 and l_spce[key_max] > 10:
                #   print("type 1:",self.pgno,"col key:", key_max, "max length of line in page:",\
                #       mxln, "w_spce of key:",w_spce[key_max], "r_spce:", r_spce[key_max],\
                #       "l_spce:", l_spce[key_max],"total_lines :", total_lines,
                spl_spce = key_max
            else:  # if r_spce[key_max]>=10 and l_spce[key_max]>=10:
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
                first_col = temp_first_col
                second_col = temp_second_col
                entr = 0
        if entr:
            for line_i, line in enumerate(self.output, 1):
                if lines_removed_preprocess[line_i-1]:
                    continue
                line1 = line.rstrip()
                if line_i == len(self.output) and (line1[-1] not in line_end):
                    # print(line)
                    line += '.'
                #line=re.sub(r'(?<=[a-zA-Z])[0-9]+\s',' ', line)
                # if self.pgno==10 and line_i==5:
                #     print("this line:::", spl_spce, line[:spl_spce], w_spce[52], total_lines)
                if spl_spce < len(line)-1 and line[spl_spce] == ' ' and line[spl_spce+1] == ' ':
                    first_col += line[:spl_spce]
                    # if re.findall(r'[a-zA-Z]', line[:spl_spce]):
                # first_page_ends+='0'
                    # if first_col[-1]!='\n':
                    first_col += '\n'
                    # first_page_ends+='\n'
                    second_col += line[spl_spce:]
                    # if re.findall(r'[a-zA-Z]', line[spl_spce:]):
                # second_page_ends+='0'
                    if line[-1] != '\n':
                        second_col += '\n'
                        # second_page_ends+='\n'
                else:
                    if len(line)-1 <= spl_spce:
                        second_col += '\n'
                      # second_page_ends+='0'
                    first_col += line
                    # first_page_ends+='0'
                    if len(line) == 0 or line[-1] != '\n':
                        first_col += '\n'
                        # first_page_ends+='\n'
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
        if first_col:
            #z = 0
            while first_col and (first_col[-1] == '\n' or first_col[-1] == ' '):
                # print(z)
                # z+=1
                first_col = first_col[:-1]
                # first_page_ends.pop()
            first_col += '\n'
        if second_col:
            while len(second_col) >= 2 and (second_col[-1] == '\n' or second_col[-1] == ' '):
                second_col = second_col[:-1]
                # second_page_ends.pop()
            # if second_col[-1]!='\n':
            if second_col[-1] != '\n':
                second_col += '\n'
            # else:
       #         second_col='\n'
        for line in first_col.splitlines():
            first_page_ends.append(0)
        for line in second_col.splitlines():
            second_page_ends.append(0)
        if first_page_ends:
            first_page_ends[-1] = 1
        if second_page_ends:
            second_page_ends[-1] = 1
        return first_col, second_col, first_page_ends, second_page_ends
        #print(starts, line)

    def extract_text(self):
        """ the caller function for calling the main function """
        final_output = ""
        pg_ends = []
        for page in range(1, self.no_pages+1):
            self.pgno = page
            command = ['pdftotext', '-f',
                       str(page), '-l', str(page), '-layout', self.pdf_file, '-']
            try:
                output = subprocess.check_output(command).decode('utf8')
            except:
                print("error in running pdftotext")
                return ""
            # print(self.output)
             # output=re.sub(r':','',output)
            first_col, second_col, _, _ = self.main(
                output.splitlines(), 1)
            if first_col:
                first_first_col, first_second_col, pg1, pg2 = self.main(
                    first_col.splitlines(), 0)
                final_output += first_first_col
                pg_ends += pg1
                pg_ends += pg2
                # page_ends.
                # final_self.output+='\n'
                # if re.findall(r'\w', first_second_col):
                final_output += first_second_col
#              final_self.output+='\n'
            if second_col:
                second_col, third_column, pg1, pg2 = self.main(
                    second_col.splitlines(), 0)
                final_output += second_col
                pg_ends += pg1
                pg_ends += pg2

   #             final_self.output+='\n'
                final_output += third_column
    #            final_self.output+='\n'
            # final_self.output+=self.main(self.f1(self.output),2)
        return final_output, pg_ends  # .encode('utf8')


# if __name__ == '__main__':
#     PDF = '/home/pratyush1999/Documents/btp/digitalee/src/pdf_to_txt/app/PDFs/Original PDFs/Regtech in Financial Services.pdf'
#     pdftotxt_extract = PdfGetPages(PDF)
#     # print(pdftotxt_extract.extract_text())
#     RET, _ = pdftotxt_extract.extract_text()
#     print(RET)
