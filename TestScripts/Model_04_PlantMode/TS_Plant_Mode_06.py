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
    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('OBC_EVSE_REQUEST'),'OBC_EVSE_REQUEST', 1)
    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('CABLE_LOCK_REQ'),'CABLE_LOCK_REQ', 1)
    信号发生器.SCPI.Write(':SOUR1:APPL:SQU 1000,12.1,0,0;:SOUR1:FUNC:SQU:DCYC 80;:OUTP1 ON')
    交流源载一体机.Set.Basic(ACPwrModeEnum.SOUR, ACChannelEnum.EACH, ACCouplingEnum.AC,0, ACPwrWorkModeEnum.CC)
    交流源载一体机.Set.Freq(dFreq=50)
    交流源载一体机.Set.Volt(dealListData([220.0, 220.0, 220.0]),dealListData([0.0, 0.0, 0.0]))
    交流源载一体机.Out.Enable(ACeEnable.ON)
    Sleep(17000)

    STLA_CAN.DBC.SetSignal(1, get_message_for_signal('ACDC_CONVERSION_REQUEST'),'ACDC_CONVERSION_REQUEST', 1)
    Sleep(1000)
    Test, OBCEvseState = STLA_CAN.DBC.GetSignal(1,get_message_for_signal('OBC_EVSE_STATE'),'OBC_EVSE_STATE', 0.0)
    TestResult2 = OBCEvseState == 6
    print(f"OBC_EVSE_STATE={OBCEvseState}, 测试结果={TestResult2}")

    STLA_CAN.DBC.SendMessage(1,'REQ_DIAG_ON_CAN_590',['802','54717','0','0'], 1, 100)  # 03 22 D5 BD

    AssignmentCode1 = 156
    AssignmentCode2 = 158
    TestResult31 = STLA_M_EncapsulationClass.CheckFaultIsInFaultList(AssignmentCode1)
    TestResult32 = STLA_M_EncapsulationClass.CheckFaultIsInFaultList(AssignmentCode2)
    TestResult3 = TestResult31 and TestResult32
    print(f"Result_Test_ACPhaseOutOfRange= {TestResult31}")
    print(f"Result_Test_PilotDutyOutOfRange= {TestResult32}")

    STLA_M_EncapsulationClass.ExitPlantMode()
    STLA_M_EncapsulationClass.TestCaseConfig(RecordStart = False, case_name = "STLA-M-STEP2.5_PlantMode")
    STLA_M_EncapsulationClass.RCD_Exit_EcoMode()
    STLA_M_EncapsulationClass.CloseAllDevice()
    STLA_M_EncapsulationClass.CloseAllCANMessage()
    TestResult1 = STLA_M_EncapsulationClass.PlantModeScreenshot(faultcode=AssignmentCode1, VerifyWhetherReportFault=True)


    print(f"前置条件结果:{PreCondition}, 测试步骤1结果: {TestResult1}, 测试步骤2结果: {TestResult2}, 测试步骤3结果: {TestResult3}")
    TestResult = True if PreCondition and TestResult1 and TestResult2 and TestResult3 else False
    if TestResult == True:
        TestResultDisplay = '合格'
        print(TestResultDisplay)
    else:
        TestResultDisplay = '不合格'
        print(TestResultDisplay)
    
    all_prints = stop_capture_prints()
    Log4NetWrapper.WriteToOutput_KeyInfo(TestResultDisplay, 
        f"\n"+
        f"1./. \n"+
        f"2.OBC_EVSE_STATE= {OBCEvseState}. \n"+
        f"\n"+
        f"========================================================================="+
        f"\n"+
        f"{all_prints}"
    )

