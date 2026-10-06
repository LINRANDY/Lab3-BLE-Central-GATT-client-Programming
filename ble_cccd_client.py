import sys
import struct
from bluepy.btle import Scanner, DefaultDelegate, Peripheral, UUID

# 1. 定義掃描事件回呼類別 (來自講義範例)
class ScanDelegate(DefaultDelegate):
    def __init__(self):
        super().__init__()

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewDev:
            print("發現新裝置:", dev.addr)
        elif isNewData:
            print("收到裝置新資料:", dev.addr)

def main():
    print("=== [步驟 1] 開始掃描周圍 BLE 裝置 (持續 10 秒) ===")
    scanner = Scanner().withDelegate(ScanDelegate())
    devices = scanner.scan(10.0)

    n = 0
    addr_list = []
    addr_types = []

    print("\n---------------- 掃描結果列表 ----------------")
    for dev in devices:
        print(f"[{n}] 裝置 MAC: {dev.addr} ({dev.addrType}), RSSI: {dev.rssi} dB")
        # 印出廣播內容（如 Local Name、Service UUID 等）以利辨認手機
        for (adtype, desc, value) in dev.getScanData():
            print(f"    {desc}: {value}")
        addr_list.append(dev.addr)
        addr_types.append(dev.addrType)
        n += 1

    if len(addr_list) == 0:
        print("\n未掃描到任何 BLE 裝置！請確認手機端是否已按下 Start Advertising。")
        return

    # 由使用者輸入裝置編號
    choice = input("\n請輸入你的手機裝置編號 (例如 0, 1, 2...): ")
    target_idx = int(choice)
    target_addr = addr_list[target_idx]
    target_type = addr_types[target_idx]

    print(f"\n=== [步驟 2] 正在連線至 {target_addr} ({target_type})... ===")
    # 講義說明：手機等週邊裝置通常使用 random 位址，此處依掃描結果自動帶入
    dev = Peripheral(target_addr, target_type)

    try:
        print("\n=== [步驟 3] 探索目標服務與特徵值 ===")
        # 講義規定的 Custom Service: 0xfff0
        test_service = dev.getServiceByUUID(UUID(0xfff0))
        print("成功取得服務:", str(test_service))

        # 講義規定的 Custom Characteristic: 0xfff1
        ch = test_service.getCharacteristics(UUID(0xfff1))[0]
        print("成功取得特徵值:", str(ch))

        # 讀取特徵值原本的內容並印出 (講義中的 ch.read() 測試)
        if ch.supportsRead():
            val = ch.read()
            print("特徵值目前內容 (原始 Bytes):", val)

        print("\n=== [步驟 4] 尋找 CCCD (0x2902) 並寫入 0x0002 ===")
        cccd_uuid = UUID(0x2902)
        cccd_desc = None

        # 遍歷該特徵值的所有描述符 (Descriptors)
        for desc in ch.getDescriptors():
            print(f"發現描述符: UUID={desc.uuid}, Handle={hex(desc.handle)}")
            if desc.uuid == cccd_uuid:
                cccd_desc = desc
                break

        if cccd_desc is not None:
            # 依作業要求：將 CCCD 設定為 0x0002 (Indication)
            # 使用小端序 (Little-Endian) 打包為 2 位元組: b'\x02\x00'
            payload = struct.pack('<H', 0x0002)
            print(f"正在向 CCCD (Handle: {hex(cccd_desc.handle)}) 寫入數值 0x0002...")
            cccd_desc.write(payload, withResponse=True)
            print("\n【寫入成功】已向手機端 CCCD 送出 0x0002！")
        else:
            print("\n【找不到 CCCD】未在此特徵值底下找到 UUID 0x2902，請確認手機端特徵值是否有開啟 Indicate 或 Notify。")

    finally:
        dev.disconnect()
        print("連線已正常釋放關閉。")

if __name__ == '__main__':
    main()