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
    STLA_CAN.DBC.ConfigureSetting('EVTECH_STLA-M_TS-VF-2', 'TS-DCS-02', RecordFileType.BLF, None)
    STLA_CAN.DBC.SetChannel('All', ['ALL'], RecordEnum.ON)
    STLA_CAN.DBC.RecordState(AcqEnum.Start)
    InitAllCANMessage()
    STLA_CAN.DBC.SetSignal(1, 'DYN_E_VCU_342', 'REVEIL_PRINCIPAL', 0)

    低压辅源.SCPI.Write(':SOUR1:VOLT 12.5;:SOUR1:CURR 3;:OUTP CH1,ON')
    Sleep(65000)

    低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
    Sleep(10)

    EndTime = TimeStamp()       # 获取毫秒级时间戳
    Test, DCDCStateBB = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_541','DCDC_STATE_BB', 0.0)
    TestResult = DCDCStateBB == 1
    Sleep(2000)

    CloseAllCANMessage()
    CloseAllDevice()
    STLA_CAN.DBC.RecordState(AcqEnum.Stop)

    Test, dArrTimeStamp1, dArrTimeStampList= STLA_CAN.DBC.FindValueOfSignal('DAT_OBC_DCDC_541','DCDC_STATE_BB',1,ConditionEnum.Equal,0,0,[],[])
    StartTime = dArrTimeStamp1[0]

    CursorPosition = [StartTime, EndTime]
    print(TestResult , DCDCStateBB, CursorPosition)
    if TestResult == True:
        TestResultDisplay = '合格'
        print(TestResultDisplay)
    else:
        TestResultDisplay = '不合格'
        print(TestResultDisplay)