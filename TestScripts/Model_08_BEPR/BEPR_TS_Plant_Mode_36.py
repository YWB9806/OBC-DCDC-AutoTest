from CommonFunction.FunctionClass_V2 import *
from UtilityClass.UtilityClass01_DeviceConnectInit import *
from CommonFunction.Common00_Fuction import *
from CommonFunction.Common04_SoftwareCommonFunction import STLA_M_EncapsulationClass

if __name__ == '__main__':

    start_capture_prints()
    STLA_M_EncapsulationClass.InitDevice()
    STLA_M_EncapsulationClass.InitAllCANMessage()
    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = True, case_name = "STLA-M-BEPR")
    PreCondition = STLA_M_EncapsulationClass.EnterPlantModePreCondition(CONFIG_VHL = 1)
   
    继电器控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='8181')
    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='220')
    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('BMS_DC_RELAY_MES_EVSE_VOLTAGE'),'BMS_DC_RELAY_MES_EVSE_VOLTAGE', 20)
    信号发生器.SCPI.Write(':SOUR1:APPL:SQU 1000,12.1,0,0;:SOUR1:FUNC:SQU:DCYC 50;:OUTP1 ON')
    交流源载一体机.Set.Basic(ACPwrModeEnum.SOUR, ACChannelEnum.EACH, ACCouplingEnum.AC,0, ACPwrWorkModeEnum.CC)
    交流源载一体机.Set.Freq(dFreq=50)
    交流源载一体机.Set.Volt(dealListData([40.0, 40.0, 40.0]),dealListData([0.0, 0.0, 0.0]))
    交流源载一体机.Out.Enable(ACeEnable.ON)
    Sleep(17000)

    TestResult3 = debug_break("OBC shall high-side control the red charge LED on.", timeout = 30)
    STLA_M_EncapsulationClass.Send590DiagMessageAndLog(
        message="03 22 D5 BD",
        expected_response=["0x05", "0x62", "0xD5", "0xBD", "0x01", "0x0E"],
        check_len=6
    )
    STLA_M_EncapsulationClass.Send590DiagMessageAndLog(
        message="03 22 D4 F7",
        expected_response=["0x04", "0x62", "0xD4", "0xF7", "0x01"],
        check_len=5
    )

    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='2300')
    Sleep(1000)
    Test, OBCChrgConnConf1 = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('OBC_CHRG_CONN_CONF'),'OBC_CHRG_CONN_CONF', 0.0)
    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='220')
    Sleep(1000)
    Test, OBCChrgConnConf2 = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('OBC_CHRG_CONN_CONF'),'OBC_CHRG_CONN_CONF', 0.0)
    TestResult21 = OBCChrgConnConf1 == 0
    TestResult22 = OBCChrgConnConf2 == 2
    TestResult2 = TestResult21 and TestResult22
    print(f"OBC_CHRG_CONN_CONF={OBCChrgConnConf1}时, 测试结果={TestResult21}")
    print(f"OBC_CHRG_CONN_CONF={OBCChrgConnConf2}时, 测试结果={TestResult22}")


    STLA_M_EncapsulationClass.Send590DiagMessageAndLog(
        message="03 22 D5 BD",
        expected_response=["0x05", "0x62", "0xD5", "0xBD", "0x01", "0x0E"],
        check_len=6
    )

    AssignmentCode=156

    STLA_M_EncapsulationClass.ExitPlantMode()
    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = False, case_name = "STLA-M-BEPR")
    STLA_M_EncapsulationClass.RCD_Exit_EcoMode()
    STLA_M_EncapsulationClass.CloseAllDevice()
    STLA_M_EncapsulationClass.CloseAllCANMessage()
    TestResult1 = STLA_M_EncapsulationClass.PlantModeScreenshot(faultcode=AssignmentCode, VerifyWhetherReportFault=True)


    print(f"前置条件结果:{PreCondition}, 测试步骤1结果: {TestResult1}, 测试步骤2结果: {TestResult2}, 测试步骤3结果: {TestResult3}")
    TestResult = True if PreCondition and TestResult1 and TestResult2 and TestResult3  else False
    if TestResult == True:
        TestResultDisplay = '合格'
        print(TestResultDisplay)
    else:
        TestResultDisplay = '不合格'
        print(TestResultDisplay)
    
    all_prints = stop_capture_prints()
    Log4NetWrapper.WriteToOutput_KeyInfo(TestResultDisplay, 
        f"\n"+
        f"1. Charge LED is solid white color. \n"+
        f"\n"+
        f"========================================================================="+
        f"\n"+
        f"{all_prints}"
    )






