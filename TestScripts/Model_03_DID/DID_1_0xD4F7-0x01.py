from CommonFunction.FunctionClass_V2 import *
from UtilityClass.UtilityClass01_DeviceConnectInit import *
from CommonFunction.Common00_Fuction import *
from CommonFunction.Common04_SoftwareCommonFunction import STLA_M_EncapsulationClass

if __name__ == '__main__':

    start_capture_prints()
    STLA_M_EncapsulationClass.InitDevice()
    STLA_M_EncapsulationClass.InitAllCANMessage()
    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = True, case_name = "STLA-M-STEP2.5_DID")
    PreCondition = STLA_M_EncapsulationClass.EnterPlantModePreCondition(CONFIG_VHL = 1)
   
    继电器控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='8181')
    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='220')
    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('BMS_DC_RELAY_MES_EVSE_VOLTAGE'),'BMS_DC_RELAY_MES_EVSE_VOLTAGE', 20)
    信号发生器.SCPI.Write(':SOUR1:APPL:SQU 1000,12.1,0,0;:SOUR1:FUNC:SQU:DCYC 50;:OUTP1 ON')
    交流源载一体机.Set.Basic(ACPwrModeEnum.SOUR, ACChannelEnum.EACH, ACCouplingEnum.AC,0, ACPwrWorkModeEnum.CC)
    交流源载一体机.Set.Freq(dFreq=50)
    交流源载一体机.Set.Volt(dealListData([20.0, 20.0, 20.0]),dealListData([0.0, 0.0, 0.0]))
    交流源载一体机.Out.Enable(ACeEnable.ON)
    Sleep(17000)

    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('CABLE_LOCK_REQ'),'CABLE_LOCK_REQ', 2)
    Sleep(1000)
    Test, EVSEPlugLockState = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('EVSE_PLUG_LOCK_STATE'),'EVSE_PLUG_LOCK_STATE', 0.0)
    TestResult2 = EVSEPlugLockState == 0
    print(f"EVSE_PLUG_LOCK_STATE={EVSEPlugLockState}时, 测试结果={TestResult2}")


    AssignmentCode1 = 156
    AssignmentCode2 = 157
    AssignmentCode3 = 158
    AssignmentCode4 = 159
    TestResult31 = not(STLA_M_EncapsulationClass.CheckFaultIsInFaultList(AssignmentCode1))
    TestResult32 = not(STLA_M_EncapsulationClass.CheckFaultIsInFaultList(AssignmentCode2))
    TestResult33 = not(STLA_M_EncapsulationClass.CheckFaultIsInFaultList(AssignmentCode3))
    TestResult34 = not(STLA_M_EncapsulationClass.CheckFaultIsInFaultList(AssignmentCode4))
    TestResult3 = TestResult31 and TestResult32 and TestResult33 and TestResult34
    print(f"Result_Test_ACPhaseOutOfRange= {TestResult31}")
    print(f"Result_Test_ProxiVoltageOutOfRange= {TestResult32}")
    print(f"Result_Test_PilotDutyOutOfRange= {TestResult33}")
    print(f"Result_Test_DCLinesOutOfRange= {TestResult34}")


    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='2300')
    Sleep(1500)
    Test, OBCChrgConnConf1 = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('OBC_CHRG_CONN_CONF'),'OBC_CHRG_CONN_CONF', 0.0)
    TestResult41 = OBCChrgConnConf1 == 0
    TestResult42 = debug_break("The signal of BEPR_LockLEDCommand = OFF.", timeout = 30)
    TestResult4 = TestResult41 and TestResult42
    print(f"OBC_CHRG_CONN_CONF={OBCChrgConnConf1}, 测试结果={TestResult41}")
    print(f"Charge LED is White,测试结果={TestResult42}")

    STLA_CAN.DBC.SendMessage(1,'REQ_DIAG_ON_CAN_590',['793','527','0','0'], 1, 100) # 03 19 02 0F
    Sleep(2500)
    STLA_CAN.DBC.SendMessage(1,'REQ_DIAG_ON_CAN_590',['802','54717','0','0'], 1, 100)  # 03 22 D5 BD
    Sleep(2500)
    STLA_CAN.DBC.SendMessage(1,'REQ_DIAG_ON_CAN_590',['802','54519','0','0'], 1, 100)  # 03 22 D4 F7
    Sleep(2500)


    STLA_M_EncapsulationClass.ExitPlantMode()
    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = False, case_name = "STLA-M-STEP2.5_DID")
    STLA_M_EncapsulationClass.RCD_Exit_EcoMode()
    STLA_M_EncapsulationClass.CloseAllDevice()
    STLA_M_EncapsulationClass.CloseAllCANMessage()
    TestResult1 = STLA_M_EncapsulationClass.PlantModeScreenshot(faultcode=AssignmentCode1, VerifyWhetherReportFault=False)


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
        f"1. Test finished and test result are OK==>{TestResult3}. \n"+
        f"2. 1) OBC_CHRG_CONN_CONF = {OBCChrgConnConf1} (BEPR connector unlocked). \n"+
        f"   2) The signal of BEPR_LockLEDCommand =OFF {TestResult42}\n"+
        f"   3)DTC is healing(UDS service19 02 0F).\n"+
        f"\n"+
        f"========================================================================="+
        f"\n"+
        f"{all_prints}"
    )





    
    







