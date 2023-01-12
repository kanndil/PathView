set_cmd_units -time ns -capacitance pF -current mA -voltage V -resistance kOhm -distance um
read_liberty sky130_fd_sc_hd.lib
read_verilog i2c_master.v
link_design i2c_master
create_clock -name clk -period 20 sys_clk
report_checks -path_delay min_max -format full -fields input_pins  > ./staReport.txt
# Exit OpenSTA shell
exit