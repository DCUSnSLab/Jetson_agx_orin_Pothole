import os
import sys
import time
import signal

# 경로, x, y 를 파라미터로 넣으면 해당 경로에 좌표값을 담은 txt 파일과 xls 파일을 생성해주는 임시 프로그램입니다.
# len(sys.argv) : 파라미터 개수(파라미터없이 실행만 시킬 경우, 개수는 1.)
def exit_handler(signum, frame):
    filename = str(sys.argv[1]) + str(time.strftime("%Y년-%m월-%d일_%H시-%M분")) + ".txt"

    # file = open(filename, "w")
    # file.write("X_coord = " + str(sys.argv[2]) + "\n")
    # file.write("Y_coord = " + str(sys.argv[3]) + "\n")
    # file.close()
    # print("Text File Saved !")

    # excel_file = open(str(sys.argv[1]) + str(time.strftime("%Y년-%m월-%d일_%H시-%M분")) + ".xls", "w")
    # excel_file.close()
    # print("Excel File Saved !")
    for i in range(3):
        excel_file = open(str(sys.argv[1]) + "/" + str(time.strftime("%M분-%s초_")) + str(i + 1) + ".xls", "w")
        excel_file.close()
        print("Excel File {0} Saved !".format(i + 1))
    sys.exit()


signal.signal(signal.SIGTERM, exit_handler)
while True:
    print("Still Running . . .")
    time.sleep(1)
