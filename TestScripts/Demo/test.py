import sys
sys.path.append(r"D:\AI自动化\DriverTest")  # 添加DLL所在目录

import clr
clr.AddReference("ActionPower.DRV.ACPwr")
clr.AddReference("ActionPower.DRV.DCPwr")
clr.AddReference("ActionPower.DRV.Scope")
clr.AddReference("ActionPower.DRV.DMM")
clr.AddReference("ActionPower.DRV.UserDef")
from time import sleep as Sleep
from ActionPower.DRV.ACPwr import *
from ActionPower.DRV.DCPwr import *
from ActionPower.DRV.Scope import *
from ActionPower.DRV.DMM import *
from ActionPower.DRV.UserDef import UserDef,FileTypeEnum,RecordEnum,AcqEnum

def CAN初始化():
    source = "CAN::1::TS::TC1011::1::500"
    CAN = UserDef.CreateInstance(source)
    
    return CAN
STLA_CAN = CAN初始化()

if __name__ == '__main__':
    print('Initialize:')
    print(STLA_CAN.Initialize(False, False, "DevType=STLA_DBC1.0.A_AutoSar"))
    print(STLA_CAN.Utility.DefaultSetup())
    print(STLA_CAN.Initialize(False, False, "DevType=STLA_DBC1.0.A_AutoSar"))
    print(STLA_CAN.DBC.ConfigureSetting("EVTECH_STLA-M_V1.3_TS-VF-1", "TS-NAV2L-05-1", FileTypeEnum.BLF, "data"))
    print(STLA_CAN.DBC.SetChannel("All", ["ALL"], RecordEnum.ON))
    print(STLA_CAN.DBC.RecordState(AcqEnum.Start))
    print(STLA_CAN.DBC.SetMessage(1, "DAT_E_VCU_448", ["0", "0", "0", "1", "0" ]))
    print(STLA_CAN.DBC.Trigger(1, "DAT_E_VCU_448", True))
    Sleep(5)
    ret1,data1 = STLA_CAN.DBC.GetSignal(1, "DAT_OBC_DCDC_541", "DCDC_STATE_BB", 0.0)
    print('GetSignal:')
    print(data1)
    Sleep(5)
    print(STLA_CAN.DBC.Trigger(1, "DAT_E_VCU_448", False))
    print(STLA_CAN.DBC.RecordState(AcqEnum.Stop))