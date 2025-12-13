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
    STLA_CAN.DBC.ConfigureSetting('EVTECH_STLA-M_TS-VF-2', 'TS_DCC_07', RecordFileType.BLF, None)
    STLA_CAN.DBC.SetChannel('All', ['ALL'], RecordEnum.ON)
    STLA_CAN.DBC.RecordState(AcqEnum.Start)
    InitAllCANMessage()
    STLA_CAN.DBC.SetSignal(1, 'DYN_E_VCU_342', 'REVEIL_PRINCIPAL', 2)

    低压辅源.SCPI.Write(':SOUR1:VOLT 12.5;:SOUR1:CURR 3;:OUTP CH1,ON')
    低压辅源.SCPI.Write(':SOUR2:VOLT 5;:SOUR2:CURR 3;:OUTP CH2,ON')
    Sleep(2500)

    高压源载一体机.Set.Volt(dVolt=375)
    高压源载一体机.Out.Enable(eEnable.ON)
    Sleep(1000)

    STLA_CAN.DBC.SetMessage(1,'DYN_E_VCU_342',[0,0,0,15,0,0,0,0,0])
    STLA_CAN.DBC.Trigger(1, 'DYN_E_VCU_342', True)
    Sleep(1000)
    Test , DCDCStateBB1 = STLA_CAN.DBC.GetSignal(1, 'DAT_OBC_DCDC_541', 'DCDC_STATE_BB', 0.0)
    PreCondition = True if DCDCStateBB1 == 2 else False

    STLA_CAN.DBC.SetSignal(1, 'DAT_E_VCU_448', 'REG_MODE_DCDC_BB_REQ', 2)
    Sleep(200)
    Test , DCDCStateBB2 = STLA_CAN.DBC.GetSignal(1, 'DAT_OBC_DCDC_541', 'DCDC_STATE_BB', 0.0)
    TestResult1 = DCDCStateBB2 == 3
    
    低压源载一体机.Set.Curr(DCPwrModeEnum.Load, 10)
    低压源载一体机.Out.Enable(eEnable.ON)
    Sleep(1000)

    index = 0
    list = []
    DCDCOutputCurrentList = [50,100,150,200,250]
    CurrentSetListLength = len(DCDCOutputCurrentList)
    for index in range(CurrentSetListLength):
        SetDCDCOutputCurrent = DCDCOutputCurrentList[index]

        低压源载一体机.Set.Curr(DCPwrModeEnum.Load, SetDCDCOutputCurrent)
        Sleep(500)
        Test , ReadDCDCOutputCurrent = STLA_CAN.DBC.GetSignal(1, 'DAT_OBC_DCDC_501', 'DCDC_REAL_LV_CURR_HD', 0.0)
        SingleResult = (ReadDCDCOutputCurrent<=SetDCDCOutputCurrent*1.15) and (ReadDCDCOutputCurrent>=SetDCDCOutputCurrent*0.85)
        if SingleResult == True:
            SingleResultList = list.append(True)
        else:
            SingleResultList = list.append(False)
        
        index += 1
    TestResult2 = min(SingleResultList)

    Sleep(2000)
    CloseAllCANMessage()
    CloseAllDevice()
    STLA_CAN.DBC.RecordState(AcqEnum.Stop)

    TestResult = True if PreCondition and TestResult1 and TestResult2 else False
    if TestResult == True:
        TestResultDisplay = '合格'
    else:
        TestResultDisplay = '不合格'

