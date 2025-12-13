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
    Log4NetWrapper.InitLogManage("EVTECH_STLA-M_TS-VF-2", "TS-LED-LOCK-02")
    STLA_CAN.DBC.ConfigureSetting('EVTECH_STLA-M_TS-VF-2', 'TS-LED-LOCK-02', RecordFileType.BLF, None)
    STLA_CAN.DBC.SetChannel('All', ['ALL'], RecordEnum.ON)
    STLA_CAN.DBC.RecordState(AcqEnum.Start)
    InitAllCANMessage()

    低压辅源.SCPI.Write(':SOUR1:VOLT 14:SOUR1:CURR 3;:OUTP CH1,ON')
    低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
    低压辅源.SCPI.Write(':SOUR3:VOLT 0.6;:SOUR3:CURR 3;:OUTP CH3,ON')
    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='150')
    信号发生器.SCPI.Write(':SOUR1:APPL:SQU 1000,18.1,0,0;:SOUR1:FUNC:SQU:DCYC 80;:OUTP1 ON')
    Sleep(2000)

    Test , OBCFaultState = STLA_CAN.DBC.GetSignal(1, 'DAT_OBC_DCDC_421', 'OBC_FAULT_STATE', 0.0)
    Test , AcdcConversionState = STLA_CAN.DBC.GetSignal(1, 'DAT_OBC_DCDC_501', 'ACDC_CONVERSION_STATE', 0.0)
    PreTestResult1 = OBCFaultState == 0
    PreTestResult2 = AcdcConversionState == 0
    PreCondition = True if PreTestResult1 and PreTestResult2 else False
    print(PreTestResult1,PreTestResult2)
    Log4NetWrapper.WriteToOutput(f'OBC_FAULT_STATE:{OBCFaultState},ACDC_CONVERSION_STATE:{AcdcConversionState}')
    Log4NetWrapper.WriteToOutput(f'PreCondition:{PreCondition},PreTestResult1:{PreTestResult1},PreTestResult2:{PreTestResult2}')
    Sleep(1000)

    STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','CABLE_LOCK_REQ',1)
    Sleep(2000)

    StartTime = TimeStamp()     # 获取毫秒级时间戳
    Test , EvsePlugLockState1 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_421','EVSE_PLUG_LOCK_STATE', 0.0)
    TestResult1 = EvsePlugLockState1 == 1

    STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','CABLE_LOCK_REQ',2)
    Sleep(2000)

    EndTime = TimeStamp()       # 获取毫秒级时间戳
    Test , EvsePlugLockState2 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_421','EVSE_PLUG_LOCK_STATE', 0.0)
    TestResult2 = EvsePlugLockState2 == 0
    Log4NetWrapper.WriteToOutput(f'EVSE_PLUG_LOCK_STATE:{EvsePlugLockState1},EVSE_PLUG_LOCK_STATE:{EvsePlugLockState2}')
    Log4NetWrapper.WriteToOutput(f'TestResult1:{TestResult1},TestResult2:{TestResult2}')

    Sleep(2000)
    CloseAllCANMessage()
    CloseAllDevice()
    STLA_CAN.DBC.RecordState(AcqEnum.Stop)

    CursorPosition = [StartTime, EndTime]
    print(f"前置条件结果:{PreCondition}, 测试步骤1结果: {TestResult1}, 测试步骤2结果: {TestResult2},时间戳: {CursorPosition}")
    TestResult = True if PreCondition and TestResult1 and TestResult2 else False
    if TestResult == True:
        TestResultDisplay = '合格'
        print(TestResultDisplay)
        Log4NetWrapper.WriteToOutput(f'测试结果:{TestResultDisplay}')
    else:
        TestResultDisplay = '不合格'
        print(TestResultDisplay)
        Log4NetWrapper.WriteToOutput(f'测试结果:{TestResultDisplay}')
    Log4NetWrapper.WriteToOutput(f'$Report:Test result:{TestResultDisplay}#,$Actual test result:1. EVSE_PLUG_LOCK_STATE = {EvsePlugLockState1},2. EVSE_PLUG_LOCK_STATE = {EvsePlugLockState2}#')
