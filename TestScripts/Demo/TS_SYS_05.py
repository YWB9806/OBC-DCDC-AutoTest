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
    STLA_CAN.DBC.ConfigureSetting ('EVTECH_STLA-M_TS-VF-2', 'TS-SYS-05', RecordFileType.BLF, "data")
    STLA_CAN.DBC.SetChannel ('All', ['ALL'], RecordEnum.ON)
    STLA_CAN.DBC.RecordState (AcqEnum.Start)
    InitAllCANMessage()
    低压辅源.SCPI.Write (':SOUR1:VOLT 12.5;:SOUR1:CURR 3;:OUTP CH1,ON')
    低压辅源.SCPI.Write (':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
    
    list = []
    SetCCResistance = 641
    for i in range (1000):
        电阻控制板.Modbus.SetRegister (iID=1,Reg=3072,Data=str (SetCCResistance))
        Sleep (1000)
        Test, OBCFaultState = STLA_CAN.DBC.GetSignal (1,'DAT_OBC_DCDC_421','OBC_FAULT_STATE', 0.0)
        Test, DCDCFaultState = STLA_CAN.DBC.GetSignal (1,'DAT_OBC_DCDC_501','DCDC_FAULT_STATE', 0.0)
        Test, OBCChargeConnConf = STLA_CAN.DBC.GetSignal (1,'DAT_OBC_DCDC_421','OBC_CHRG_CONN_CONF', 0.0)
        Test, CCRes = STLA_CAN.DBC.GetSignal (1,'IFB_CC_CP','IFB_CCCP_CC_Res', 0.0)
        SingleResult = OBCChargeConnConf == 3
        print (f'IFB_CCCP_CC_Res:{CCRes},OBC_CHRG_CONN_CONF:{OBCChargeConnConf}')

    
        if SingleResult == True:
            list.append (True)
        else:
            list.append (False)
            
        SetCCResistance += 10

        if SetCCResistance >= 1999:
            EndTime = TimeStamp ()
            TestResult = min (list)
            print (list)
            break
    
    Sleep (1000)
    CloseAllCANMessage ()
    CloseAllDevice ()
    STLA_CAN.DBC.RecordState (AcqEnum.Stop)
    TestResult = True if TestResult else False
    if TestResult == True:
        TestResultDisplay = '合格'
        print(TestResultDisplay)
    else:
        TestResultDisplay = '不合格'
        print(TestResultDisplay)