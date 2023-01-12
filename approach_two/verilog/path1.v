module top (input clk, output out);

wire net0;
wire net1;
wire net2;
wire net3;
wire net4;
wire net5;
wire net6;
wire net7;
wire net8;
wire net9;
wire net10;
wire net11;
wire net12;
wire net13;
wire net14;
wire net15;
wire net16;
wire net17;
wire net18;
wire net19;
wire net20;
wire net21;
wire net22;
wire net23;
wire net24;
wire net25;
wire net26;
wire net27;
wire net28;
wire net29;
wire net30;
wire net31;
wire net32;
wire net33;
wire net34;
wire net35;
wire net36;

sky130_fd_sc_hd__clkbuf_16 clkbuf_0_core_clk(.A(clk ), .X(net0), );

sky130_fd_sc_hd__clkbuf_8 clkbuf_1_1_0_core_clk(.A(net0), .X(net1), );

sky130_fd_sc_hd__clkbuf_8 clkbuf_1_1_1_core_clk(.A(net1), .X(net2), );

sky130_fd_sc_hd__clkbuf_8 clkbuf_1_1_2_core_clk(.A(net2), .X(net3), );

sky130_fd_sc_hd__clkbuf_8 clkbuf_1_1_3_core_clk(.A(net3), .X(net4), );

sky130_fd_sc_hd__clkbuf_8 clkbuf_1_1_4_core_clk(.A(net4), .X(net5), );

sky130_fd_sc_hd__clkbuf_8 clkbuf_1_1_5_core_clk(.A(net5), .X(net6), );

sky130_fd_sc_hd__clkbuf_8 clkbuf_1_1_6_core_clk(.A(net6), .X(net7), );

sky130_fd_sc_hd__clkbuf_8 clkbuf_2_3_0_core_clk(.A(net7), .X(net8), );

sky130_fd_sc_hd__clkbuf_8 clkbuf_2_3_1_core_clk(.A(net8), .X(net9), );

sky130_fd_sc_hd__clkbuf_8 clkbuf_3_6_0_core_clk(.A(net9), .X(net10), );

sky130_fd_sc_hd__clkbuf_8 clkbuf_3_6_1_core_clk(.A(net10), .X(net11), );

sky130_fd_sc_hd__clkbuf_8 clkbuf_3_6_2_core_clk(.A(net11), .X(net12), );

sky130_fd_sc_hd__clkbuf_8 clkbuf_4_12_0_core_clk(.A(net12), .X(net13), );

sky130_fd_sc_hd__clkbuf_8 clkbuf_5_25_0_core_clk(.A(net13), .X(net14), );

sky130_fd_sc_hd__clkbuf_8 clkbuf_5_25_1_core_clk(.A(net14), .X(net15), );

sky130_fd_sc_hd__clkbuf_16 clkbuf_leaf_149_core_clk(.A(net15), .X(net16), );

sky130_fd_sc_hd__dfxtp_4 _31022_(.CLK(net16), .Q(net17), );

sky130_fd_sc_hd__buf_12 fanout1989(.A(net17), .X(net18), );

sky130_fd_sc_hd__clkinv_8 _13829_(.A(net18), .Y(net19), );

sky130_fd_sc_hd__nand2_1 _14126_(.A(net19), .Y(net20), );

sky130_fd_sc_hd__dlygate4sd3_1 hold637(.A(net20), .X(net21), );

sky130_fd_sc_hd__buf_12 fanout1728(.A(net21), .X(net22), );

sky130_fd_sc_hd__buf_12 fanout1727(.A(net22), .X(net23), );

sky130_fd_sc_hd__o21ai_4 _14250_(.A2(net23), .Y(net24), );

sky130_fd_sc_hd__nor4_2 _19504_(.B(net24), .Y(net25), );

sky130_fd_sc_hd__and4b_4 _19506_(.C(net25), .X(net26), );

sky130_fd_sc_hd__and3_1 _19509_(.C(net26), .X(net27), );

sky130_fd_sc_hd__buf_12 fanout1231(.A(net27), .X(net28), );

sky130_fd_sc_hd__and4b_4 _19517_(.C(net28), .X(net29), );

sky130_fd_sc_hd__and4_4 _19518_(.B(net29), .X(net30), );

sky130_fd_sc_hd__buf_8 fanout1033(.A(net30), .X(net31), );

sky130_fd_sc_hd__nand2_1 _19519_(.A(net31), .Y(net32), );

sky130_fd_sc_hd__buf_12 fanout772(.A(net32), .X(net33), );

sky130_fd_sc_hd__buf_12 fanout771(.A(net33), .X(net34), );

sky130_fd_sc_hd__or4b_1 _19801_(.B(net34), .X(net35), );

sky130_fd_sc_hd__o211a_1 _19802_(.B1(net35), .X(net36), );

sky130_fd_sc_hd__dfxtp_4 _28553_(.D(net36), );assign out = net36;
endmodule