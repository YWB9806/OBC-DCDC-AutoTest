from CommonFunction.FunctionClass_V2 import *
from UtilityClass.UtilityClass01_DeviceConnectInit import *
from CommonFunction.Common00_Fuction import *
from CommonFunction.Common04_SoftwareCommonFunction import STLA_M_EncapsulationClass

if __name__ == '__main__':

    start_capture_prints()
    STLA_M_EncapsulationClass.InitDevice()
    STLA_M_EncapsulationClass.InitAllCANMessage()
    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = True, case_name = "STLA-M-STEP2.5_PlantMode")
    PreCondition = STLA_M_EncapsulationClass.EnterPlantModePreCondition(CONFIG_VHL = 1)
   
    继电器控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='8181')
    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='1400')
    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('BMS_DC_RELAY_MES_EVSE_VOLTAGE'),'BMS_DC_RELAY_MES_EVSE_VOLTAGE', 40)
    信号发生器.SCPI.Write(':SOUR1:APPL:SQU 1000,12.1,0,0;:SOUR1:FUNC:SQU:DCYC 70;:OUTP1 ON')
    交流源载一体机.Set.Basic(ACPwrModeEnum.SOUR, ACChannelEnum.EACH, ACCouplingEnum.AC,0, ACPwrWorkModeEnum.CC)
    交流源载一体机.Set.Freq(dFreq=50)
    交流源载一体机.Set.Volt(dealListData([40.0, 40.0, 40.0]),dealListData([0.0, 0.0, 0.0]))
    交流源载一体机.Out.Enable(ACeEnable.ON)
    Sleep(17000)

    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('CABLE_LOCK_REQ'),'CABLE_LOCK_REQ', 2)
    Sleep(1000)
    Test, EVSEPlugLockState = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('EVSE_PLUG_LOCK_STATE'),'EVSE_PLUG_LOCK_STATE', 0.0)
    TestResult2 = EVSEPlugLockState == 0
    print(f"EVSE_PLUG_LOCK_STATE={EVSEPlugLockState}时, 测试结果={TestResult2}")

    TestResult3 = debug_break("BEPR_LockLEDCommand= OFF, and BEPR Charge LED is blinding green.", timeout = 30)


    STLA_CAN.DBC.SendMessage(1,'REQ_DIAG_ON_CAN_590',['802','54717','0','0'], 1, 100)  # 03 22 D5 BD

    AssignmentCode1 = 156
    AssignmentCode2 = 157
    AssignmentCode3 = 158
    AssignmentCode4 = 159
    TestResult41 = STLA_M_EncapsulationClass.CheckFaultIsInFaultList(AssignmentCode1)
    TestResult42 = STLA_M_EncapsulationClass.CheckFaultIsInFaultList(AssignmentCode2)
    TestResult43 = STLA_M_EncapsulationClass.CheckFaultIsInFaultList(AssignmentCode3)
    TestResult44 = STLA_M_EncapsulationClass.CheckFaultIsInFaultList(AssignmentCode4)
    TestResult4 = TestResult41 and TestResult42 and TestResult43 and TestResult44
    print(f"Result_Test_ACPhaseOutOfRange= {TestResult41}")
    print(f"Result_Test_ProxiVoltageOutOfRange= {TestResult42}")
    print(f"Result_Test_PilotDutyOutOfRange= {TestResult43}")
    print(f"Result_Test_DCLinesOutOfRange= {TestResult44}")

    STLA_M_EncapsulationClass.ExitPlantMode()
    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = False, case_name = "STLA-M-STEP2.5_PlantMode")
    STLA_M_EncapsulationClass.RCD_Exit_EcoMode()
    STLA_M_EncapsulationClass.CloseAllDevice()
    STLA_M_EncapsulationClass.CloseAllCANMessage()
    TestResult1 = STLA_M_EncapsulationClass.PlantModeScreenshot(faultcode=AssignmentCode1, VerifyWhetherReportFault=True)


    print(f"前置条件结果:{PreCondition}, 测试步骤1结果: {TestResult1}, 测试步骤2结果: {TestResult2}, 测试步骤3结果: {TestResult3}, 测试步骤4结果: {TestResult4}")
    TestResult = True if PreCondition and TestResult1 and TestResult2 and TestResult3 and TestResult4 else False
    if TestResult == True:
        TestResultDisplay = '合格'
        print(TestResultDisplay)
    else:
        TestResultDisplay = '不合格'
        print(TestResultDisplay)
    
    all_prints = stop_capture_prints()
    Log4NetWrapper.WriteToOutput_KeyInfo(TestResultDisplay, 
        f"\n"+
        f"1. /. \n"+
        f"2. 1)  EVSE_PLUG_LOCK_STATE ={EVSEPlugLockState}(BEPR connector unlocked). \n"+
        f"2. 2)  BEPR_LockLEDCommand= OFF.\n"+
        f"2. 3)  BEPR Charge LED is blinding green.\n"+
        f"2. 4)  Result_Test_ACPhaseOutOfRange= NOK (have 156 fault trigger).\n"+
        f"2. 4)  Result_Test_ProxiVoltageOutOfRange= NOK (have 157 fault trigger).\n"+
        f"2. 4)  Result_Test_PilotDutyOutOfRange= NOK (have 158 fault trigger).\n"+
        f"2. 4)  Result_Test_DCLinesOutOfRange= NOK (have 159 fault trigger).\n"+
        f"\n"+
        f"========================================================================="+
        f"\n"+
        f"{all_prints}"
    )



