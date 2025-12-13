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
    STLA_CAN.DBC.ConfigureSetting('EVTECH_STLA-M_TS-VF-2', 'TS-LED-LOCK-04-AI', RecordFileType.BLF, None)
    STLA_CAN.DBC.SetChannel('All', ['ALL'], RecordEnum.ON)
    STLA_CAN.DBC.RecordState(AcqEnum.Start)
    InitAllCANMessage()

    低压辅源.SCPI.Write(':SOUR1:VOLT 12.5;:SOUR1:CURR 3;:OUTP CH1,ON')
    低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
    信号发生器.SCPI.Write(':SOUR1:APPL:SQU 1000,12.1,0,0;:SOUR1:FUNC:SQU:DCYC 80;:OUTP1 ON')
    Sleep(2000)

    Test, OBCFaultState = STLA_CAN.DBC.GetSignal(1, 'DAT_OBC_DCDC_421', 'OBC_FAULT_STATE', 0.0)
    Test, AcdcConversionState = STLA_CAN.DBC.GetSignal(1, 'DAT_OBC_DCDC_501', 'ACDC_CONVERSION_STATE', 0.0)
    PreTestResult1 = OBCFaultState == 0
    PreTestResult2 = AcdcConversionState == 0
    PreCondition = True if PreTestResult1 and PreTestResult2 else False
    print(PreTestResult1, PreTestResult2)
    Sleep(1000)

    SetCCResistance = 101
    list = []
    while SetCCResistance <= 270:
        电阻控制板.Modbus.SetRegister(iID=1, Reg=3072, Data=str(SetCCResistance))
        Sleep(1000)
        STLA_CAN.DBC.SetSignal(1, 'DAT_E_VCU_448', 'CABLE_LOCK_REQ', 1)
        Sleep(1000)
        Test, OBCChargeConnConf = STLA_CAN.DBC.GetSignal(1, 'DAT_OBC_DCDC_421', 'OBC_CHRG_CONN_CONF', 0.0)
        Test, EvsePlugLockState = STLA_CAN.DBC.GetSignal(1, 'DAT_OBC_DCDC_421', 'EVSE_PLUG_LOCK_STATE', 0.0)
        TestResult1 = OBCChargeConnConf == 2
        TestResult2 = EvsePlugLockState == 1
        list.append(TestResult1 and TestResult2)
        SetCCResistance += 10
    print(list)
    TestResult = all(list)

    CloseAllCANMessage()
    CloseAllDevice()
    STLA_CAN.DBC.RecordState(AcqEnum.Stop)

    if TestResult == True:
        TestResultDisplay = '合格'
        print(TestResultDisplay)
    else:
        TestResultDisplay = '不合格'
        print(TestResultDisplay)