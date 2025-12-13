from CommonFuction.FunctionClass_V2 import *
from UtilityClass.UtilityClass01_DeviceConnectInit import *
# from UtilityClass.UtilityClass02_TSCANConnectInit import *
from CommonFuction.Common00_Fuction import *
from CommonFuction.Common01_InitDevice import InitDevice
from CommonFuction.Common01_CloseDevice import CloseAllDevice
from CommonFuction.Common02_InitCANMessage import InitAllCANMessage
from CommonFuction.Common03_CloseCANMessage import CloseAllCANMessage

if __name__ == '__main__':

    InitDevice()
    Sleep(1000)
    STLA_CAN.DBC.ConfigureSetting('EVTECH_STLA-M_RCD', 'RCD_test_116', RecordFileType.BLF, None)
    STLA_CAN.DBC.SetChannel('All', ['ALL'], RecordEnum.ON)
    STLA_CAN.DBC.RecordState(AcqEnum.Start)

    低压辅源.SCPI.Write(':SOUR1:VOLT 12.5;:SOUR1:CURR 3;:OUTP CH1,ON')
    低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
    InitAllCANMessage()
    Sleep(2000)

    Test, RcdLineState = STLA_CAN.DBC.GetSignal(1,'SUPV_V2_OBC_DCDC_591','RCD_LINE_STATE', 0.0)
    PreTestResult1 = RcdLineState == 1

    信号发生器.SCPI.Write(':SOUR1:APPL:SQU 1000,9.4,0,0;:SOUR1:FUNC:SQU:DCYC 78;:OUTP1 ON')
    Sleep(1500)

    Test, EcuElecStateRCD = STLA_CAN.DBC.GetSignal(1,'SUPV_V2_OBC_DCDC_591','ECU_ELEC_STATE_RCD', 0.0)
    Test, OBCFaultState = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_421','OBC_FAULT_STATE', 0.0)
    Test, DCDCFaultState = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','DCDC_FAULT_STATE', 0.0)
    Test, CoolingWakeupState1 = STLA_CAN.DBC.GetSignal(1,'SUPV_V2_OBC_DCDC_591','COOLING_WUP_STATE', 0.0)
    PreTestResult2 = EcuElecStateRCD == 0
    PreTestResult3 = OBCFaultState == 0 and DCDCFaultState == 0
    PreTestResult4 = CoolingWakeupState1 == 0
    PreCondition = True if PreTestResult1 and PreTestResult2 and PreTestResult3 and PreTestResult4 else False
    print(f"前置条件1结果:{PreTestResult1}, 前置条件2结果: {PreTestResult2}, 前置条件3结果: {PreTestResult3}, 前置条件4结果: {PreTestResult4}")

    STLA_CAN.DBC.SetSignal(1,'DYN_E_VCU_342','COOLING_WAKEUP',1)
    STLA_CAN.DBC.SetSignal(1,'DYN_E_VCU_342','REVEIL_PRINCIPAL',1)
    Sleep(500)

    Test, CoolingWakeupState2 = STLA_CAN.DBC.GetSignal(1,'SUPV_V2_OBC_DCDC_591','COOLING_WUP_STATE', 0.0)
    TestResult1 = CoolingWakeupState2 == 1

    CloseAllCANMessage()
    CloseAllDevice()
    STLA_CAN.DBC.RecordState(AcqEnum.Stop)

    print(f"前置条件结果:{PreCondition}, 测试步骤1结果: {TestResult1}")
    TestResult = True if PreCondition and TestResult1 else False
    if TestResult == True:
        TestResultDisplay = '合格'
        print(TestResultDisplay)
    else:
        TestResultDisplay = '不合格'
        print(TestResultDisplay)
    
