'''
--------------------------------------------------------------------------------

This program provides a Simple Microprogram ROM (SMR) Tool for assembling
and/or compiling text files into memory initialization files suitable for use
with FPGA tools in embedded memory blocks. Future updates will provide more
output options: inferred ROM blocks in Verilog or VHDL, and listing files.

--------------------------------------------------------------------------------
--
--  Copyright 2018 by Michael A. Morris, dba M. A. Morris & Associates
--
--  All rights reserved. The source code contained herein is publicly released
--  under the terms and conditions of the GNU General Public License as conveyed
--  in the license provided below.
--
--  This program is free software: you can redistribute it and/or modify it
--  under the terms of the GNU General Public License as published by the Free
--  Software Foundation, either version 3 of the License, or any later version.
--
--  This program is distributed in the hope that it will be useful, but WITHOUT
--  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
--  FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
--  more details.
--
--  You should have received a copy of the GNU General Public License along with
--  this program.  If not, see <http://www.gnu.org/licenses/>, or write to
--
--  Free Software Foundation, Inc.
--  51 Franklin Street, Fifth Floor
--  Boston, MA  02110-1301 USA
--
--  Further, no use of this source code is permitted in any form or means
--  without inclusion of this banner prominently in any derived works.
--
--  Michael A. Morris <morrisma_at_mchsi_dot_com>
--  164 Raleigh Way
--  Huntsville, AL 35811
--  USA
--
--------------------------------------------------------------------------------
-- Revision History:
--------------------------------------------------------------------------------
--
--  0001    18C09   MAM     Initial release.
--
--------------------------------------------------------------------------------
'''

import sys
import re

if len(sys.argv) < 2:
    print('Usage: python SMRToolV1.py filename [options]' \
          '\n\tinput  < "filename".txt.' \
          '\n\toutput > "filename".coe.')
else:
    filename = sys.argv[1]

    with open(filename+'.txt', "rt") as finp:
        lines = finp.readlines()

    '''
        Skip the header portion of the source file. Will process later.
    '''

    ln = 0
    for line in lines:
        ln += 1
        m = re.match('^endh', line)
        if m:
            break

    '''
        Write out the source file with the comments stripped out.
    '''

    with open(filename+'.out', "wt") as fout:
        instructions = {}; fields = []; defines = {}
        for line in lines[ln:]:
            m = re.split('\s*--', line)
            if m[0] == "" or m[0] == "\n":
                pass
            elif len(m) == 1:
                print(m[0], file=fout, end='')
            else:
                print(m[0], file=fout)

            asm = re.split('\s*\.asm\s*', m[0])
            if len(asm) == 2:
                if asm[0] in instructions:
                    print('ERROR: redefinition of '+asm[0]+' at line = '+ln)
                else:
                    instructions[asm[0]] = asm[1]

            fld = re.split('\s*\.def\s*', m[0])
            if len(fld) == 2:
                if fld[0] in fields:
                    print('ERROR: redefinition of '+fld[0]+' at line = '+ln)
                else:
                    fields.append((fld[0], fld[1]))

            equ = re.split('\s*\.equ\s*', m[0])
            if len(equ) == 2:
                if equ[0] in defines:
                    print('ERROR: redefinition of ' \
                          + str(equ[0]) \
                          + ' at line = ' \
                          + str(ln))
                else:
                    defines[equ[0]] = equ[1]
            ln += 1

    '''
        Find first label. First label signifies the start of the microprogram.
    '''

    ln = 0
    for line in lines:
        ln += 1
        m = re.match('_[A-Za-z]+[A-Za-z_0-9]*:', line)
        if m:
            ln -= 1
            break

    '''
        Print out the portion of the source files that pertains to the micro-
        program. Capture source-only lines in source[]
    '''

    with open(filename+'.src', "wt") as fout:
        source = []; maxSourceLength = 0
        for line in lines[ln:]:
            m = re.split('\s*--', line)
            m[0] = m[0].rstrip()
            if m[0] == '' or m[0] == '\n':
                pass
            elif len(m) == 1:
                print(m[0], file=fout, end='')
                source.append(m[0])
            else:
                print(m[0], file=fout)
                source.append(m[0])
            lineLength = len(m[0])
            if maxSourceLength < lineLength:
                maxSourceLength = lineLength

    with open(filename+'.lbl', "wt") as fout:
        lc = 0; labels = {}; max_label_len = 0; lines = []
        for line in source:
            m = re.match('_.*:\s*', line)
            if m:
                lbl = re.split(':\s*', m.group())
                val = re.split(':\s*\.org\s*', line)
                if len(val) == 2:
                    print(lbl[0]+", "+val[1], file=fout, end='')
                    lc = int(val[1])
                else:
                    print(lbl[0]+", "+str(lc), file=fout)

                if lbl[0] in labels:
                    print('ERROR: Redefinition of', lbl[0], "at loc =", lc)
                else:
                    labels[lbl[0]] = lc

                if len(lbl[0]) > max_label_len:
                    max_label_len = len(lbl[0])
            else:
                m = re.match('\s*\.org\s*', line)
                if m:
                    val = re.split('\.org\s*', line)
                    lc = int(val[1])
                else:
                    lines.append((lc, line))    # capture (lc, source) to parse
                    lc += 1
        max_label_len += 1

    '''
        Print out the tables from the source array:
            Instructions -- Names and values for field 1 of microprogram
            Fields       -- Names and widths of the fields in the microword
            Defines      -- Names and values of the constants for the micro-
                            program
            Labels       -- Names and addresses of locations in microprogram
    '''

    indent = 2
    print('Instructions = {')
    for instruction in instructions:
        if len(instruction) < max_label_len:
            buffer = max_label_len - len(instruction)
        print(' '*indent+instruction+ \
              ' '*buffer+': '+str(instructions[instruction]))
    print('}')
    print()

    print('Fields = [')
    width = 0
    for field in range(len(fields)):
        fldnm, fldln = fields[field]
        if len(fldnm) < max_label_len:
            buffer = max_label_len - len(fldnm)
        print(' '*indent+fldnm+' '*buffer+", "+fldln)
        width += int(fldln)
    print(']')
    print()

    print('Defines = {')
    for define in defines:
        if len(define) < max_label_len:
            buffer = max_label_len - len(define)
        print(' '*indent+define+' '*buffer+": "+str(defines[define]))
    print('}')
    print()

    print('Labels = {')
    for label in labels:
        if len(label) < max_label_len:
            buffer = max_label_len - len(label)
        print(' '*indent+label+' '*buffer+": "+str(labels[label]))
    print('}')
    print()

    '''
        Create list of empty fields to hold the processed source
        Length of list is set by the value of the '_end' label.
    '''

    if '_end' in labels:
        rom = []; num_fields = len(fields)
        for lc in range(labels['_end']):
            rom_line = []
            for field in range(num_fields):
                fldnm, fldln = fields[field]
                rom_line.append('0'*int(fldln))
            rom.append(rom_line)
    ##        print('0x%03X: %s' % (lc, rom[lc]))
    ##        #print('0x%03X (0o%03o, %03d): %s' % (lc, lc, lc, rom[lc]))
    else:
        print('ERROR: Label "_end:" not found')
    ##print()

    '''
        Process the source lines. Extract the fields, and merge into the
        ROM[] listed above. Truncate the values extracted to fit the width of
        each field.

        Numeric constants are allowed to be represented as decimal, binary,
        octal, or hexadecimal values. The int() built-in function is used to
        convert the numeric strings into integers by setting the base= parameter
        of the function appropriately.

        All fields are represented as binary strings. Padding with 0 is per-
        formed when the resulting value binary string output of the bin() is
        less than the field width. Trimming of the binary string from the left
        is performed if the string output by bin() is greater than field width.
    '''

    for line in range(len(lines)):
        lc, src = lines[line]; flds = []
        i = 0; length = len(src)

        m = re.match('\s*[a-zA-Z][a-zA-Z0-9]*\s*', src)
        if m:
            flds.append(m.group().lstrip().rstrip())
        else:
            print('\tERROR: Expected identifier in field 1')

        m = re.split(',\s*', src[len(m.group()):])
        for i in range(len(m)):
            flds.append(m[i].rstrip())
        if src[length-1] == '\n':
            src = src[:-1]

        bufferLength = maxSourceLength - len(src)
        print('0x%03X: %s' % (lc, src), ' '*bufferLength, "-- ", flds)
        lines[line] = (lc, flds)

        for field in range(len(flds)):
            fldnm, fldln = fields[field]
            fld = flds[field]
            width = int(fldln)
            if field == 0:
                '''
                    Field 0 must be represented as elements of instructions{}.
                    Field 0 cannot be ''.
                '''
                if fld in instructions:
                    val = bin(int(instructions[fld]))[2:]
                    if width < len(val):
                        val = val[(len(val) - width):]
                    padlen = width-len(val)
                    if padlen < 1:
                        rom[lc][field] = '%-*s' % (width, val)
                    else:
                        rom[lc][field] = '%-*s' % (width, '0'*padlen+val)
                else:
                    print('\tERROR: Undefined value in ' \
                          'field %d: %s.' % (field, fld))
                    break
            elif field == 1:
                '''
                    Field 1 may be represented as labels{}, a numeric constant,
                    or a $, which represents the current location counter.
                    Field 1 cannot be ''.
                '''
                if fld is '$':
                    val = bin(int(lc))[2:]
                    if width < len(val):
                        val = val[(len(val) - width):]
                    padlen = width-len(val)
                    if padlen < 1:
                        rom[lc][field] = '%-*s' % (width, val)
                    else:
                        rom[lc][field] = '%-*s' % (width, '0'*padlen+val)
                elif fld in labels:
                    val = bin(int(labels[fld]))[2:]
                    if width < len(val):
                        val = val[(len(val) - width):]
                    padlen = width-len(val)
                    if padlen < 1:
                        rom[lc][field] = '%-*s' % (width, val)
                    else:
                        rom[lc][field] = '%-*s' % (width, '0'*padlen+val)
                elif fld[0].isdigit():
                    if len(fld) == 1:
                        val = bin(int(fld))[2:]
                    elif fld[0] == '0':
                        radix = fld[1]
                        if radix == 'b':
                            val = fld[2:]
                        elif radix == 'o':
                            val = bin(int(fld, base=8))[2:]
                        elif radix == 'x' or radix == 'X':
                            val = bin(int(fld, base=16))[2:]
                    else:
                        val = bin(int(fld, base=10))[2:]
                    if width < len(val):
                        val = val[(len(val) - width):]
                    padlen = width-len(val)
                    if padlen < 1:
                        rom[lc][field] = '%-*s' % (width, val)
                    else:
                        rom[lc][field] = '%-*s' % (width, '0'*padlen+val)
                else:
                    print('\tERROR: Expected identifier, "$", or number in ' \
                          'field %d: %s.' % (field, fld))
            else:
                '''
                    Remaining fields must be represented as defines{}, or
                    numbers. Remaining fields may be '', in which case the
                    field is null filled, i.e. 0 valued binary strings.
                '''
                if fld == '':
                    continue    # Keep the default value already in rom[].
                elif fld in defines:
                    val = bin(int(defines[fld]))[2:]
                    if width < len(val):
                        val = val[(len(val) - width):]
                    padlen = width-len(val)
                    if padlen < 1:
                        rom[lc][field] = '%-*s' % (width, val)
                    else:
                        rom[lc][field] = '%-*s' % (width, '0'*padlen+val)
                elif fld[0].isdigit():
                    if len(fld) == 1:
                        val = bin(int(fld))[2:]
                    elif fld[0] == '0':
                        radix = fld[1]
                        if radix == 'b':
                            val = fld[2:]
                        elif radix == 'o':
                            val = bin(int(fld, base=8))[2:]
                        elif radix == 'x' or radix == 'X':
                            val = bin(int(fld, base=16))[2:]
                    else:
                        val = bin(int(fld, base=10))[2:]
                    if width < len(val):
                        val = val[(len(val) - width):]
                    padlen = width-len(val)
                    if padlen < 1:
                        rom[lc][field] = '%-*s' % (width, val)
                    else:
                        rom[lc][field] = '%-*s' % (width, '0'*padlen+val)
                else:
                    print('\tERROR: Expected identifier or number in ' \
                          'field %d: %s.' % (field, fld))
    print()

    line = 0
    for i in range(len(rom)):
        lc, flds = lines[line]
        if lc == i:
            print('0x%03X:' % (i), '_'.join(rom[i]), '--', \
                  flds[0]+' '+','.join(flds[1:]))
            line += 1
        else:
            print('0x%03X:' % (i), '_'.join(rom[i]))
    print()

    with open(filename+'.coe', 'wt') as fout:
        for line in range(len(rom)):
            print(''.join(rom[line]), file=fout)

##    with open(filename+'.coe', 'rt') as finp:
##        lines = finp.readlines()
##
##    for i in range(len(lines)):
##        line  = lines[i][:-1]
##        width = len(line)
##        data  = int('0b'+''.join(rom[i]), base=2) ^ int('0b'+line, base=2)
##        if data != 0:
##            print('ERROR: Miscompare in line 0x%03X: ' % (i), \
##                  '0b'+'0'*(width-len(line))+bin(data)[2:])
##    print()
