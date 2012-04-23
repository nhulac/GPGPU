//
// Send a response on the CPI interface
// - Cache Read Hit: send an acknowledgement.
// - Cache Write Hit: send an acknowledgement and the new contents
//   of the line.  If there are lines in other cores that match,
//   need to send write updates for those.  
// - Cache miss: don't send anything.
//

module l2_cache_response(
	input						clk,

	input 			stg4_pci_valid,
	input [1:0]	stg4_pci_unit,
	input [1:0]	stg4_pci_strand,
	input [2:0]	stg4_pci_op,
	input [1:0]	stg4_pci_way,
	input [511:0]	stg4_data,
	input stg4_dir_valid,
	input [1:0] stg4_dir_way,
	input stg4_cache_hit,
	input stg4_has_sm_data,
	output reg					cpi_valid_o = 0,
	output reg					cpi_status_o = 0,
	output reg[1:0]				cpi_unit_o = 0,
	output reg[1:0]				cpi_strand_o = 0,
	output reg[1:0]				cpi_op_o = 0,
	output reg					cpi_update_o = 0,
	output reg[1:0]				cpi_way_o = 0,
	output reg[511:0]			cpi_data_o = 0);

	reg[1:0] response_op = 0;

	always @*
	begin
		case (stg4_pci_op)
			`PCI_LOAD: response_op = `CPI_LOAD_ACK;
			`PCI_STORE: response_op = `CPI_STORE_ACK;
			`PCI_FLUSH: response_op = 0;
			`PCI_INVALIDATE: response_op = 0;
			`PCI_LOAD_SYNC: response_op = `CPI_LOAD_ACK;
			`PCI_STORE_SYNC: response_op = `CPI_STORE_ACK;
			default: response_op = 0;
		endcase
	end

	always @(posedge clk)
	begin
		if (stg4_pci_valid)
			$display("stg4: op = %d", stg4_pci_op);

		if (stg4_pci_valid && (stg4_cache_hit || stg4_has_sm_data))
		begin
			cpi_valid_o <= #1 stg4_pci_valid;
			cpi_status_o <= #1 1;
			cpi_unit_o <= #1 stg4_pci_unit;
			cpi_strand_o <= #1 stg4_pci_strand;
			cpi_op_o <= #1 response_op;	
			cpi_update_o <= #1 stg4_dir_valid;	
			cpi_way_o <= #1 stg4_dir_way;
			cpi_data_o <= #1 stg4_data;	
		end
		else
			cpi_valid_o <= #1 0;
	end
endmodule