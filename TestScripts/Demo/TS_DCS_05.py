from CommonFuction.FunctionClass_V2 import *
from UtilityClass.UtilityClass01_DeviceConnectInit import *
# from UtilityClass.UtilityClass02_TSCANConnectInit import *
from CommonFuction.Common00_Fuction import *
from CommonFuction.Common01_InitDevice import InitDevice
from CommonFuction.Common01_CloseDevice import CloseAllDevice
from CommonFuction.Common02_InitCANMessage import InitAllCANMessage
from CommonFuction.Common03_CloseCANMessage import CloseAllCANMessage

if __name__ == '__main__':

    # StartTestMethodTotal = [False,True]
    StartTestMethodTotal = [True,False]
    StartTestMethod1=StartTestMethodTotal[0]
    StartTestMethod2=StartTestMethodTotal[1]
    print(StartTestMethod1,StartTestMethod2)

    if StartTestMethod1 == True:
        InitDevice()
        Sleep(1000)
        STLA_CAN.DBC.ConfigureSetting('EVTECH_STLA-M_TS-VF-2', 'TS_DCS_05-1', RecordFileType.BLF, None)
        STLA_CAN.DBC.SetChannel('All', ['ALL'], RecordEnum.ON)
        STLA_CAN.DBC.RecordState(AcqEnum.Start)
        InitAllCANMessage()
        低压辅源.SCPI.Write(':SOUR1:VOLT 12.5;:SOUR1:CURR 3;:OUTP CH1,ON')
        低压辅源.SCPI.Write(':SOUR2:VOLT 2.1;:SOUR2:CURR 3;:OUTP CH2,ON')
        Sleep(5000)

        高压源载一体机.Set.Basic(DCPwrModeEnum.NORM, DCPwrWorkModeEnum.NONE)
        高压源载一体机.Set.Volt(dVolt=350)
        高压源载一体机.Out.Enable(eEnable.ON)
        Sleep(5000)

        StartTime = TimeStamp()       # 获取毫秒级时间戳
        STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','REG_MODE_DCDC_BB_REQ',1)
        Sleep(1000)

        低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
        Sleep(5000)

        EndTime = TimeStamp()       # 获取毫秒级时间戳
        Test, DCDCStateBB = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_541','DCDC_STATE_BB', 0.0)
        TestResult = DCDCStateBB == 3
        Sleep(1500)


        CloseAllCANMessage()
        CloseAllDevice()
        STLA_CAN.DBC.RecordState(AcqEnum.Stop)

        CursorPosition = [StartTime, EndTime]
        print(TestResult , DCDCStateBB)
        if TestResult == True:
            TestResultDisplay = '合格'
            print(TestResultDisplay)
        else:
            TestResultDisplay = '不合格'
            print(TestResultDisplay)

    if StartTestMethod2 == True:
        InitDevice()
        Sleep(1000)
        STLA_CAN.DBC.ConfigureSetting('EVTECH_STLA-M_TS-VF-2', 'TS_DCS_05-2', RecordFileType.BLF, None)
        STLA_CAN.DBC.SetChannel('All', ['ALL'], RecordEnum.ON)
        STLA_CAN.DBC.RecordState(AcqEnum.Start)
        InitAllCANMessage()
        低压辅源.SCPI.Write(':SOUR1:VOLT 12.5;:SOUR1:CURR 3;:OUTP CH1,ON')
        低压辅源.SCPI.Write(':SOUR2:VOLT 2.1;:SOUR2:CURR 3;:OUTP CH2,ON')
        Sleep(5000)

        高压源载一体机.Set.Basic(DCPwrModeEnum.NORM, DCPwrWorkModeEnum.NONE)
        高压源载一体机.Set.Volt(dVolt=350)
        高压源载一体机.Out.Enable(eEnable.ON)
        Sleep(5000)

        StartTime = TimeStamp()       # 获取毫秒级时间戳
        STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','REG_MODE_DCDC_BB_REQ',2)
        Sleep(1000)

        低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
        Sleep(5000)

        EndTime = TimeStamp()       # 获取毫秒级时间戳
        Test, DCDCStateBB = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_541','DCDC_STATE_BB', 0.0)
        TestResult = DCDCStateBB == 3
        Sleep(1500)


        CloseAllCANMessage()
        CloseAllDevice()
        STLA_CAN.DBC.RecordState(AcqEnum.Stop)

        CursorPosition = [StartTime, EndTime]
        print(TestResult , DCDCStateBB)
        if TestResult == True:
            TestResultDisplay = '合格'
            print(TestResultDisplay)
        else:
            TestResultDisplay = '不合格'
            print(TestResultDisplay)
