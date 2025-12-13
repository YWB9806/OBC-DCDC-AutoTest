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
    STLA_CAN.DBC.ConfigureSetting('EVTECH_STLA-M_TS-VF-2', 'TS-OBCS-06', RecordFileType.BLF, None)
    STLA_CAN.DBC.SetChannel('All', ['ALL'], RecordEnum.ON)
    STLA_CAN.DBC.RecordState(AcqEnum.Start)
    InitAllCANMessage()

    低压辅源.SCPI.Write(':SOUR1:VOLT 12.5;:SOUR1:CURR 3;:OUTP CH1,ON')
    低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='150')
    信号发生器.SCPI.Write(':SOUR1:APPL:SQU 1000,12.1,0,0;:SOUR1:FUNC:SQU:DCYC 80;:OUTP1 ON')
    Sleep(1000)

    Test , OBCEvseState1 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_441','OBC_EVSE_STATE', 0.0)
    TestResult1 = OBCEvseState1 == 1

    交流源载一体机.Set.Basic(ACPwrModeEnum.SOUR, ACChannelEnum.SING, ACCouplingEnum.AC,0, ACPwrWorkModeEnum.CC)
    交流源载一体机.Set.Freq(dFreq=50)
    交流源载一体机.Set.Volt(dealListData([230.0, 0.0, 0.0]),dealListData([0.0, 0.0, 0.0]))
    高压源载一体机.Set.Basic(DCPwrModeEnum.NORM, DCPwrWorkModeEnum.NONE)
    高压源载一体机.Set.Volt(dVolt=350)

    交流源载一体机.Out.Enable(ACeEnable.ON)
    高压源载一体机.Out.Enable(eEnable.ON)

    STLA_CAN.DBC.SetSignal(1, 'DAT_E_VCU_448', 'OBC_EVSE_REQUEST', 1)
    STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','CABLE_LOCK_REQ',1)
    Sleep(1000)

    StartTime = TimeStamp()     # 获取毫秒级时间戳
    Test , OBCFaultState = STLA_CAN.DBC.GetSignal(1, 'DAT_OBC_DCDC_421', 'OBC_FAULT_STATE', 0.0)
    Test , AcdcConversionState = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','ACDC_CONVERSION_STATE', 0.0)
    PreTestResult1 = OBCFaultState == 0
    PreTestResult2 = AcdcConversionState == 0

    Test , OBCEvseState = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_441','OBC_EVSE_STATE', 0.0)
    Test , EvsePlugLockState = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_421','EVSE_PLUG_LOCK_STATE', 0.0)
    Test , OBCFaultState = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_421','OBC_FAULT_STATE', 0.0)
    PreTestResult3 = OBCEvseState == 5
    PreTestResult4 = EvsePlugLockState == 1
    PreTestResult5 = OBCFaultState == 0
    PreCondition = True if PreTestResult1 and PreTestResult2 and PreTestResult3 and PreTestResult4 and PreTestResult5 else False
    print(PreTestResult1,PreTestResult2,PreTestResult3,PreTestResult4,PreTestResult5)
    Sleep(1500)

    STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','ACDC_CONVERSION_REQUEST',1)
    Sleep(500)

    EndTime = TimeStamp()       # 获取毫秒级时间戳
    Test , PItoHVConversionState1 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','ACDC_CONVERSION_STATE', 0.0)
    Test , AcChargeModeAvail = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','AC_CHARGE_MODE_AVAIL', 0.0)
    TestResult2 = PItoHVConversionState1 == 2
    TestResult3 = AcChargeModeAvail == 1
    Sleep(2000)

    CloseAllCANMessage()
    CloseAllDevice()
    STLA_CAN.DBC.RecordState(AcqEnum.Stop)
    CursorPosition = [StartTime, EndTime]

    print(f"前置条件结果:{PreCondition}, 测试步骤1结果: {TestResult1}, 测试步骤2结果: {TestResult2}, 测试步骤3结果: {TestResult3}")
    TestResult = True if PreCondition and TestResult1 and TestResult2 and TestResult3 else False
    if TestResult == True:
        TestResultDisplay = '合格'
        print(TestResultDisplay)
    else:
        TestResultDisplay = '不合格'
        print(TestResultDisplay)
