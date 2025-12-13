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

    STLA_CAN.DBC.SendMessage(1,'REQ_DIAG_ON_CAN_590',['802','54717','0','0'], 1, 100)  # 03 22 D5 BD

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
    TestResult42 = debug_break("Charge LED is White.", timeout = 30)
    TestResult4 = TestResult41 and TestResult42
    print(f"OBC_CHRG_CONN_CONF={OBCChrgConnConf1}, 测试结果={TestResult41}")
    print(f"Charge LED is White,测试结果={TestResult42}")

    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='500')
    Sleep(1500)
    Test, OBCChrgConnConf2 = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('OBC_CHRG_CONN_CONF'),'OBC_CHRG_CONN_CONF', 0.0)
    TestResult5 = OBCChrgConnConf2 == 2
    print(f"OBC_CHRG_CONN_CONF={OBCChrgConnConf2}, 测试结果={TestResult5}")

    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('RECHARGE_HMI_STATE_EVO'),'RECHARGE_HMI_STATE_EVO', 4)
    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='6')
    Sleep(1500)
    Test, OBCChrgConnConf3 = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('OBC_CHRG_CONN_CONF'),'OBC_CHRG_CONN_CONF', 0.0)
    TestResult61 = OBCChrgConnConf3 == 3
    TestResult62 = debug_break("Charge LED is solid green color.", timeout = 30)
    TestResult6 = TestResult61 and TestResult62
    print(f"OBC_CHRG_CONN_CONF={OBCChrgConnConf3}, 测试结果={TestResult61}")
    print(f"Charge LED is solid green color,测试结果={TestResult62}")


    STLA_M_EncapsulationClass.ExitPlantMode()
    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = False, case_name = "STLA-M-STEP2.5_PlantMode")
    STLA_M_EncapsulationClass.RCD_Exit_EcoMode()
    STLA_M_EncapsulationClass.CloseAllDevice()
    STLA_M_EncapsulationClass.CloseAllCANMessage()
    TestResult1 = STLA_M_EncapsulationClass.PlantModeScreenshot(faultcode=AssignmentCode1, VerifyWhetherReportFault=False)


    print(f"前置条件结果:{PreCondition}, 测试步骤1结果: {TestResult1}, 测试步骤2结果: {TestResult2}, 测试步骤3结果: {TestResult3}, 测试步骤4结果: {TestResult4}, 测试步骤5结果: {TestResult5}, 测试步骤6结果: {TestResult6}")
    TestResult = True if PreCondition and TestResult1 and TestResult2 and TestResult3 and TestResult4 and TestResult5 and TestResult6 else False
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
        f"2. OBC_CHRG_CONN_CONF = {OBCChrgConnConf1} and Charge LED is White{TestResult42} . \n"+
        f"3. /.\n"+
        f"4. OBC_CHRG_CONN_CONF = 01: PARTIALLY PLUGGED OR {OBCChrgConnConf2} OR {OBCChrgConnConf3},RECHARGE_HMI_STATE_EVO=4 Finished,  Charge LED is solid green color{TestResult62}.\n"+
        f"\n"+
        f"========================================================================="+
        f"\n"+
        f"{all_prints}"
    )











