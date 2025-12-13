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
    STLA_CAN.DBC.ConfigureSetting('EVTECH_STLA-M_TS-VF-2', 'TS-LED-LOCK-30', RecordFileType.BLF, None)
    STLA_CAN.DBC.SetChannel('All', ['ALL'], RecordEnum.ON)
    STLA_CAN.DBC.RecordState(AcqEnum.Start)
    InitAllCANMessage()

    低压辅源.SCPI.Write(':SOUR1:VOLT 12.5;:SOUR1:CURR 3;:OUTP CH1,ON')
    低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
    电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data='220')
    信号发生器.SCPI.Write(':SOUR1:APPL:SQU 1000,12.1,0,0;:SOUR1:FUNC:SQU:DCYC 80;:OUTP1 ON')
    Sleep(1000)

    Test, OBCFaultState = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_421','OBC_FAULT_STATE', 0.0)
    Test, AcdcConversionState = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','ACDC_CONVERSION_STATE', 0.0)
    print(f"OBC故障等级:{OBCFaultState}, OBC状态: {AcdcConversionState}")
    PreTestResult1 = OBCFaultState == 0
    PreTestResult2 = AcdcConversionState == 0
    PreCondition = True if PreTestResult1 and PreTestResult2 else False

    STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_402','RECHARGE_HMI_STATE_EVO',5)
    Sleep(2000)

    示波器.Acq.State(StateEnum.Stop)
    Sleep(500)
    Test , MeasureDataList= 示波器.Meas.Value(['CH1_2', 'CH1_2', 'CH1_2', 'CH1_2'],['PER','FREQ','DUTY','NDUTY'])
    TestResult11 = MeasureDataList[0] == 500 * 0.001
    TestResult12 = MeasureDataList[1] == 200
    TestResult13 = (MeasureDataList[2] + MeasureDataList[3] == 1)
    TestResult1 = True if TestResult11 and TestResult12 and TestResult13 else False
    print(f'周期:{MeasureDataList[0] * 0.001},频率:{MeasureDataList[1]},正占空比:{MeasureDataList[2]},负占空比:{MeasureDataList[3]}')

    示波器.Save.Image('','EVTECH','TS2')
    Sleep(1000)

    CloseAllCANMessage()
    CloseAllDevice()
    STLA_CAN.DBC.RecordState(AcqEnum.Stop)

    TestResult = True if PreCondition and TestResult1 else False
    if TestResult == True:
        TestResultDisplay = '合格'
        print(TestResultDisplay)
    else:
        TestResultDisplay = '不合格'
        print(TestResultDisplay)
    
