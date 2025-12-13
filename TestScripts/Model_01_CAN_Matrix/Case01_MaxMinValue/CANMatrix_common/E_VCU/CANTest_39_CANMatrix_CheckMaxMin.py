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
    低压辅源.SCPI.Write(':SOUR1:VOLT 12.5;:SOUR1:CURR 3;:OUTP CH1,ON')
    低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
    低压辅源.SCPI.Write(':SOUR3:VOLT 0.6;:SOUR3:CURR 3;:OUTP CH3,ON')
    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='220')
    Sleep(2500)
    Log4NetWrapper.InitLogManage("STLA-M-VC1_CANMatrix_CheckMaxMin", get_current_filename())
    STLA_CAN.DBC.ConfigureSetting('STLA-M-VC1_CANMatrix_CheckMaxMin', get_current_filename(), RecordFileType.BLF, None)
    STLA_CAN.DBC.SetChannel('All', ['ALL'], RecordEnum.ON)
    STLA_CAN.DBC.RecordState(AcqEnum.Start)
    InitAllCANMessage()
    STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_398','MAX_INDI_DISCHRG_CURR',0)
    StartTime = TimeStamp()     # 获取毫秒级时间戳
    Sleep(15000)
    STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_398','MAX_INDI_DISCHRG_CURR',2000)
    EndTime = TimeStamp()       # 获取毫秒级时间戳
    Sleep(5000)
    STLA_CAN.DBC.RecordState(AcqEnum.Stop)
    CloseAllDevice()
    CloseAllCANMessage()

    Test, dArrTimeStamp1, dArrTimeStampList1= STLA_CAN.DBC.FindValueOfSignal('DAT_E_VCU_398','MAX_INDI_DISCHRG_CURR',0,ConditionEnum.Equal,0,0,[],[])
    Test, dArrTimeStamp2, dArrTimeStampList2= STLA_CAN.DBC.FindValueOfSignal('DAT_E_VCU_398','MAX_INDI_DISCHRG_CURR',2000,ConditionEnum.Equal,0,0,[],[])
    FindReqTime = dArrTimeStamp1[10]
    FindStateTime = dArrTimeStamp2[0]

    CursorPosition = [FindReqTime, FindStateTime]
    STLA_CAN.DBC.ExportWfmFile(['DAT_E_VCU_398'],
                                ['MAX_INDI_DISCHRG_CURR'],
                                ''
    )
    Sleep(2000)
    STLA_CAN.DBC.ConfigureCursor(CursorEnum.X,CursorPosition)
    STLA_CAN.DBC.ExportImage(ImageFormatEnum.PNG,ColorInversionEnum.ON,'')

    # print(f" 前置步骤结果：{PreCondition}, 测试步骤1结果: {TestResult1}")
    # TestResult = True if PreCondition and TestResult1  else False
    # if TestResult == True:
    #     TestResultDisplay = '合格'
    #     Log4NetWrapper.WriteToOutput(f'测试结果:{TestResultDisplay}')
    #     print(TestResultDisplay)
    # else:
    #     TestResultDisplay = '不合格'
    #     Log4NetWrapper.WriteToOutput(f'测试结果:{TestResultDisplay}')
    #     print(TestResultDisplay)

    # Log4NetWrapper.WriteToOutput_KeyInfo(TestResultDisplay, 
    #     f'Actual test result: 1. In Standby mode, OBC shall have no power output, the output current of EVSE_CCS_PLUGIN_CURRENT_ST is {EVSE_CCS_PLUGIN_CURRENT_ST}A.\n'
    # )
