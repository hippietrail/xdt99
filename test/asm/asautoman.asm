* autogenerated constants

     aorg >a000

     li   r0, 1
     movb @b_42, r1

     cb   r4, @b_48
     socb @b_48, r4

     mov  @w_haa01, @>af00
     xor  @w_12345, r3

     movb @b_R, r1
     szc  @w_X, r3

     data >ffff


b_42 byte 42
b_48 byte >30
w_haa01 data >aa01
w_12345 data 12345
w_X data >5800
b_R byte >52
 byte 0  ; filler

     end
