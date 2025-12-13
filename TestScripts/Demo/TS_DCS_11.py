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
    STLA_CAN.DBC.ConfigureSetting('EVTECH_STLA-M_TS-VF-2', 'TS_DCS_11', RecordFileType.BLF, None)
    STLA_CAN.DBC.SetChannel('All', ['ALL'], RecordEnum.ON)
    STLA_CAN.DBC.RecordState(AcqEnum.Start)
    InitAllCANMessage()
    低压辅源.SCPI.Write(':SOUR1:VOLT 12.5;:SOUR1:CURR 3;:OUTP CH1,ON')
    低压辅源.SCPI.Write(':SOUR2:VOLT 2.1;:SOUR2:CURR 3;:OUTP CH2,ON')
    Sleep(5000)

    低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
    Sleep(2000)

    高压源载一体机.Set.Basic(DCPwrModeEnum.NORM, DCPwrWorkModeEnum.NONE)
    高压源载一体机.Set.Volt(dVolt=375)
    高压源载一体机.Out.Enable(eEnable.ON)
    Sleep(2000)

    STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','REG_MODE_DCDC_BB_REQ',1)
    Sleep(1000)

    StartTime = TimeStamp()       # 获取毫秒级时间戳
    Test, DCDCStateBB1 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_541','DCDC_STATE_BB', 0.0)
    PreCondition = DCDCStateBB1 == 3

    高压源载一体机.Set.Volt(dVolt=480)
    Sleep(1000)

    EndTime = TimeStamp()       # 获取毫秒级时间戳
    Test, DCDCStateBB2 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_541','DCDC_STATE_BB', 0.0)
    TestResult1 = DCDCStateBB2 == 5

    CloseAllCANMessage()
    CloseAllDevice()
    STLA_CAN.DBC.RecordState(AcqEnum.Stop)

    CursorPosition = [StartTime, EndTime]
    print(f"前置条件结果:{PreCondition}, 测试步骤1结果: {TestResult1}")
    TestResult = True if PreCondition and TestResult1 else False
    if TestResult == True:
        TestResultDisplay = '合格'
        print(TestResultDisplay)
    else:
        TestResultDisplay = '不合格'
        print(TestResultDisplay)
