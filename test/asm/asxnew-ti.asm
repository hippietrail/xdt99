*  NEW FEATURES

        IDT 'ASXNEW'

START   BLWP @0

* BINARY LITERALS

BINVAL  EQU >0A
        DATA >5A,>F0
        BYTE BINVAL

* BINARY INCLUDES

BININC  BYTE >AA
        BYTE >01,>10,>0F,>F0,>0A,>00,>0D,>FF,>01
        BYTE >BB
        BYTE >01,>10,>0F,>F0,>0A,>00,>0D,>FF,>01
        BYTE >CC

* TEXT BYTES

TXTBYT  BYTE >12,>34,>56,>78,>90,>AB,>CD,>EF
        BYTE >12,>30
        BYTE >12,>34,->56

* LOCAL LABELS

GLOB1   DATA 1
        JMP  GLOB2
        JMP  GLOB2
        JMP  GLOB1
        JMP  GLOB2
GLOB2   DATA 2
        DATA 0
LLL1    DATA 3
        JMP  LLL2
        JMP  LLL3
        JMP  LLL4
        JMP  LLL1
        JMP  GLOB2
        JMP  GLOB1
        DATA 0
LLL2    DATA 4
        JMP  LLL2
        JMP  LLL3
LLL3    JMP  LLL2
LLL4    JMP  GLOB3
        B    @LLL4-2
        B    @GLOB3+2
        MOV  @LLL4(1),@GLOB3(2)
GLOB3   DATA 5

* LABEL CONTINUATIONS

LREG1   DATA 1
LREG2
LREG3   DATA 2
LREG4
LREG5   EQU  3
LREG6
        AORG >A200
LREG7   DATA 4

        DATA LREG1,LREG2,LREG3
        DATA LREG4,LREG5,LREG6
        DATA LREG7

LCONT1  DATA 1
LCONT2  DATA 2
LCONT3  DATA 3
LCONT4  EQU  4
LCONT5  EQU  5
LCONT6  AORG >A200
LCONT7  BES  10

        DATA LCONT1,LCONT2,LCONT3
        DATA LCONT4,LCONT5,LCONT6
        DATA LCONT7

        END
