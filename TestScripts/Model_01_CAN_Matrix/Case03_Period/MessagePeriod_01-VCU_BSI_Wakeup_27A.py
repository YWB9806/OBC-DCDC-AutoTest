from CommonFunction.FunctionClass_V2 import *
from UtilityClass.UtilityClass01_DeviceConnectInit import *
from CommonFunction.Common00_Fuction import *
from CommonFunction.Common01_InitDevice import InitDevice
from CommonFunction.Common01_CloseDevice import CloseAllDevice
from CommonFunction.Common02_InitCANMessage import InitAllCANMessage
from CommonFunction.Common03_CloseCANMessage import CloseAllCANMessage


if __name__ == '__main__':
    InitDevice()
    Sleep(1000)
    Log4NetWrapper.InitLogManage("STLA-M_CANMatrix_MessagePeriod", get_current_filename())
    STLA_CAN.DBC.ConfigureSetting('STLA-M_CANMatrix_MessagePeriod', get_current_filename(), RecordFileType.BLF, None)
    STLA_CAN.DBC.SetChannel('All', ['ALL'], RecordEnum.ON)
    # STLA_CAN.DBC.RecordState(AcqEnum.Start)

    低压辅源.SCPI.Write(':SOUR1:VOLT 12.5;:SOUR1:CURR 3;:OUTP CH1,ON')
    InitAllCANMessage()
    Sleep(8000)

    Test, MeasureKL30Current = 低压辅源.SCPI.Query(':MEAS:CURR? CH1')
    MeasureKL30Current = list(MeasureKL30Current)
    PreTestResult = MeasureKL30Current[0] <= 0.05
    print(MeasureKL30Current[0], PreTestResult)

    低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
    低压辅源.SCPI.Write(':SOUR3:VOLT 0.6;:SOUR3:CURR 3;:OUTP CH3,ON')
    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='220')
    Sleep(2500)

    STLA_CAN.DBC.RecordState(AcqEnum.Start)
    StartTime = TimeStamp()     # 获取毫秒级时间戳
    Sleep(15000)
    Sleep(5000)
    EndTime = TimeStamp()       # 获取毫秒级时间戳
    STLA_CAN.DBC.RecordState(AcqEnum.Stop)
    CloseAllDevice()
    CloseAllCANMessage()

    ExpectOfFramePeriod = 50
    # Test, out1, out2, out3, out4 = STLA_CAN.DBC.MsgStatisticsInfo('VCU_BSI_Wakeup_27A',0.0,0.0)
    # Test, out1, out2, out3, out4 = STLA_CAN.DBC.MsgStatisticsInfo('VCU_BSI_Wakeup_27A',StartTime,EndTime)
    Test, out1, out2, out3, out4 = STLA_CAN.DBC.MsgStatisticsInfo('VCU_BSI_Wakeup_27A',float(StartTime),float(EndTime))
    TestResult = abs(out2 - ExpectOfFramePeriod) <= 2
    print(f"MsgStatisticsInfo: 报文累计收发次数 {out1}, 报文平均周期 {out2}, 报文最大周期 {out3}, 报文最小周期 {out4}")

    if TestResult == True:
        TestResultDisplay = '合格'
        print(TestResultDisplay)
    else:
        TestResultDisplay = '不合格'
        print(TestResultDisplay)

    Log4NetWrapper.WriteToOutput(f'本条脚本测试ID为: '+ get_current_filename() +'\n')
    Log4NetWrapper.WriteToOutput(f'测试结果: {TestResultDisplay}')
    Log4NetWrapper.WriteToOutput(f'==============================================')
    Log4NetWrapper.WriteToOutput(f'实测报文累计收发次数: {out1}')
    Log4NetWrapper.WriteToOutput(f'预期报文周期为: {ExpectOfFramePeriod}ms')
    Log4NetWrapper.WriteToOutput(f'实测报文平均周期: {out2}ms; 实测报文最小周期: {out4}ms; 实测报文最大周期: {out3}ms')
    Log4NetWrapper.WriteToOutput(f'==============================================')
    # Log4NetWrapper.WriteToOutput_KeyInfo(TestResultDisplay, 
    #     f'Actual test result: 1. In Standby mode, OBC shall have no power output, the output current of EVSE_CCS_PLUGIN_CURRENT_ST is {EVSE_CCS_PLUGIN_CURRENT_ST}A.\n'
    # )
