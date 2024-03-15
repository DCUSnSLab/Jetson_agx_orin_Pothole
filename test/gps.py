from ublox_gps import UbloxGps
import serial

# Can also use SPI here - import spidev
# I2C is not supported

port = serial.Serial('/dev/ttyACM0', baudrate=115200, timeout=1)
gps = UbloxGps(port)

'''
def run():
    try:
        print("Listenting for UBX Messages.")
        while True:
            try:
                coords = gps.geo_coords()
                print(coords.lon, coords.lat)
            except (ValueError, IOError) as err:
                print(err)

    finally:
        port.close()


if __name__ == '__main__':
    run()
'''
import signal

# 이전 코드 생략

def run():
    try:
        print("UBX 메시지를 수신 대기 중입니다.")
        while True:
            try:
                coords = gps.geo_coords()
                print(coords.lon, coords.lat)
                
            except (ValueError, IOError) as err:
                print(err)

    except KeyboardInterrupt:
        print("인터럽트가 발생하여 프로그램을 종료합니다.")
        port.close()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.default_int_handler)
    run()
