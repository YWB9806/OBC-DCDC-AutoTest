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
    STLA_CAN.DBC.ConfigureSetting('EVTECH_STLA-M_TS-VF-2', 'TS-LED-LOCK-04', RecordFileType.BLF, None)
    STLA_CAN.DBC.SetChannel('All', ['ALL'], RecordEnum.ON)
    STLA_CAN.DBC.RecordState(AcqEnum.Start)
    InitAllCANMessage()

    低压辅源.SCPI.Write(':SOUR1:VOLT 16.5:SOUR1:CURR 3;:OUTP CH1,ON')
    低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
    低压辅源.SCPI.Write(':SOUR3:VOLT 0.6;:SOUR3:CURR 3;:OUTP CH3,ON')
    信号发生器.SCPI.Write(':SOUR1:APPL:SQU 1000,18.1,0,0;:SOUR1:FUNC:SQU:DCYC 80;:OUTP1 ON')
    Sleep(1000)

    list = []
    SetCCResistance = 101
    StartTime = TimeStamp()     # 获取毫秒级时间戳
    for i in range(100):
        电阻控制板.Modbus.SetRegister(iID=1,Reg=3072,Data=str(SetCCResistance))
        Sleep(1000)

        Test, OBCFaultState = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_421','OBC_FAULT_STATE', 0.0)
        Test, DCDCFaultState = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_501','DCDC_FAULT_STATE', 0.0)
        Test, OBCChargeConnConf = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_421','OBC_CHRG_CONN_CONF', 0.0)
        Test, CCRes = STLA_CAN.DBC.GetSignal(1,'IFB_CC_CP','IFB_CCCP_CC_Res', 0.0)
        SingleResult1 = OBCChargeConnConf == 2

        STLA_CAN.DBC.SetSignal(1,'DAT_E_VCU_448','CABLE_LOCK_REQ',1)
        Sleep(1500)

        Test , EvsePlugLockState1 = STLA_CAN.DBC.GetSignal(1,'DAT_OBC_DCDC_421','EVSE_PLUG_LOCK_STATE', 0.0)
        SingleResult2 = EvsePlugLockState1 == 1

        print(f'IFB_CCCP_CC_Res:{CCRes},OBC_CHRG_CONN_CONF:{OBCChargeConnConf}')
        if SingleResult1 == True and SingleResult2 == True:
            list.append(True)
        else:
            list.append(False)

        SetCCResistance += 10

        if SetCCResistance >= 270:
            EndTime = TimeStamp()       # 获取毫秒级时间戳
            TestResult = min(list)
            print(list)
            break
    
    CloseAllCANMessage()
    STLA_CAN.DBC.RecordState(AcqEnum.Stop)

    Sleep(2000)
    CloseAllDevice()

    if TestResult == True:
        TestResultDisplay = '合格'
        print(TestResultDisplay)
    else:
        TestResultDisplay = '不合格'
        print(TestResultDisplay)