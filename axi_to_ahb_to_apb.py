import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from cocotb.result import TestFailure

@cocotb.test()
async def test_spi_interface(dut):
    # Initialize SPI signals
    dut.cs <= 1
    dut.mosi <= 0
    await FallingEdge(dut.clk)

    # Reset DUT
    dut.reset <= 1
    await FallingEdge(dut.clk)
    dut.reset <= 0

    # Initialize clock
    cocotb.fork(Clock(dut.clk, 10, units="ns").start())

    # Test SPI communication
    await RisingEdge(dut.clk)
    dut.cs <= 0
    await RisingEdge(dut.clk)

    # initialise test data arrays
    expected_data = [0x12, 0x34, 0x56, 0x78]
    received_data = []

    for data_byte in expected_data:
        
        dut.mosi <= data_byte
        await RisingEdge(dut.clk)
        received_data.append(int(dut.miso))

    # deassert chip sellect 
    dut.cs <= 1

    # check to see if the data matches
    if received_data != expected_data:
        raise TestFailure(f"Received data = {received_data} is not equal to the expected data = {expected_data}")

@cocotb.test()
async def test_axi_to_ahb_to_apb_interface(dut):
    # Initialize AXI interface
    dut.axi_arready <= 0
    dut.axi_rvalid <= 0
    dut.axi_awready <= 0
    dut.axi_wready <= 0
    dut.axi_bvalid <= 0

    # Reset DUT
    dut.reset <= 1
    await FallingEdge(dut.clk)
    dut.reset <= 0

    # Initialize clock
    cocotb.fork(Clock(dut.clk, 10, units="ns").start())

    # Send read request to AXI
    dut.axi_arvalid <= 1
    dut.axi_araddr <= 0x1000  # Example address
    await RisingEdge(dut.clk)
    dut.axi_arvalid <= 0

    # Wait for read response
    while not dut.axi_arready:
        await RisingEdge(dut.clk)

    # Check read data
    if dut.axi_rvalid:
        read_data = dut.axi_rdata.value.integer
        expected_data = 0xABCD  # Example expected data
        if read_data != expected_data:
            raise TestFailure(f"Received data {read_data} does not match expected data {expected_data}")

    # Send write request to AXI
    dut.axi_awvalid <= 1
    dut.axi_awaddr <= 0x2000  # Example address
    dut.axi_wvalid <= 1
    dut.axi_wdata <= 0x1234  # Example data
    await RisingEdge(dut.clk)
    dut.axi_awvalid <= 0
    dut.axi_wvalid <= 0

    # Wait for write response
    while not dut.axi_awready or not dut.axi_wready:
        await RisingEdge(dut.clk)

    # Check write response
    if dut.axi_bvalid:
        if dut.axi_bresp != 0:
            raise TestFailure(f"Write request failed with response {dut.axi_bresp}")

